<#
.SYNOPSIS
    Runs an end-to-end test of the data pipeline.
.DESCRIPTION
    This test covers:
    1. Upserting a sample transcript to ChromaDB.
    2. Verifying that search returns a result.
    3. Syncing metadata to Firestore.
    4. Syncing metadata to Notion.
    5. Cleaning up the created data in Firestore.
#>

# --- Script Configuration ---
# Exit on error
$ErrorActionPreference = "Stop"

# --- Test Configuration ---
$sampleTranscript = "local_data\transcripts\sample_meeting_for_test.json"
$meetingId = "sample_meeting_for_test"
$searchQuery = "search functionality"
$serviceAccountKey = "serviceAccountKey.json"

# --- Helper Functions ---
function Print-Step {
    param($title)
    Write-Host ""
    Write-Host "=================================================" -ForegroundColor Green
    Write-Host "STEP: $title" -ForegroundColor Green
    Write-Host "=================================================" -ForegroundColor Green
}

function Check-Command {
    param($command, $errorMessage)
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "Error: Required command '$command' not found. $errorMessage"
    }
}

# --- Pre-flight Checks ---
Print-Step "Performing pre-flight checks"

if (-not (Test-Path $sampleTranscript)) {
    throw "Error: Sample transcript file not found at '$sampleTranscript'."
}
if (-not (Test-Path $serviceAccountKey)) {
    throw "Error: Firebase service account key not found at '$serviceAccountKey'."
}
if ([string]::IsNullOrEmpty($env:NOTION_API_TOKEN) -or [string]::IsNullOrEmpty($env:NOTION_DATABASE_ID)) {
    throw "Error: NOTION_API_TOKEN or NOTION_DATABASE_ID environment variables are not set."
}

Check-Command "python" "Please ensure Python 3.9+ is installed and in your PATH."
Check-Command "firebase" "Please ensure Firebase CLI is installed ('npm install -g firebase-tools')."

Write-Host "All checks passed."

# --- Test Execution ---
try {
    # Step 1: Embed and Upsert
    Print-Step "1/5 - Upserting sample transcript to ChromaDB"
    python scripts\embed_and_upsert.py --input $sampleTranscript
    Write-Host "Upsert successful."

    # Step 2: Verify Search
    Print-Step "2/5 - Verifying search functionality"
    python scripts\verify_search.py -- "$searchQuery" --top_k 1
    Write-Host "Search verification successful."

    # Step 3: Sync to Firestore
    Print-Step "3/5 - Syncing metadata to Firestore"
    python scripts\sync_to_firestore.py $sampleTranscript --key $serviceAccountKey
    Write-Host "Firestore sync successful."

    # Step 4: Sync to Notion
    Print-Step "4/5 - Syncing metadata to Notion"
    python scripts\sync_to_notion.py $sampleTranscript
    Write-Host "Notion sync successful."

    # Step 5: Cleanup
    Print-Step "5/5 - Cleaning up test data"
    Write-Host "Deleting Firestore document: meetings/$meetingId"
    # Note: This command requires you to be logged into firebase CLI (`firebase login`)
    # and have the correct project selected (`firebase use <project_id>`).
    firebase firestore:delete "meetings/$meetingId" --yes
    Write-Host "Firestore cleanup successful."

    Write-Host ""
    Write-Host "NOTE: A sample page was created in your Notion database. Please delete it manually." -ForegroundColor Yellow

} catch {
    Write-Host ""
    Write-Host "-------------------------------------------------" -ForegroundColor Red
    Write-Host "❌ E2E TEST FAILED" -ForegroundColor Red
    Write-Host "Error on step: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "-------------------------------------------------"
    exit 1
}

# --- Final Result ---
Write-Host ""
Write-Host "-------------------------------------------------" -ForegroundColor Green
Write-Host "✅ E2E TEST SUCCEEDED" -ForegroundColor Green
Write-Host "-------------------------------------------------"
