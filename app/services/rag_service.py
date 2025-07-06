# Path: app/services/rag_service.py

from typing import Any, List, Dict
from app.services.llm_client import OllamaClient
from app.services.embeddings import EmbeddingService
from app.services.vectorstore import VectorStoreService
from app.services.data_loader import DocumentProcessor
from app.core.config import CONTEXT_HISTORY_MESSAGES, GOOGLE_PROJECT_ID, GOOGLE_LOCATION, GOOGLE_PROCESSOR_ID, MAX_CHUNKS_RETRIEVED
from app.core.prompts import get_system_prompt, get_prompt_template, get_query_intent_prompt, LANGUAGE_DETECTION_PROMPT, ROUTER_PROMPT, EXTRACTION_PROMPT_TEMPLATE,DOCUMENT_SUMMARY_PROMPT
import logging
import os
import re
import numpy as np

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        try:
            logger.info("Initializing RAGService components...")
            self.llm_client = OllamaClient()
            self.embedding_service = EmbeddingService()
            self.vector_store = VectorStoreService()
            
            if not all([GOOGLE_PROJECT_ID, GOOGLE_LOCATION, GOOGLE_PROCESSOR_ID]):
                logger.error("Google Document AI credentials are not fully configured.")
                raise Exception("Google Document AI credentials not configured properly.")
            
            self.doc_processor = DocumentProcessor()
            logger.info("RAGService initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}", exc_info=True)
            raise

    def _create_document_summary(self, full_text: str) -> str:
        """
        Uses an LLM call to create a concise summary of the document text.
        This summary is used as context for the router.
        """
        try:            
            prompt = DOCUMENT_SUMMARY_PROMPT.format(full_text=full_text)
            
            summary = self.llm_client.generate_response(prompt).strip()
            logger.info(f"--- RAGService: Generated document summary: '{summary}' ---")
            return summary
        except Exception as e:
            logger.error(f"--- RAGService: Failed to create document summary: {e} ---", exc_info=True)
            return "No summary could be generated." # Return a default value on error

    def _get_query_intent(self, question: str, language: str) -> str:
        """
        Uses the LLM to classify the user's query intent as either HOLISTIC or SPECIFIC.
        This version is more robust and cleans the LLM response before parsing.
        """
        try:
            prompt_template = get_query_intent_prompt(language)
            prompt = prompt_template.format(question=question)
            
            raw_response = self.llm_client.generate_response(prompt)
            
            # --- THE CRUCIAL FIX ---
            # Clean the response to handle markdown or extra spaces from the LLM.
            # This looks for the core word, ignoring surrounding characters.
            cleaned_response = raw_response.strip().upper()
            
            logger.info(f"Intent detection for '{question[:30]}...' -> Raw LLM response: '{raw_response}', Cleaned: '{cleaned_response}'")

            if "HOLISTICO" in cleaned_response or "HOLISTIC" in cleaned_response:
                logger.info("--- LLM classified query intent as: HOLISTIC ---")
                return "HOLISTIC"
            
            if "ESPECIFICO" in cleaned_response or "SPECIFIC" in cleaned_response:
                logger.info("--- LLM classified query intent as: SPECIFIC ---")
                return "SPECIFIC"

            # Fallback if the classification is still unclear
            logger.warning(f"Could not reliably classify intent from response: '{raw_response}'. Defaulting to SPECIFIC.")
            return "SPECIFIC"
                
        except Exception as e:
            logger.error(f"Error during query intent classification: {e}. Defaulting to SPECIFIC.", exc_info=True)
            return "SPECIFIC"

    def query_simple_document(self, question: str, full_text: str, chat_history: List[Dict]) -> Dict:
        """
        Answers a question about a simple document, using multilingual intent detection.
        """
        logger.info("--- RAGService: Querying simple document, determining intent first. ---")
        language = self._detect_language(question)
        
        # Pass the detected language to the intent classifier
        intent = self._get_query_intent(question, language)
        
        try:
            relevant_context = ""
            if intent == "HOLISTIC":
                logger.info("--- RAGService: Holistic intent detected. Using full document text. ---")
                relevant_context = full_text
            else: # intent == "SPECIFIC"
                logger.info("--- RAGService: Specific intent detected. Extracting relevant snippets. ---")
                extraction_prompt = EXTRACTION_PROMPT_TEMPLATE.format(
                    full_text=full_text,
                    question=question
                )
                relevant_context = self.llm_client.generate_response(extraction_prompt)

                if "no relevant information found" in relevant_context.lower():
                    return {
                        "response": "I couldn't find any information in the document for your question." 
                                    if language == "english" else 
                                    "No encontré información en el documento para tu pregunta.",
                        "sources": [],
                        "language": language
                    }

            # --- Final Answer Synthesis ---
            history_text = self._format_chat_history(chat_history)
            system_message = get_system_prompt(language)
            template = get_prompt_template(language)
            
            final_prompt = template.format(
                system_message=system_message,
                context=relevant_context,
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

    def process_document(self, file_path: str) -> bool:
        """
        Processes a complex document for the knowledge base. It chunks, enriches,
        embeds, and stores the document in the permanent vector store.
        """
        logger.info(f"--- RAGService: Starting permanent ingestion for: {file_path} ---")
        try:
            # 1. Process with DocumentAI and enrich with questions
            enriched_chunks = self._process_and_enrich_chunks(file_path)
            if not enriched_chunks:
                return False

            # 2. Generate embeddings for the enriched content
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

    def query(self, question: str, chat_history: List[Dict] = None) -> Dict:
        """Queries the general knowledge base (documents in the vector store)."""
        try:
            logger.info(f"--- RAGService: Received general query: '{question}' ---")
            language = self._detect_language(question)
            
            query_embedding = self.embedding_service.generate_single_embedding(question)
            search_results = self.vector_store.search(query_embedding, n_results=MAX_CHUNKS_RETRIEVED)
            
            context = self._build_context(search_results)
            prompt = self._build_prompt(question, context, search_results, chat_history, language)
            
            response_text = self.llm_client.generate_response(prompt)
            
            return {
                "response": response_text,
                "sources": [r.get("metadata", {}) for r in search_results],
                "language": language
            }
        except Exception as e:
            logger.error(f"--- RAGService: Error during general query: {e} ---", exc_info=True)
            raise

    def determine_conversational_mode(self, query: str) -> str:
        """
        Uses a simplified, rule-based prompt to classify the query's intent
        based solely on the query's content.
        """
        try:
            logger.info("--- RAGService: Determining conversational mode (Simplified, Rule-Based Router) ---")
            
            prompt = ROUTER_PROMPT.format(query=query)
            
            response = self.llm_client.generate_response(prompt).strip().upper()
            # Clean the response to handle potential markdown
            cleaned_response = re.sub(r'[^A-Z_]', '', response)
            
            logger.info(f"Router raw response: '{response}', Cleaned: '{cleaned_response}'")

            if "GENERAL_KNOWLEDGE_BASE" in cleaned_response:
                logger.info("--- Router decision: GENERAL_KNOWLEDGE_BASE ---")
                return "GENERAL_QA"
            else:
                # Default to Document Handler if the response is anything else
                logger.info("--- Router decision: DOCUMENT_HANDLER ---")
                return "DOCUMENT_QA"

        except Exception as e:
            logger.error(f"Error in determining conversational mode: {e}", exc_info=True)
            return "GENERAL_QA" # Default to general on error

    def _process_and_enrich_chunks(self, file_path: str) -> List[Dict]:
        """Internal method to handle Document AI chunking and question enrichment."""
        chunks = self.doc_processor.process_pdf(file_path)
        if not chunks:
            logger.warning(f"No chunks extracted from {file_path}.")
            return []

        enriched_chunks = []
        for chunk in chunks:
            original_content = chunk["content"]
            enriched_content = original_content
            if chunk.get("questions"):
                questions_text = " ".join(chunk["questions"])
                enriched_content += f"\n\nRelated questions: {questions_text}"
            
            chunk['original_content'] = original_content
            chunk['content'] = enriched_content
            chunk['source'] = chunk.get('document_name', os.path.basename(file_path))
            
            enriched_chunks.append(chunk)
            
        return enriched_chunks

    def _detect_language(self, text: str) -> str:
        """
        Detects the language of the given text using the LLM for better accuracy.
        """
        try:
            if not text.strip():
                return "english" # Default for empty strings

            prompt = LANGUAGE_DETECTION_PROMPT.format(text=text)
            response = self.llm_client.generate_response(prompt).strip().lower()

            logger.info(f"Language detection for '{text[:30]}...' -> Raw LLM response: '{response}'")

            if "spanish" in response:
                return "spanish"
            else:
                return "english"
                
        except Exception as e:
            logger.error(f"LLM-based language detection failed: {e}. Defaulting to English.", exc_info=True)
            return "english"

    def _build_context(self, search_results: List[Dict]) -> str:
        """Builds a string context from search results for the LLM prompt."""
        return "\n\n".join([result.get('original_content', result.get('content', '')) for result in search_results])

    def _build_prompt(self, question: str, context: str, search_results: List[Dict], chat_history: List[Dict], language: str) -> str:
        """Builds the final prompt for the LLM, including numbered source citations."""
        try:
            numbered_context = []
            for i, result in enumerate(search_results, 1):
                content = result.get('original_content', result.get('content', ''))
                source = result.get('source', 'Unknown')
                page = result.get('page', 'N/A')
                numbered_context.append(f"[{i}] {content}\nSource: {source}, page {page}")
            
            context_with_sources = "\n\n".join(numbered_context)
            
            history_text = self._format_chat_history(chat_history)
            system_message = get_system_prompt(language)
            template = get_prompt_template(language)
            
            return template.format(
                system_message=system_message,
                context=context_with_sources,
                chat_history=history_text,
                question=question
            )
        except Exception as e:
            logger.error(f"Error building prompt: {e}")
            return f"Context: {context}\nQuestion: {question}\nAnswer:"

    def _format_chat_history(self, chat_history: List[Dict]) -> str:
        """Formats chat history into a string for the prompt."""
        if not chat_history:
            return ""
        parts = [f"User: {msg.get('question', '')}\nAssistant: {msg.get('response', '')}" for msg in chat_history[-CONTEXT_HISTORY_MESSAGES:]]
        return "Chat History:\n" + "\n\n".join(parts)

    def _format_history_for_router(self, history: List[Dict[str, Any]]) -> str:
        """Formats chat history specifically for the router prompt."""
        if not history:
            return "No history yet."
        parts = [f"User: {turn.get('question', '')}\nAssistant: {turn.get('response', '')}" for turn in history]
        return "\n\n".join(parts)