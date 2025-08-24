import argparse
import json
from pathlib import Path
import datetime

# --- Early check for required libraries ---
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    print("Error: Required 'firebase-admin' library is not installed.")
    print("Please install it by running: pip install -r scripts/requirements.txt")
    exit(1)


def sync_to_firestore(transcript_path: Path, service_account_key_path: Path):
    """
    Reads a transcript JSON file and syncs its metadata to a Firestore collection.
    """
    print("--- Initializing Firebase ---")

    # 1. Initialize Firebase Admin SDK
    if not service_account_key_path.exists():
        print(f"Error: Firebase service account key not found at '{service_account_key_path}'.")
        print("Download it from your Firebase project settings and provide the correct path.")
        exit(1)

    try:
        cred = credentials.Certificate(str(service_account_key_path))
        # Check if the app is already initialized to prevent crashing on re-runs
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("Firebase Admin SDK initialized successfully.")
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        exit(1)

    # 2. Load the local transcript JSON
    print(f"\n--- Processing Transcript ---")
    print(f"Loading file: {transcript_path}")
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error: Could not read or parse the transcript file. Details: {e}")
        exit(1)

    meeting_id = data.get("meeting_id")
    if not meeting_id:
        print("Error: JSON file must contain a 'meeting_id' key.")
        exit(1)

    # 3. Prepare data for Firestore
    # We use .get() to safely access keys that might not exist in the JSON.
    full_transcript = "\n".join([seg.get('text', '') for seg in data.get('segments', [])])

    firestore_data = {
        "meeting_id": meeting_id,
        "title": data.get("title", f"Meeting - {meeting_id}"),
        "date": data.get("date", datetime.datetime.now(datetime.timezone.utc).isoformat()),
        "summary": data.get("summary", ""),
        "tags": data.get("tags", []),
        "full_transcript": full_transcript,
        "synced_at": datetime.datetime.now(datetime.timezone.utc)
    }

    # 4. Upsert the document to Firestore
    print(f"\n--- Syncing to Firestore ---")
    print(f"Target collection: 'meetings'")
    print(f"Document ID: '{meeting_id}'")

    try:
        doc_ref = db.collection("meetings").document(meeting_id)
        doc_ref.set(firestore_data, merge=True) # Use merge=True to upsert
        print("Document successfully synced to Firestore.")
    except Exception as e:
        print(f"Error syncing document to Firestore: {e}")
        exit(1)

    print("\n--- Success ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sync a meeting transcript's metadata to Google Firestore."
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the transcript JSON file (e.g., local_data/transcripts/meetingA.json)."
    )
    parser.add_argument(
        "--key",
        type=str,
        default="serviceAccountKey.json",
        help="Path to your Firebase service account key JSON file. Defaults to './serviceAccountKey.json'."
    )
    args = parser.parse_args()

    sync_to_firestore(Path(args.input_file), Path(args.key))
