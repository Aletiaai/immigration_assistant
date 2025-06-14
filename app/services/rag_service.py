from typing import Any, List, Dict, Optional
from app.services.llm_client import OllamaClient
from app.services.embeddings import EmbeddingService
from app.services.vectorstore import VectorStoreService
from app.services.data_loader import DocumentProcessor
from app.core.config import CONTEXT_HISTORY_MESSAGES, GOOGLE_PROJECT_ID, GOOGLE_LOCATION, GOOGLE_PROCESSOR_ID, MAX_CHUNKS_RETRIEVED
from app.core.prompts import get_system_prompt, get_prompt_template, LANGUAGE_DETECTION_PROMPT, get_document_processing_prompt

import re
import logging

import numpy as np

logger = logging.getLogger(__name__) 

class RAGService:
    def __init__(self):
        try:
            logger.info("Initializing RAGService components...")
            self.llm_client = OllamaClient()
            logger.info("OllamaClient initialized.")
            self.embedding_service = EmbeddingService()
            logger.info("EmbeddingService initialized.")
            self.vector_store = VectorStoreService()
            logger.info("VectorStoreService initialized.")
            # Check Google Document AI credentials early
            if not all([GOOGLE_PROJECT_ID, GOOGLE_LOCATION, GOOGLE_PROCESSOR_ID]):
                logger.error("Google Document AI credentials (PROJECT_ID, LOCATION, or PROCESSOR_ID) are missing in .env or config.")
                raise Exception("Google Document AI credentials not configured properly.")
            self.doc_processor = DocumentProcessor()
            logger.info("DocumentProcessor initialized.")
            logger.info("RAGService initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {str(e)}", exc_info=True) # exc_info=True logs traceback
            raise Exception(f"Failed to initialize RAG service: {str(e)}")
    
    def process_document(self, file_path: str) -> bool:
        logger.info(f"--- RAGService: Starting process_document for: {file_path} ---")
        try:
            # Step 1: Process PDF with Document AI
            logger.info(f"--- RAGService: Step 1 - Processing PDF with Document AI: {file_path} ---")
            chunks = self.doc_processor.process_pdf(file_path) # This calls Google
            logger.info(f"--- RAGService: Document AI processing returned {len(chunks)} chunks. ---")

            if not chunks:
                logger.warning(f"--- RAGService: No chunks extracted from PDF for {file_path}. Document might be empty or unprocessable by Document AI. ---")
                return False # Explicitly return False if no chunks

            # Step 2: Generate embeddings
            logger.info(f"--- RAGService: Step 2 - Generating embeddings for {len(chunks)} extracted chunks. ---")
            texts = []
            for chunk in chunks:
                # Combine content with questions for better semantic embedding
                content_with_questions = chunk["content"]
                if chunk.get("questions"):
                    questions_text = " ".join(chunk["questions"])
                    content_with_questions += f"\n\nRelated questions: {questions_text}"
                texts.append(content_with_questions)

            if not texts:
                logger.warning(f"--- RAGService: No text content found in chunks to generate embeddings for {file_path}. ---")
                return False

            embeddings = self.embedding_service.generate_embeddings(texts)
            logger.info(f"--- RAGService: Generated {len(embeddings)} embeddings. ---")
            if not embeddings or len(embeddings) != len(chunks):
                logger.error(f"--- RAGService: Mismatch in number of embeddings ({len(embeddings)}) and chunks ({len(chunks)}) or no embeddings generated for {file_path}. ---")
                return False

            # Step 3: Store in vector database
            logger.info(f"--- RAGService: Step 3 - Adding {len(chunks)} documents (with embeddings) to vector store. ---")
            # Get filename from path for the source metadata
            source_filename = file_path.split('/')[-1] if '/' in file_path else file_path.split('\\')[-1] if '\\' in file_path else file_path

            for chunk in chunks:
                if 'source' not in chunk or not chunk['source']: # Adding filename as source if not present or empty
                    chunk['source'] = source_filename
                # Ensuring page is present, default to 1 if missing
                if 'page' not in chunk:
                    chunk['page'] = chunk.get("page", 1) # Default to 1 if 'page' key is missing
                if 'type' not in chunk:
                    chunk['type'] = chunk.get("type", "block") # Default to 'block'
                
                # Store the original content (without questions) separately for display
                chunk['original_content'] = chunk['content']


            add_success = self.vector_store.add_documents(chunks, embeddings)
            if add_success:
                logger.info(f"--- RAGService: Successfully added documents to vector store for {file_path}. ---")
            else:
                logger.error(f"--- RAGService: Failed to add documents to vector store for {file_path} (VectorStoreService.add_documents returned False). ---")
            
            logger.info(f"--- RAGService: Finished process_document for: {file_path}. Overall Success: {add_success} ---")
            return add_success

        except Exception as e:
            # Log the exception from RAGService.process_document itself
            logger.error(f"--- RAGService: Error during process_document for {file_path}: {str(e)} ---", exc_info=True)
            logger.info(f"--- RAGService: Finished process_document for: {file_path} with error. Returning False. ---")
            return False # Ensure it returns False on any exception within this block
    
    def query(self, question: str, chat_history: List[Dict] = None) -> Dict:
        try:
            logger.info(f"--- RAGService: Received query: '{question}' ---")
            # Detect language
            language = self._detect_language(question)
            logger.info(f"--- RAGService: Detected language: {language} ---")
            
            # Generate query embedding
            logger.info(f"--- RAGService: Generating embedding for query... ---")
            query_embedding = self.embedding_service.generate_single_embedding(question)
            logger.info(f"--- RAGService: Query embedding generated. ---")
            
            # Search relevant documents
            logger.info(f"--- RAGService: Searching vector store... ---")
            search_results = self.vector_store.search(query_embedding, n_results= MAX_CHUNKS_RETRIEVED)
            logger.info(f"--- RAGService: Found {len(search_results)} search results. ---")

            # Create prompt with citations
            logger.info(f"--- RAGService: Building prompt with citations... ---")
            context = self._build_context(search_results)  # Fallback
            prompt = self._build_prompt(question, context, search_results, chat_history, language)

            # Generate response
            logger.info(f"--- RAGService: Generating response from LLM... ---")
            response_text = self.llm_client.generate_response(prompt)
            logger.info(f"--- RAGService: LLM response received. ---")
            
            return {
                "response": response_text,
                "sources": [r["metadata"] for r in search_results if "metadata" in r],
                "language": language
            }
        except Exception as e:
            logger.error(f"--- RAGService: Error during query processing: {str(e)} ---", exc_info=True)
            raise Exception(f"Query processing failed: {str(e)}")
    
    def _detect_language(self, text: str) -> str:
        try:
            # Use simple heuristic for very short texts
            if len(text.strip()) < 10:
                spanish_words = ['el', 'la', 'es', 'de', 'que', 'y', 'en', 'un', 'una', 'con', 'por', 'para']
                words = re.findall(r'\b\w+\b', text.lower())
                spanish_count = sum(1 for word in words if word in spanish_words)
                return "spanish" if spanish_count > len(words) * 0.2 else "english"
            
            # Use LLM for longer texts
            prompt = LANGUAGE_DETECTION_PROMPT.format(text=text)
            
            response = self.llm_client.generate_response(prompt).strip().lower()
            logger.info(f"The system detected {response} as the language from the query\n{50 * '-----'}")
            return "spanish" if "spanish" in response else "english"
            
        except Exception as e:
            logger.warning(f"Language detection failed: {str(e)}, defaulting to english")
            return "english"
    
    def _build_context(self, search_results: List[Dict]) -> str:
        try:
            context_parts = []
            for result in search_results:
                # Use original content without questions for context display
                content = result.get('original_content', result['content'])
                context_parts.append(f"Content: {content}")
            return "\n\n".join(context_parts)
        except Exception as e:
            return ""

    def _build_prompt(self, question: str, context: str, search_results: List[Dict], chat_history: List[Dict], language: str) -> str:
        try:
            # Build numbered context with source references
            numbered_context = []
            for i, result in enumerate(search_results, 1):
                source = result.get('metadata', {}).get('source', 'Unknown')
                page = result.get('metadata', {}).get('page', '')
                page_ref = f", page {page}" if page else ""
                
                # Use original content for display (without questions)
                content = result.get('original_content', result['content'])
                numbered_context.append(f"[{i}] {content}\nSource: {source}{page_ref}")
            
            context_with_sources = "\n\n".join(numbered_context)
            
            # Format chat history
            history_text = ""
            if chat_history:
                history_formatted = self._format_chat_history(chat_history)
                history_text = f"Chat History:\n{history_formatted}\n\n"
            
            # Get prompts from centralized file
            system_message = get_system_prompt(language)
            template = get_prompt_template(language)
            
            # Build final prompt
            final_prompt = template.format(
                system_message=system_message,
                context=context_with_sources,
                chat_history=history_text,
                question=question
            )
            
            return final_prompt
            
        except Exception as e:
            logger.error(f"Error building prompt: {str(e)}")
            return f"Context: {context}\nQuestion: {question}\nAnswer:"
            
    def _format_chat_history(self, chat_history: List[Dict]) -> str:
        try:
            history_parts = []
            for msg in chat_history[-CONTEXT_HISTORY_MESSAGES:]:  # Last 5 messages to stay within token limit
                history_parts.append(f"User: {msg.get('question', '')}")
                history_parts.append(f"Assistant: {msg.get('response', '')}")
            return "\n".join(history_parts)
        except Exception as e:
            return ""
        
    def process_document_temporarily(self, file_path: str, original_filename: str, user_message: str, instructions: str = "") -> Dict[str, Any]:
        """Process document temporarily for one-time use without adding to knowledge base"""
        try:
            logger.info(f"--- RAGService: Processing document temporarily: {file_path} ---")

            # Process document based on file type
            if original_filename.lower().endswith('.pdf'):
                full_text = self.doc_processor.extract_text_from_pdf(file_path)
                logger.debug(f"Este es el contenido del archivo PDF: {full_text}")
            elif original_filename.lower().endswith('.docx'):
                full_text = self.doc_processor.extract_text_from_docx(file_path)
            else:
                raise ValueError("Unsupported file type")

            if not full_text:
                raise Exception("No content extracted from document")
            
            # Create special prompt for document processing
            context = full_text

            # Detect language and get appropriate prompt
            language = self._detect_language(user_message)

            prompt = get_document_processing_prompt(language)
    
            prompt_tamplate = prompt.format(
                context = context,
                user_message = user_message,
                instructions = instructions if instructions else "None provided"
            )

            # Generate response
            response = self.llm_client.generate_response(prompt_tamplate)
            
            return {
            "response": response,
            "sources": [{"content": full_text[:200] + "...", "page": "N/A"}],
            "language": language
        }
            
        except Exception as e:
            logger.error(f"--- RAGService: Error in temporary document processing: {str(e)} ---")
            raise Exception(f"Temporary document processing failed: {str(e)}")