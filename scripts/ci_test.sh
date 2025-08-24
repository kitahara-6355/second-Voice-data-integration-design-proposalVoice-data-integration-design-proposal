#!/bin/bash
#
# Description: Runs a CI-friendly test of the local data pipeline.
#
# This test is a subset of the full E2E test and covers components
# that do not require external secrets or authentication.
#   1. Creates its own sample data.
#   2. Upserts the sample transcript to a local ChromaDB.
#   3. Verifying that the local search functionality works.

set -e # Exit immediately if a command exits with a non-zero status.

# --- Test Configuration ---
SAMPLE_DIR="local_data/transcripts"
SAMPLE_TRANSCRIPT="$SAMPLE_DIR/sample_meeting_for_test.json"
SEARCH_QUERY="search functionality"

# --- Helper Functions ---
print_step() {
    echo
    echo "================================================="
    echo "STEP: $1"
    echo "================================================="
}

# --- Test Execution ---

# Step 1: Set up test environment and create sample data
print_step "1/3 - Setting up test environment and creating sample data"
mkdir -p "$SAMPLE_DIR"
cat <<EOF > "$SAMPLE_TRANSCRIPT"
{
  "meeting_id": "sample_meeting_for_test",
  "title": "E2E Test Meeting",
  "date": "2024-08-23T10:00:00Z",
  "summary": "This is a sample meeting to test the end-to-end data pipeline.",
  "tags": ["test", "sample"],
  "segments": [
    {
      "start": "00:00:01.000",
      "end": "00:00:05.000",
      "text": "Hello everyone, this is a test of the data processing system."
    },
    {
      "start": "00:00:06.000",
      "end": "00:00:10.000",
      "text": "We need to verify that the search functionality works correctly."
    },
    {
      "start": "00:00:11.000",
      "end": "00:00:15.000",
      "text": "The final step is ensuring cloud synchronization with Firestore and Notion."
    }
  ]
}
EOF
echo "Sample transcript created at $SAMPLE_TRANSCRIPT"


# Step 2: Embed and Upsert
print_step "2/3 - Upserting sample transcript to ChromaDB"
python scripts/embed_and_upsert.py --input "$SAMPLE_TRANSCRIPT"
echo "Upsert successful."

# Step 3: Verify Search
print_step "3/3 - Verifying local search functionality"
# We check that the search script runs and finds a result for a relevant query.
# The `grep` command ensures that the output contains the expected document text.
# The `-q` flag makes grep quiet, it just sets the exit code.
if python scripts/verify_search.py "$SEARCH_QUERY" --top_k 1 | grep -q "We need to verify that the search functionality works correctly."; then
    echo "Search verification successful: Found expected text in search results."
else
    echo "Error: Search verification failed. Did not find expected text in search results."
    exit 1
fi

# --- Final Result ---
echo
echo "-------------------------------------------------"
echo "✅ CI TEST SUCCEEDED"
echo "-------------------------------------------------"
