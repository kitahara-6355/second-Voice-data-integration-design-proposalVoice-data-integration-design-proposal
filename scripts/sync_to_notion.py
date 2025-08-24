import argparse
import json
import os
from pathlib import Path
import datetime

# --- Early check for required libraries ---
try:
    from notion_client import Client
except ImportError:
    print("Error: Required 'notion-client' library is not installed.")
    print("Please install it by running: pip install -r scripts/requirements.txt")
    exit(1)


def sync_to_notion(transcript_path: Path):
    """
    Reads a transcript JSON and creates a new page in a Notion database.
    """
    print("--- Initializing Notion Client ---")

    # 1. Get Notion API Token and Database ID from environment variables
    notion_token = os.getenv("NOTION_API_TOKEN")
    database_id = os.getenv("NOTION_DATABASE_ID")

    if not notion_token or not database_id:
        print("Error: Required environment variables NOTION_API_TOKEN or NOTION_DATABASE_ID are not set.")
        print("\nPlease set them before running the script.")
        print("For Linux/macOS: export NOTION_API_TOKEN='your_token'")
        print("For Windows: set NOTION_API_TOKEN='your_token'")
        exit(1)

    try:
        notion = Client(auth=notion_token)
        print("Notion client initialized successfully.")
    except Exception as e:
        print(f"Error initializing Notion client: {e}")
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

    # 3. Prepare Notion page properties and content
    # This maps data from our JSON to the schema defined in notion/notion_schema.md
    title = data.get("title", f"Meeting - {meeting_id}")
    tags = [{"name": tag} for tag in data.get("tags", [])] # Format for Multi-select
    summary = data.get("summary", "No summary available.")
    # Notion API expects ISO 8601 format for dates.
    meeting_date = data.get("date", datetime.datetime.now().isoformat())

    full_transcript = "\n".join([seg.get('text', '') for seg in data.get('segments', [])])

    print(f"Preparing page with title: '{title}'")

    # 4. Create the new page in Notion
    try:
        new_page_properties = {
            "Meeting Title": {"title": [{"text": {"content": title}}]},
            "Date": {"date": {"start": meeting_date}},
            "Tags": {"multi_select": tags},
            "Summary": {"rich_text": [{"text": {"content": summary}}]},
            "Firestore ID": {"rich_text": [{"text": {"content": meeting_id}}]}
        }

        new_page_children = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": { "rich_text": [{"type": "text", "text": {"content": "Full Transcript"}}]}
            },
            {
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{"type": "text", "text": {"content": full_transcript or "Transcript not available."}}],
                    "language": "plain text"
                }
            }
        ]

        print("Sending request to create page in Notion...")
        created_page = notion.pages.create(
            parent={"database_id": database_id},
            properties=new_page_properties,
            children=new_page_children
        )

        print("\n--- Success ---")
        print(f"Successfully created Notion page!")
        print(f"URL: {created_page['url']}")

    except Exception as e:
        print(f"\nError creating Notion page: {e}")
        print("Please check the following:")
        print("1. Your NOTION_API_TOKEN is correct and has read/write permissions.")
        print("2. Your NOTION_DATABASE_ID is correct.")
        print("3. The integration has been shared with the target database.")
        print("4. The property names in this script match your Notion database schema exactly.")
        exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sync a meeting transcript to a Notion Database."
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the transcript JSON file (e.g., local_data/transcripts/meetingA.json)."
    )
    args = parser.parse_args()

    sync_to_notion(Path(args.input_file))
