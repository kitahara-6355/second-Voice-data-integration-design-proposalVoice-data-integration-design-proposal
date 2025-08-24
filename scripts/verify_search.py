import argparse
from pathlib import Path
import pprint

# --- Early check for required libraries ---
try:
    from sentence_transformers import SentenceTransformer
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("Error: Required libraries are not installed.")
    print("Please install them by running: pip install -r requirements.txt")
    exit(1)

# --- Constants ---
# These must match the constants in embed_and_upsert.py
MODEL_NAME = "all-MiniLM-L6-v2"
CHROMA_PERSIST_DIR = "local_env/chroma_db"
COLLECTION_NAME = "meetings"


def get_project_root() -> Path:
    """Gets the project root directory based on the script's location."""
    return Path(__file__).parent.parent.resolve()

def search_collection(query: str, top_k: int = 5):
    """
    Searches the ChromaDB collection for text segments similar to the query.
    """
    project_root = get_project_root()
    persist_directory = project_root / CHROMA_PERSIST_DIR

    if not persist_directory.exists():
        print(f"Error: ChromaDB persistence directory not found at '{persist_directory}'.")
        print("Please run the `embed_and_upsert.py` script first to create the database.")
        exit(1)

    print("--- Initializing ---")
    print(f"Model: {MODEL_NAME}")
    print(f"ChromaDB persistence directory: {persist_directory}")

    # 1. Initialize the Sentence Transformer model
    try:
        model = SentenceTransformer(MODEL_NAME)
    except Exception as e:
        print(f"Error: Could not load SentenceTransformer model '{MODEL_NAME}'.")
        print(f"Details: {e}")
        exit(1)

    # 2. Initialize the ChromaDB client
    client = chromadb.PersistentClient(path=str(persist_directory))

    try:
        collection = client.get_collection(name=COLLECTION_NAME)
    except ValueError:
        print(f"Error: Collection '{COLLECTION_NAME}' not found in the database.")
        print("Please ensure you have run `embed_and_upsert.py` to populate it.")
        exit(1)

    # 3. Generate embedding for the query
    print(f"\n--- Searching ---")
    print(f"Query: '{query}'")
    print(f"Returning top {top_k} results.")

    query_embedding = model.encode(query).tolist()

    # 4. Perform the query
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    # 5. Print the results
    print("\n--- Results ---")
    if not results or not results.get('ids', [[]])[0]:
        print("No results found.")
        return

    # The result is a dictionary containing lists of lists. We access the first query's results.
    ids = results['ids'][0]
    distances = results['distances'][0]
    metadatas = results['metadatas'][0]
    documents = results['documents'][0]

    for i in range(len(ids)):
        print(f"Result {i+1}:")
        print(f"  Distance: {distances[i]:.4f}")
        print(f"  Document: \"{documents[i]}\"")
        print(f"  Metadata:")
        pprint.pprint(metadatas[i], indent=4)
        print("-" * 20)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Search for similar text in the meeting transcripts stored in ChromaDB."
    )
    parser.add_argument(
        "query",
        type=str,
        help="The search query text."
    )
    parser.add_argument(
        "--top_k",
        type=int,
        default=5,
        help="The number of top results to return."
    )
    args = parser.parse_args()

    search_collection(args.query, args.top_k)
