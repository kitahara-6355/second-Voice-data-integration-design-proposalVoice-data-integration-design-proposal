import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

# --- Early check for required libraries ---
try:
    from sentence_transformers import SentenceTransformer
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("Error: Required libraries are not installed.")
    print("Please install them by running: pip install -r services/api/requirements.txt")
    exit(1)

# --- Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
CHROMA_PERSIST_DIR = "local_env/chroma_db"
COLLECTION_NAME = "meetings"

def get_project_root() -> Path:
    """Gets the project root directory based on the script's location."""
    return Path(__file__).parent.parent.parent.resolve()

# --- Lifespan Management (for startup and shutdown events) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    Loads the model and DB client on startup.
    """
    logger.info("Application startup...")

    project_root = get_project_root()
    persist_directory = project_root / CHROMA_PERSIST_DIR

    if not persist_directory.exists():
        logger.error(f"ChromaDB persistence directory not found at '{persist_directory}'.")
        logger.error("Please run the `embed_and_upsert.py` script first to create the database.")
        app.state.model = None
        app.state.collection = None
    else:
        # Load SentenceTransformer model
        logger.info(f"Loading model: {MODEL_NAME}...")
        try:
            app.state.model = SentenceTransformer(MODEL_NAME)
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model: {e}")
            app.state.model = None

        # Initialize ChromaDB client
        logger.info(f"Initializing ChromaDB client from: {persist_directory}...")
        try:
            client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(persist_directory)
            ))
            app.state.collection = client.get_collection(name=COLLECTION_NAME)
            logger.info(f"Successfully connected to collection '{COLLECTION_NAME}'.")
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB collection: {e}")
            app.state.collection = None

    yield

    # --- Shutdown logic (if any) ---
    logger.info("Application shutdown.")
    app.state.model = None
    app.state.collection = None


app = FastAPI(lifespan=lifespan)


# --- API Endpoints ---
@app.get("/")
def read_root():
    """Root endpoint for health check."""
    return {"status": "ok", "message": "Welcome to the PixelRecordings-Analytics Search API"}

@app.get("/search")
def search(
    q: str = Query(..., min_length=1, description="The search query text."),
    top_k: int = Query(5, ge=1, le=20, description="The number of top results to return.")
):
    """
    Performs a semantic search on the meeting transcripts.
    """
    if not app.state.model or not app.state.collection:
        raise HTTPException(
            status_code=503,
            detail="Service is unavailable. Model or database not loaded. Check server logs."
        )

    logger.info(f"Received search query: '{q}' with top_k={top_k}")

    try:
        # Generate embedding for the query
        query_embedding = app.state.model.encode(q).tolist()

        # Perform the query
        results = app.state.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        return JSONResponse(content=results)

    except Exception as e:
        logger.error(f"An error occurred during search: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred during search.")

# To run this app:
# uvicorn services.api.app:app --reload
