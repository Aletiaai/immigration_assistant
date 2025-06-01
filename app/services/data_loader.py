from google.cloud import documentai_v1 as documentai
from typing import List, Dict
from app.core.config import GOOGLE_PROJECT_ID, GOOGLE_LOCATION, GOOGLE_PROCESSOR_ID, MIN_SECTION_TEXT_LENGTH, DEFAULT_HEADER_TEXT, CHUNK_SIZE, CHUNK_OVERLAP
from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging
import re

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        logger.info("--- DocumentProcessor: Initializing... ---")
        if not all([GOOGLE_PROJECT_ID, GOOGLE_LOCATION, GOOGLE_PROCESSOR_ID]):
            logger.error("--- DocumentProcessor: Google Document AI credentials (PROJECT_ID, LOCATION, or PROCESSOR_ID) are missing. ---")
            raise Exception("Google Document AI credentials not configured")

        self.project_id = GOOGLE_PROJECT_ID
        self.location = GOOGLE_LOCATION
        self.processor_id = GOOGLE_PROCESSOR_ID
        
        try:
            self.client = documentai.DocumentProcessorServiceClient()
            logger.info("--- DocumentProcessor: DocumentProcessorServiceClient initialized successfully. ---")
        except Exception as e:
            logger.error(f"--- DocumentProcessor: Failed to initialize DocumentProcessorServiceClient: {str(e)} ---", exc_info=True)
            raise Exception(f"Failed to initialize DocumentProcessorServiceClient: {str(e)}")
        logger.info("--- DocumentProcessor: Initialized successfully. ---")

    def process_pdf(self, file_path: str) -> List[Dict[str, str]]:
        logger.info(f"--- DocumentProcessor: Starting process_pdf for: {file_path} ---")
        try:
            name = f"projects/{self.project_id}/locations/{self.location}/processors/{self.processor_id}"
            logger.info(f"--- DocumentProcessor: Document AI Processor name: {name} ---")

            with open(file_path, "rb") as file:
                file_content = file.read()
            logger.info(f"--- DocumentProcessor: Read {len(file_content)} bytes from file: {file_path} ---")

            # Construct the RawDocument object
            raw_document = documentai.RawDocument(
                content=file_content,       # Do I have to pass the content of the file like this? or the file itself?
                mime_type="application/pdf"
            )
            
            # Construct the request
            request = documentai.ProcessRequest(
                name=name,
                raw_document=raw_document
            )
            logger.info("--- DocumentProcessor: Prepared Document AI request. ---")

            # This is the actual call to Google Document AI
            result = self.client.process_document(request=request)
            logger.info("--- DocumentProcessor: Successfully called Google Document AI process_document. ---")
            document = result.document
            logger.info(f"--- These are the results from Document AI:\n\n{document.text}")

            if not result.document or not (hasattr(result.document, 'text') and result.document.text):
                 logger.warning(f"--- DocumentProcessor: Document AI result for {file_path} contains no document object or no extracted text. ---")
                 return [] # Return empty list if no text to process

            chunks = self._extract_chunks(result.document)
            logger.info(f"--- DocumentProcessor: Extracted {len(chunks)} chunks from Document AI response for {file_path}. ---")
            logger.info(f"--- DocumentProcessor: Finished process_pdf for: {file_path} ---")
            return chunks

        except Exception as e:
            logger.error(f"--- DocumentProcessor: Error in process_pdf for {file_path}: {str(e)} ---", exc_info=True)
            # Re-raise the exception so RAGService.process_document's try-except can catch it
            # and return False, or handle it as appropriate.
            raise Exception(f"Document processing failed within DocumentProcessor: {str(e)}")


    def _extract_chunks(self, document_proto: documentai.Document) -> List[Dict[str, str]]: 
        logger.debug(f"--- DocumentProcessor: Starting _extract_chunks. Document has text length: {len(document_proto.text) if document_proto and document_proto.text else 0} ---")
        chunks = []
        try:
            if not document_proto or not document_proto.pages: # Check document_proto itself
                logger.warning("--- DocumentProcessor: _extract_chunks - Document proto is None or has no pages. ---")
                return chunks

            for i, page in enumerate(document_proto.pages):
                page_number = page.page_number if page.page_number else i + 1 # Use actual page_number if available
                logger.debug(f"--- DocumentProcessor: Processing page number: {page_number} ---")
                if not page.blocks:
                    logger.debug(f"--- DocumentProcessor: Page {page_number} has no blocks. ---")
                    continue

                for j, block in enumerate(page.blocks):
                    logger.debug(f"--- DocumentProcessor: Processing block {j+1} on page {page_number} ---")
                    try:
                        text = self._get_text_from_layout(block.layout, document_proto.text) # Pass block.layout
                        if text and text.strip():
                            chunks.append({
                                "content": text.strip(),
                                "page": page_number,
                                "type": "block" # Or determine type more dynamically if needed
                                # 'source' will be added by RAGService
                            })
                            logger.debug(f"--- DocumentProcessor: Added chunk from block {j+1}, page {page_number}. Length: {len(text.strip())} ---")
                        else:
                            logger.debug(f"--- DocumentProcessor: Block {j+1} on page {page_number} yielded no text or only whitespace. ---")
                    except Exception as e_block:
                        logger.error(f"--- DocumentProcessor: Error processing block {j+1} on page {page_number}: {str(e_block)} ---", exc_info=True)
                        continue # Continue to next block

        except Exception as e_page: # Catch errors iterating pages or general errors
            logger.error(f"--- DocumentProcessor: Error during page/block iteration in _extract_chunks: {str(e_page)} ---", exc_info=True)
            # Depending on desired robustness, you might return partially collected chunks or an empty list.
            # For now, let it fall through to the final return or an outer exception.

        logger.info(f"--- DocumentProcessor: Finished _extract_chunks, found {len(chunks)} chunks. ---")
        return chunks


    def _get_text_from_layout(self, layout_proto: documentai.Document.Page.Layout, full_text: str) -> str:
        logger.debug(f"--- DocumentProcessor: Entering _get_text_from_layout ---")
        try:
            if not layout_proto or not layout_proto.text_anchor or not layout_proto.text_anchor.text_segments:
                logger.debug("--- DocumentProcessor: _get_text_from_layout - Layout, text_anchor, or segments missing. ---")
                return ""

            text_content_parts = []
            for segment in layout_proto.text_anchor.text_segments:
                start_index = segment.start_index
                end_index = segment.end_index
                start_index = int(start_index) if start_index is not None else 0
                end_index = int(end_index) if end_index is not None else 0 # If end_index is None, make segment empty

                if not (0 <= start_index <= len(full_text) and 0 <= end_index <= len(full_text) and start_index <= end_index):
                    logger.warning(f"--- DocumentProcessor: Invalid text segment indices: start='{segment.start_index}', end='{segment.end_index}'. Full text length: {len(full_text)}. Skipping segment. ---")
                    continue
                
                text_content_parts.append(full_text[start_index:end_index])
            
            return "".join(text_content_parts)

        except Exception as e:
            logger.error(f"--- DocumentProcessor: Error in _get_text_from_layout: {str(e)} ---", exc_info=True)
            # Re-raise to be caught by _extract_chunks
            raise Exception(f"Text extraction from layout failed: {str(e)}")