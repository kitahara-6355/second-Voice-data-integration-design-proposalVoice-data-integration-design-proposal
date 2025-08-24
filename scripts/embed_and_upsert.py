import argparse
import json
import os
from pathlib import Path

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
# Use a standard, effective model.
MODEL_NAME = "all-MiniLM-L6-v2"
# Define where the ChromaDB data will be persisted.
# This path is relative to the project root.
CHROMA_PERSIST_DIR = "local_env/chroma_db"
# The name of the collection to store meeting segments.
COLLECTION_NAME = "meetings"


def get_project_root() -> Path:
    """Gets the project root directory based on the script's location."""
    return Path(__file__).parent.parent.resolve()

def upsert_meeting_transcript(transcript_path: Path):
    """
    Loads a meeting transcript, generates embeddings for each segment,
    and upserts them into a persistent ChromaDB collection.
    """
    project_root = get_project_root()
    persist_directory = project_root / CHROMA_PERSIST_DIR

    print("--- Initializing ---")
    print(f"Model: {MODEL_NAME}")
    print(f"ChromaDB persistence directory: {persist_directory}")

    # 1. Initialize the Sentence Transformer model
    try:
        model = SentenceTransformer(MODEL_NAME)
    except Exception as e:
        print(f"Error: Could not load SentenceTransformer model '{MODEL_NAME}'.")
        print("This may be due to a network issue or a problem with the model cache.")
        print(f"Details: {e}")
        exit(1)

    # 2. Initialize the ChromaDB client
    # The Settings object ensures data is saved to disk.
    client = chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=str(persist_directory)
    ))
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    # 3. Load the transcript JSON file
    print(f"\n--- Processing Transcript ---")
    print(f"Loading file: {transcript_path}")
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error: Could not read or parse the transcript file. Details: {e}")
        exit(1)

    meeting_id = data.get("meeting_id")
    segments = data.get("segments", [])

    if not meeting_id or not segments:
        print("Error: JSON file is missing 'meeting_id' or 'segments' key.")
        exit(1)

    # 4. Prepare data for batch upsert
    print(f"Found {len(segments)} segments for meeting '{meeting_id}'.")
    ids = []
    documents = []
    metadatas = []

    for i, seg in enumerate(segments):
        text = seg.get("text", "").strip()
        if not text:
            continue  # Skip empty segments

        # Create a unique ID for each segment
        doc_id = f"{meeting_id}_{i}"

        # Prepare metadata
        metadata = {
            "meeting_id": meeting_id,
            "start": seg.get("start", ""),
            "end": seg.get("end", "")
        }

        ids.append(doc_id)
        documents.append(text)
        metadatas.append(metadata)

    if not documents:
        print("No valid text segments found to process.")
        return

    # 5. Generate embeddings and upsert into ChromaDB
    print(f"Generating embeddings for {len(documents)} segments...")
    embeddings = model.encode(documents, show_progress_bar=True).tolist()

    print("Upserting documents into ChromaDB collection...")
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        metadatas=metadatas,
        documents=documents
    )

    # Note: ChromaDB with local persistence auto-saves.
    # client.persist() is deprecated in newer versions.

    print("\n--- Success ---")
    print(f"Successfully upserted {len(ids)} documents into the '{COLLECTION_NAME}' collection.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate embeddings for a meeting transcript and upsert into ChromaDB."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the transcript JSON file (e.g., local_data/transcripts/meetingA.json)."
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    upsert_meeting_transcript(input_path)
