import chromadb
from app.core.config import CHROMA_PERSIST_DIR, COLLECTION_NAME, DEFAULT_HEADER_TEXT # Added DEFAULT_HEADER_TEXT for VectorStoreService
from app.services.vectorstore import VectorStoreService # Import your service
import logging
import pprint # For pretty printing dictionaries

# Configure basic logging for the script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def inspect_collection_content(collection: chromadb.api.models.Collection.Collection, limit: int = 1000):
    """
    Inspects and prints the content of a given ChromaDB collection.
    """
    try:
        count = collection.count()
        logger.info(f"Total documents in collection '{collection.name}': {count}")

        if count == 0:
            print(f"Collection '{collection.name}' is empty.")
            return

        effective_limit = min(limit, count) if limit is not None else count
        
        print(f"\n--- Retrieving up to {effective_limit} documents from '{collection.name}' ---")
        results = collection.get(
            limit=effective_limit,
            include=["metadatas", "documents"] 
        )

        if not results or not results.get("ids"):
            print("No documents found or unexpected result format.")
            return

        for i in range(len(results["ids"])):
            print(f"\n--- Document ID: {results['ids'][i]} ---")
            print("Metadata:")
            pprint.pprint(results["metadatas"][i])
            print("Content (first 300 chars):")
            print(f"{results['documents'][i][:300]}...")
            print("-" * 30)

    except Exception as e:
        logger.error(f"An error occurred during collection inspection: {e}", exc_info=True)

def main():
    try:
        # Instantiate VectorStoreService to use its methods
        # This will also initialize the client and get/create the collection
        vs_service = VectorStoreService() 
        logger.info(f"Connected to ChromaDB and using collection '{vs_service.collection.name}'.")

        # Ask user if they want to delete the collection
        user_choice = input(f"Do you want to delete the collection '{vs_service.collection.name}' and recreate it? (yes/no): ").strip().lower()

        if user_choice == 'yes':
            logger.info(f"User chose to delete collection '{vs_service.collection.name}'.")
            vs_service.delete_collection() # This method also recreates it
            print(f"Collection '{vs_service.collection.name}' has been deleted and recreated (it's now empty).")
        elif user_choice == 'no':
            logger.info(f"User chose not to delete collection '{vs_service.collection.name}'. Proceeding to inspect.")
            inspect_collection_content(vs_service.collection)
        else:
            logger.info(f"Invalid input. Proceeding to inspect collection '{vs_service.collection.name}'.")
            inspect_collection_content(vs_service.collection)
            
    except Exception as e:
        logger.error(f"An error occurred in the main script: {e}", exc_info=True)

if __name__ == "__main__":
    main()