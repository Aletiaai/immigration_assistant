<<<<<<< HEAD
<<<<<<< HEAD
# app/services/rag_service.py

from typing import Any, List, Dict
=======
from typing import List, Dict, Optional
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
=======
from typing import Any, List, Dict, Optional
>>>>>>> 9ea43c2 (Extracting text easily from document provided and answer only 1 question about the document)
from app.services.llm_client import OllamaClient
from app.services.embeddings import EmbeddingService
from app.services.vectorstore import VectorStoreService
from app.services.data_loader import DocumentProcessor
from app.core.config import CONTEXT_HISTORY_MESSAGES, GOOGLE_PROJECT_ID, GOOGLE_LOCATION, GOOGLE_PROCESSOR_ID, MAX_CHUNKS_RETRIEVED
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
from app.core.prompts import get_system_prompt, get_prompt_template, LANGUAGE_DETECTION_PROMPT, QUERY_INTENT_PROMPT, TOPIC_CHANGE_PROMPT, ROUTER_PROMPT, EXTRACTION_PROMPT_TEMPLATE
=======
from app.core.prompts import get_system_prompt, get_prompt_template
=======
from app.core.prompts import get_system_prompt, get_prompt_template, LANGUAGE_DETECTION_PROMPT
>>>>>>> c4d328f (Response with clickable citations with popup previewsworking)
=======
from app.core.prompts import get_system_prompt, get_prompt_template, LANGUAGE_DETECTION_PROMPT, get_document_processing_prompt
>>>>>>> 9ea43c2 (Extracting text easily from document provided and answer only 1 question about the document)

>>>>>>> 2af9797 (Enhanced semantic meaning with questions)
import re
import logging
import numpy as np
=======
import re
import logging
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)

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
<<<<<<< HEAD
=======
            logger.info("DocumentProcessor initialized.")
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
            logger.info("RAGService initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {str(e)}", exc_info=True) # exc_info=True logs traceback
            raise Exception(f"Failed to initialize RAG service: {str(e)}")
<<<<<<< HEAD
        
    def query_simple_document(self, question: str, full_text: str, chat_history: List[Dict]) -> Dict:
        """Answers a question about a simple document using a two-step LLM chain with centralized prompts."""
        
        logger.info("--- RAGService: Querying simple document with two-step LLM chain. ---")
        language = self._detect_language(question)
        
        try:
            # --- Step 1: Extract Relevant Information ---
            extraction_prompt = EXTRACTION_PROMPT_TEMPLATE.format(
                full_text=full_text,
                question=question
            )

            logger.info("--- RAGService: Calling LLM for relevance extraction. ---")
            relevant_context = self.llm_client.generate_response(extraction_prompt)

            if "no relevant information found" in relevant_context.lower():
                return {
                    "response": "I couldn't find any information in the document related to your question." 
                                if language == "english" else 
                                "No encontré información en el documento relacionada con tu pregunta.",
                    "sources": [],
                    "language": language
                }

            # --- Step 2: Synthesize the Final Answer ---
            history_text = self._format_chat_history(chat_history)
            system_message = get_system_prompt(language)
            template = get_prompt_template(language)
            
            final_prompt = template.format(
                system_message=system_message,
                context=relevant_context, # The context is now the clean, extracted info
                chat_history=history_text,
                question=question
            )

            logger.info("--- RAGService: Calling LLM for final answer synthesis. ---")
            final_answer = self.llm_client.generate_response(final_prompt)

            return {"response": final_answer, "sources": [], "language": language}

        except Exception as e:
            logger.error(f"Error during simple document query: {e}", exc_info=True)
            return {
                "response": "Sorry, an error occurred while processing the document." if language == "english" else "Lo siento, ocurrió un error al procesar el documento.",
                "sources": [],

                "language": language
            }
        
    def _process_and_enrich_chunks(self, file_path: str) -> List[Dict]:
        """Reusable internal method to handle document chunking and performance-enhancing question enrichment logic."""
        logger.info(f"--- RAGService: Step 1 - Processing PDF with Document AI: {file_path} ---")
        chunks = self.doc_processor.process_pdf(file_path)
        if not chunks:
            logger.warning(f"No chunks extracted from {file_path}.")
            return []

        logger.info(f"--- RAGService: Enriching {len(chunks)} chunks with generated questions... ---")
        enriched_chunks = []
        for chunk in chunks:
            # PRESERVE YOUR LOGIC: Store original content for display
            original_content = chunk["content"]
            
            # PRESERVE YOUR LOGIC: Enrich content with questions for better embedding
            enriched_content = original_content
            if chunk.get("questions"):
                questions_text = " ".join(chunk["questions"])
                enriched_content += f"\n\nRelated questions: {questions_text}"
            
            # Update chunk with both versions
            chunk['original_content'] = original_content
            chunk['content'] = enriched_content # The 'content' key now holds the enriched version for embedding
            
            # Add other metadata as before
            source_filename = file_path.split('/')[-1] if '/' in file_path else file_path.split('\\')[-1] if '\\' in file_path else file_path
            chunk['source'] = chunk.get('source') or source_filename
            chunk['page'] = chunk.get("page", 1)
            chunk['type'] = chunk.get("type", "block")
            
            enriched_chunks.append(chunk)
            
        return enriched_chunks
    
    def process_document(self, file_path: str) -> bool:
        """This function process and ingest documents into the permanent vector store, using the reusable enrichment method."""
        logger.info(f"--- RAGService: Starting permanent ingestion for: {file_path} ---")
        try:
            # 1. Process and enrich using your logic
            enriched_chunks = self._process_and_enrich_chunks(file_path)
            if not enriched_chunks:
                return False

            # 2. Generate embeddings from the ENRICHED content
            texts_for_embedding = [chunk['content'] for chunk in enriched_chunks]
            embeddings = self.embedding_service.generate_embeddings(texts_for_embedding)
            if not embeddings or len(embeddings) != len(enriched_chunks):
                logger.error("Embedding generation failed or mismatched.")
                return False

            # 3. Store in the permanent vector database
            add_success = self.vector_store.add_documents(enriched_chunks, embeddings)
            logger.info(f"--- RAGService: Finished permanent ingestion for: {file_path}. Success: {add_success} ---")
            return add_success
        except Exception as e:
            logger.error(f"Error in process_document for {file_path}: {e}", exc_info=True)
            return False
        
    def start_document_chat(self, file_path: str, question: str) -> tuple[Dict[str, Any], List[Dict]]:
        """Starts a temporary chat session about a document. It uses the same enrichment logic but does not save to the permanent DB."""
        logger.info(f"--- RAGService: Initiating document chat for: {file_path} ---")
        try:
            # 1. Process and enrich using your logic
            enriched_chunks = self._process_and_enrich_chunks(file_path)
            if not enriched_chunks:
                raise ValueError("Document could not be processed into chunks.")

            # 2. Answer the first question using the high-quality enriched chunks
            initial_result = self.query_with_context(
                question=question,
                chat_history=[],
                document_chunks=enriched_chunks
            )
            
            # 3. Return the answer and the chunks to be stored in the session
            return initial_result, enriched_chunks
        except Exception as e:
            logger.error(f"Error starting document chat: {e}", exc_info=True)
            raise

    def _get_query_intent(self, question: str) -> str:
        """Uses the LLM to classify the user's query intent."""
        try:
            prompt = QUERY_INTENT_PROMPT.format(question=question)
            response = self.llm_client.generate_response(prompt).strip().upper()
            
            if response in ["HOLISTIC", "SPECIFIC"]:
                logger.info(f"--- LLM classified query intent as: {response} ---")
                return response
            else:
                # Default to specific as it's the less resource-intensive path
                logger.warning(f"LLM intent classification returned unexpected value: '{response}'. Defaulting to SPECIFIC.")
                return "SPECIFIC"
        except Exception as e:
            logger.error(f"Error during query intent classification: {e}. Defaulting to SPECIFIC.")
            return "SPECIFIC"

    def query_with_context(self, question: str, chat_history: List[Dict], document_chunks: List[Dict]) -> Dict:
        """Answers questions using session-specific chunks. It correctly uses the enriched content for searching and original content for display."""
        logger.info("--- RAGService: Querying with specific document context. ---")
        language = self._detect_language(question)
        
        intent = self._get_query_intent(question)

        if intent == "HOLISTIC":
            response_text = self._handle_holistic_query(question, document_chunks, language)
            sources = [{"source": "Entire Document Analysis", "page": "N/A"}]

        else: # Intent is "SPECIFIC"
            logger.info("--- Specific query detected. Using vector search on enriched chunks. ---")
            # Use the enriched content for embedding and search
            texts_for_embedding = [chunk['content'] for chunk in document_chunks]
            chunk_embeddings = self.embedding_service.generate_embeddings(texts_for_embedding)
            query_embedding = self.embedding_service.generate_single_embedding(question)

            similarities = np.dot(chunk_embeddings, query_embedding)
            k = min(MAX_CHUNKS_RETRIEVED, len(document_chunks))
            top_indices = np.argsort(similarities)[-k:][::-1]

            # The search results now contain all the rich metadata
            search_results = [document_chunks[i] for i in top_indices]
            
            # The prompt builder will use 'original_content' for display
            context = self._build_context(search_results)
            prompt = self._build_prompt(question, context, search_results, chat_history, language)
            response_text = self.llm_client.generate_response(prompt)
            sources = [r for r in search_results]

        return {"response": response_text, "sources": sources, "language": language}
    
    def _handle_holistic_query(self, question: str, document_chunks: List[Dict], language: str) -> str:
        """Helper for summaries. It now uses original_content for readability."""
        # Use the clean, original text for summarization prompts
        full_text = "\n\n".join([chunk['original_content'] for chunk in document_chunks])

        holistic_prompt = f"""Based on the following document, {question}:\n\n---\n{full_text}\n---"""
        return self.llm_client.generate_response(holistic_prompt)
=======
    
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
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
    
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
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 340274c (Citation included)

            # Create prompt with citations
            logger.info(f"--- RAGService: Building prompt with citations... ---")
            context = self._build_context(search_results)  # Fallback
            prompt = self._build_prompt(question, context, search_results, chat_history, language)

<<<<<<< HEAD
=======
            
            # Build context from search results
            context = self._build_context(search_results)
            
            # Create prompt with chat history
            logger.info(f"--- RAGService: Building prompt... ---")
            prompt = self._build_prompt(question, context, chat_history, language)
            
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
=======
>>>>>>> 340274c (Citation included)
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
<<<<<<< HEAD
<<<<<<< HEAD
            # Use LLM to identify the language
=======
            # Use simple heuristic for very short texts
            if len(text.strip()) < 10:
                spanish_words = ['el', 'la', 'es', 'de', 'que', 'y', 'en', 'un', 'una', 'con', 'por', 'para']
                words = re.findall(r'\b\w+\b', text.lower())
                spanish_count = sum(1 for word in words if word in spanish_words)
                return "spanish" if spanish_count > len(words) * 0.2 else "english"
            
            # Use LLM for longer texts
>>>>>>> c4d328f (Response with clickable citations with popup previewsworking)
            prompt = LANGUAGE_DETECTION_PROMPT.format(text=text)
            
            response = self.llm_client.generate_response(prompt).strip().lower()
            logger.info(f"The system detected {response} as the language from the query\n{50 * '-----'}")
            return "spanish" if "spanish" in response else "english"
            
        except Exception as e:
            logger.warning(f"Language detection failed: {str(e)}, defaulting to english")
<<<<<<< HEAD
            return "english"
        
    def _build_context(self, search_results: List[Dict]) -> str:
        """Builds context for the prompt using the clean, original content."""
        return "\n\n".join([result.get('original_content', result['content']) for result in search_results])

    def _build_prompt(self, question: str, context: str, search_results: List[Dict], chat_history: List[Dict], language: str) -> str:
        """Builds the final prompt, showing the clean, original content to the LLM."""
        try:
            # Build numbered context with source references
            numbered_context = []
            for i, result in enumerate(search_results, 1):
                source = result.get('source', 'Unknown')
                page = result.get('page', '')
                # PRESERVE YOUR LOGIC: Use original_content for what the LLM sees
                content = result.get('original_content', result['content'])
                numbered_context.append(f"[{i}] {content}\nSource: {source}, page {page}")
            
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
            if not chat_history: return ""
            parts = [f"User: {msg.get('question', '')}\nAssistant: {msg.get('response', '')}" for msg in chat_history[-CONTEXT_HISTORY_MESSAGES:]]
            return "Chat History:\n" + "\n".join(parts)
        except Exception as e:
            logger.error(f"Error formatting the chat history: {str(e)}")

    def is_topic_follow_up(self, question: str, chat_history: List[Dict]) -> bool:
        """Uses the LLM to determine if a new question is a follow-up to the existing conversation or a change in topic."""
        # We only need the last message for context
        if not chat_history:
            return True # If there's no history, it's the first question, so it's a follow-up

        try:
            # Format the last Q&A pair for the prompt
            last_exchange = chat_history[-1]
            history_context = f"User: {last_exchange.get('question')}\nAssistant: {last_exchange.get('response')}"

            prompt = TOPIC_CHANGE_PROMPT.format(chat_history = history_context, question = question)
            response = self.llm_client.generate_response(prompt).strip().upper()

            logger.info(f"--- LLM classified topic as: {response} ---")
            if response == "NEW_TOPIC":
                return False
            # Default to FOLLOW-UP for safety and any other LLM response
            return True

        except Exception as e:
            logger.error(f"Error during topic change detection: {e}. Defaulting to FOLLOW-UP.")
            return True

    def _format_history_for_router(self, history: List[Dict[str, Any]]) -> str:
        """Helper function to format chat history specifically for the router prompt. It expects history to be a list of dicts with 'query' and 'response' keys."""
        try:
            if not history:
                return "No history yet."
            
            # Using .get() provides safety if a key is missing from a turn.
            # This format matches what the ROUTER_PROMPT expects.
            parts = [f"User: {turn.get('question', '')}\nAssistant: {turn.get('response', '')}" for turn in history]
            return "\n\n".join(parts)

        except Exception as e:
            logger.error(f"Error formatting history for router: {e}", exc_info=True)
            return "" # Return empty string on error

    def determine_conversational_mode(self, query: str, history: List[Dict[str, Any]]) -> str:
        """ Uses an LLM call to classify the user's query to determine the conversational mode. This new method will act as my "master router".
            It gets the user's current query and The conversation history from the session.
            Then it returns either 'DOCUMENT_QA' or 'GENERAL_QA'."""
        try:
            logger.info("--- RAGService: Determining conversational mode ---")

            # Use the new helper to format history for the router
            formatted_history = self._format_history_for_router(history)
        
            # The prompt expects {history} and {query} placeholders.
            prompt = ROUTER_PROMPT.format(history = formatted_history, query = query)
            
            logger.debug(f"Router prompt: {prompt}")

            # Using your existing llm_client. We expect a short response.
            response = self.llm_client.generate_response(prompt).strip()
            
            logger.info(f"Router raw decision: '{response}'")

            # The ROUTER_PROMPT asks the LLM to return a specific string.
            # Checking for the presence of the string for robustness.
            if "DOCUMENT_HANDLER" in response:
                logger.info("Mode has been set to DOCUMENT_QA")
                return "DOCUMENT_QA"
            else:
                logger.info("Mode has been set to GENERAL_QA")
                return "GENERAL_QA"

        except Exception as e:
            logger.error(f"Error in determining conversational mode: {e}", exc_info=True)
            # Default to general QA on error for operational safety
            return "GENERAL_QA"
=======
            spanish_words = ['el', 'la', 'es', 'de', 'que', 'y', 'en', 'un', 'una', 'con', 'por', 'para']
            words = re.findall(r'\b\w+\b', text.lower())
            spanish_count = sum(1 for word in words if word in spanish_words)
            return "spanish" if spanish_count > len(words) * 0.2 else "english"
        except:
=======
>>>>>>> c4d328f (Response with clickable citations with popup previewsworking)
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
<<<<<<< HEAD
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
=======
        
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
>>>>>>> 9ea43c2 (Extracting text easily from document provided and answer only 1 question about the document)
