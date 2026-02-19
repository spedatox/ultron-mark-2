import chromadb
from chromadb.utils import embedding_functions
import os
import uuid
from datetime import datetime

# Initialize ChromaDB client
# Using a persistent client to save data to disk
CHROMA_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# Use default embedding function (Sentence Transformers)
# This runs locally and doesn't require an API key for embeddings, 
# saving OpenAI credits and reducing dependency.
default_ef = embedding_functions.DefaultEmbeddingFunction()

# Get or create the collection for chat history
collection = client.get_or_create_collection(
    name="ultron_memory",
    embedding_function=default_ef
)

class MemoryService:
    @staticmethod
    def store_message(role: str, content: str, metadata: dict = None):
        """
        Store a message in the vector database.
        """
        if metadata is None:
            metadata = {}
        
        # Add timestamp and role to metadata
        metadata["timestamp"] = datetime.now().isoformat()
        metadata["role"] = role
        
        # Generate a unique ID
        msg_id = str(uuid.uuid4())
        
        collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[msg_id]
        )
        print(f"Stored message in memory: {role} - {content[:50]}...")

    @staticmethod
    def retrieve_context(query: str, n_results: int = 5):
        """
        Retrieve relevant past messages based on the query.
        """
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Format results for the LLM
        context_messages = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i]
                role = meta.get("role", "unknown")
                timestamp = meta.get("timestamp", "")
                context_messages.append(f"[{timestamp}] {role}: {doc}")
                
        return "\n".join(context_messages)

    @staticmethod
    def get_recent_history(limit: int = 10):
        """
        Get the most recent messages (simple retrieval, not semantic).
        Note: Chroma isn't optimized for time-based sorting without metadata filtering,
        so for a real app we might want a SQL DB for the chat log and Vector for search.
        For this prototype, we'll rely on the client sending recent history or 
        just use semantic search.
        
        Actually, for the 'last N chat turns' requirement, the frontend usually sends 
        the conversation history. The Vector DB is for *long-term* memory (RAG).
        So this method might not be strictly necessary if the frontend sends context,
        but it's good to have for background processing.
        """
        # This is tricky in pure Vector DB without a separate index. 
        # We will rely on the frontend to pass the immediate conversation history,
        # and use this service specifically for RAG (finding *old* relevant stuff).
        pass

    @staticmethod
    def clear_all_memory():
        """
        Clear all stored memories from the vector database.
        This resets Ultron's long-term memory.
        """
        global collection
        # Delete and recreate the collection
        client.delete_collection(name="ultron_memory")
        collection = client.get_or_create_collection(
            name="ultron_memory",
            embedding_function=default_ef
        )
        return True
