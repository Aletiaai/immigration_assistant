# Path: app/services/data_loader.py

from google.cloud import documentai_v1 as documentai
from google.cloud.documentai_v1.types import Document
from typing import List, Dict
from app.core.config import (
    GOOGLE_PROJECT_ID, GOOGLE_LOCATION, GOOGLE_PROCESSOR_ID,
    MIN_SECTION_TEXT_LENGTH, DEFAULT_HEADER_TEXT, CHUNK_SIZE, CHUNK_OVERLAP,
    DOCUMENT_AI_HEADER_TYPES, DOCUMENT_AI_FOOTER_TYPES, DOCUMENT_AI_TABLE_TYPES
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.services.llm_client import OllamaClient
from app.core.prompts import get_question_generation_prompt
import logging
import re
import os

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Handles complex document processing using Google Document AI Layout Parser,
    followed by intelligent chunking and question-based enrichment.
    """
    def __init__(self):
        logger.info("--- DocumentProcessor: Initializing... ---")
        if not all([GOOGLE_PROJECT_ID, GOOGLE_LOCATION, GOOGLE_PROCESSOR_ID]):
            raise Exception("Google Document AI credentials not configured properly.")

        self.project_id = GOOGLE_PROJECT_ID
        self.location = GOOGLE_LOCATION
        self.processor_id = GOOGLE_PROCESSOR_ID
        
        self.client = documentai.DocumentProcessorServiceClient()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len
        )
        
        try:
            self.llm_client = OllamaClient()
            logger.info("--- DocumentProcessor: LLM client for question generation initialized. ---")
        except Exception as e:
            logger.warning(f"--- DocumentProcessor: Could not initialize LLM client: {e}. Question enrichment will be skipped. ---")
            self.llm_client = None

        logger.info("--- DocumentProcessor: Initialized successfully. ---")

    def process_pdf(self, file_path: str) -> List[Dict[str, any]]:
        """Processes a PDF using Document AI and extracts structured, enriched chunks."""
        logger.info(f"--- DocumentProcessor: Starting PDF processing for: {file_path} ---")
        document_name = os.path.basename(file_path)
        try:
            name = self.client.processor_path(self.project_id, self.location, self.processor_id)
            with open(file_path, "rb") as file:
                file_content = file.read()

            raw_document = documentai.RawDocument(content=file_content, mime_type="application/pdf")
            request = documentai.ProcessRequest(name=name, raw_document=raw_document)
            
            result = self.client.process_document(request=request)
            document_proto: Document = result.document

            if not (hasattr(document_proto, 'document_layout') and document_proto.document_layout.blocks):
                logger.warning(f"--- DocumentProcessor: No layout blocks found in Document AI response for {file_path}. ---")
                return []

            chunks = self._extract_chunks_from_layout_parser(document_proto, document_name)
            logger.info(f"--- DocumentProcessor: Extracted {len(chunks)} chunks for {file_path}. ---")
            return chunks

        except Exception as e:
            logger.error(f"--- DocumentProcessor: PDF processing failed for {file_path}: {e} ---", exc_info=True)
            raise

    def _extract_chunks_from_layout_parser(self, document_proto: Document, document_name: str) -> List[Dict[str, any]]:
        """Extracts and processes chunks based on the document's layout structure."""
        all_chunks = []
        doc_layout = document_proto.document_layout

        current_header_text = DEFAULT_HEADER_TEXT
        current_section_content_parts = []
        current_section_page_start = 1

        for block in doc_layout.blocks:
            page_start = block.page_span.page_start if block.page_span else 1
            block_type = block.text_block.type
            block_text = self._get_text_from_block(block)

            if not block_text:
                continue
            
            if block_type in DOCUMENT_AI_FOOTER_TYPES or block_type in DOCUMENT_AI_TABLE_TYPES:
                continue

            if block_type in DOCUMENT_AI_HEADER_TYPES:
                # Process the previous section before starting a new one
                if current_section_content_parts:
                    section_text = "\n".join(current_section_content_parts).strip()
                    if section_text:
                        processed_chunks = self._process_section_into_chunks(
                            current_header_text, section_text, current_section_page_start, document_name
                        )
                        all_chunks.extend(processed_chunks)
                
                # Start a new section
                current_header_text = block_text
                current_section_content_parts = [block_text]
                current_section_page_start = page_start
            else:
                # Append content to the current section
                if not current_section_content_parts:
                    current_section_page_start = page_start
                current_section_content_parts.append(block_text)
        
        # Process the last remaining section
        if current_section_content_parts:
            section_text = "\n".join(current_section_content_parts).strip()
            if section_text:
                processed_chunks = self._process_section_into_chunks(
                    current_header_text, section_text, current_section_page_start, document_name
                )
                all_chunks.extend(processed_chunks)

        return all_chunks

    def _process_section_into_chunks(self, header: str, content: str, page: int, doc_name: str) -> List[Dict[str, any]]:
        """Splits a large section into smaller chunks or keeps it whole, then enriches with questions."""
        final_chunks = []
        if len(content) < MIN_SECTION_TEXT_LENGTH:
            return [] # Discard very short, likely irrelevant sections
            
        if len(content) > CHUNK_SIZE:
            split_texts = self.text_splitter.split_text(content)
        else:
            split_texts = [content]

        for text_part in split_texts:
            questions = self._generate_questions_for_chunk(text_part)
            final_chunks.append({
                "content": text_part,
                "page": str(page),
                "header": header,
                "document_name": doc_name,
                "questions": questions
            })
        return final_chunks

    def _generate_questions_for_chunk(self, content: str) -> List[str]:
        """Generates questions for a chunk of text using the local LLM."""
        if not self.llm_client or len(content.strip()) < 50:
            return []
        try:
            # Simple language detection for choosing the right prompt
            is_spanish = any(word in content.lower() for word in [' de ', ' la ', ' el ', ' en ', ' que '])
            language = "spanish" if is_spanish else "english"
            
            prompt_template = get_question_generation_prompt(language)
            prompt = prompt_template.format(content=content)
            
            response = self.llm_client.generate_response(prompt)
            return self._parse_questions_from_response(response)
        except Exception as e:
            logger.error(f"--- DocumentProcessor: Error during question generation: {e} ---", exc_info=True)
            return []

    def _parse_questions_from_response(self, response: str) -> List[str]:
        """Parses a numbered list of questions from the LLM's raw output."""
        questions = []
        for line in response.split('\n'):
            match = re.match(r'^\d+\.\s*(.*)', line.strip())
            if match:
                question = match.group(1).strip()
                if question and ']' not in question:
                    questions.append(question)
        return questions[:10]

    def _get_text_from_block(self, block: 'documentai.Document.Layout.Block') -> str:
        """Recursively extracts all text from a block and its nested blocks."""
        text = ""
        if block.text_block and block.text_block.text:
            text = block.text_block.text.strip()
        
        # This part is crucial for layouts where content is nested inside other blocks
        if block.text_block and block.text_block.blocks:
            nested_texts = [self._get_text_from_block(nb) for nb in block.text_block.blocks]
            text = "\n".join([text] + nested_texts).strip()
            
        return text