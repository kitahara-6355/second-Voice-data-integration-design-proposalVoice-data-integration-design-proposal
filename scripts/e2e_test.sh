#!/bin/bash
#
# Description: Runs an end-to-end test of the data pipeline.
#
# This test covers:
#   1. Upserting a sample transcript to ChromaDB.
#   2. Verifying that search returns a result.
#   3. Syncing metadata to Firestore.
#   4. Syncing metadata to Notion.
#   5. Cleaning up the created data in Firestore.

set -e # Exit immediately if a command exits with a non-zero status.

# --- Test Configuration ---
SAMPLE_TRANSCRIPT="local_data/transcripts/sample_meeting_for_test.json"
MEETING_ID="sample_meeting_for_test"
SEARCH_QUERY="search functionality"
SERVICE_ACCOUNT_KEY="serviceAccountKey.json"

# --- Helper Functions ---
print_step() {
    echo
    echo "================================================="
    echo "STEP: $1"
    echo "================================================="
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "Error: Required command '$1' not found."
        echo "$2"
        exit 1
    fi
}

# --- Pre-flight Checks ---
print_step "Performing pre-flight checks"

if [ ! -f "$SAMPLE_TRANSCRIPT" ]; then
    echo "Error: Sample transcript file not found at '$SAMPLE_TRANSCRIPT'."
    exit 1
fi

if [ ! -f "$SERVICE_ACCOUNT_KEY" ]; then
    echo "Error: Firebase service account key not found at '$SERVICE_ACCOUNT_KEY'."
    exit 1
fi

if [ -z "$NOTION_API_TOKEN" ] || [ -z "$NOTION_DATABASE_ID" ]; then
    echo "Error: NOTION_API_TOKEN or NOTION_DATABASE_ID environment variables are not set."
    exit 1
fi

check_command "python" "Please ensure Python 3.9+ is installed and in your PATH."
check_command "firebase" "Please ensure Firebase CLI is installed ('npm install -g firebase-tools')."

echo "All checks passed."

# --- Test Execution ---

# Step 1: Embed and Upsert
print_step "1/5 - Upserting sample transcript to ChromaDB"
python scripts/embed_and_upsert.py --input "$SAMPLE_TRANSCRIPT"
echo "Upsert successful."

# Step 2: Verify Search
print_step "2/5 - Verifying search functionality"
# We just check if the command runs successfully. A more advanced test could grep the output.
python scripts/verify_search.py "$SEARCH_QUERY" --top_k 1
echo "Search verification successful."

# Step 3: Sync to Firestore
print_step "3/5 - Syncing metadata to Firestore"
python scripts/sync_to_firestore.py "$SAMPLE_TRANSCRIPT" --key "$SERVICE_ACCOUNT_KEY"
echo "Firestore sync successful."

# Step 4: Sync to Notion
print_step "4/5 - Syncing metadata to Notion"
# The script will print the URL of the created page.
python scripts/sync_to_notion.py "$SAMPLE_TRANSCRIPT"
echo "Notion sync successful."

# Step 5: Cleanup
print_step "5/5 - Cleaning up test data"

echo "Deleting Firestore document: meetings/$MEETING_ID"
# Note: This command requires you to be logged into firebase CLI (`firebase login`)
# and have the correct project selected (`firebase use <project_id>`).
firebase firestore:delete "meetings/$MEETING_ID" --yes
echo "Firestore cleanup successful."

echo
echo "NOTE: A sample page was created in your Notion database. Please delete it manually."
echo

# --- Final Result ---
echo "-------------------------------------------------"
echo "✅ E2E TEST SUCCEEDED"
echo "-------------------------------------------------"
