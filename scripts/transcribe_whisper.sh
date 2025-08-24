#!/bin/bash
#
# Description: Transcribes an audio file using whisper.cpp and outputs a structured JSON file.
# Usage: ./scripts/transcribe_whisper.sh <path_to_audio_file>
#
# Dependencies:
#   - whisper.cpp: Must be compiled. https://github.com/ggerganov/whisper.cpp
#   - jq: A command-line JSON processor. (e.g., `sudo apt-get install jq`)

set -e

# --- Configuration ---
# Adjust these paths based on your whisper.cpp installation location.
# Assumes whisper.cpp is cloned in the same parent directory as this project.
WHISPER_CPP_DIR="../whisper.cpp"
WHISPER_EXECUTABLE="${WHISPER_CPP_DIR}/main"
# Recommend starting with a base model. Change as needed.
MODEL_PATH="${WHISPER_CPP_DIR}/models/ggml-base.en.bin"

# Output directory for final transcripts
TRANSCRIPTS_DIR="local_data/transcripts"
# --- End Configuration ---

# --- Input Validation ---
if ! command -v jq &> /dev/null; then
    echo "Error: jq is not installed. Please install it (e.g., 'sudo apt-get install jq')." >&2
    exit 1
fi

if [ ! -f "$WHISPER_EXECUTABLE" ]; then
    echo "Error: whisper.cpp executable not found at '$WHISPER_EXECUTABLE'." >&2
    echo "Please check the WHISPER_CPP_DIR configuration in this script." >&2
    exit 1
fi

if [ ! -f "$MODEL_PATH" ]; then
    echo "Error: Model file not found at '$MODEL_PATH'." >&2
    echo "Please download a model and/or check the MODEL_PATH configuration." >&2
    exit 1
fi

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path_to_audio_file>" >&2
    exit 1
fi

INPUT_FILE="$1"
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file not found at '$INPUT_FILE'." >&2
    exit 1
fi

# --- Main Logic ---
MEETING_ID=$(basename "$INPUT_FILE" | cut -f 1 -d '.')
OUTPUT_JSON_PATH="${TRANSCRIPTS_DIR}/${MEETING_ID}.json"
TEMP_WHISPER_OUTPUT=$(mktemp)

mkdir -p "$TRANSCRIPTS_DIR"

echo "Transcribing '$INPUT_FILE'..."
echo "Meeting ID: $MEETING_ID"

# Run whisper.cpp
# -m: model path
# -f: input file path
# -oj: output in JSON format
# -l auto: auto-detect language
"$WHISPER_EXECUTABLE" -m "$MODEL_PATH" -f "$INPUT_FILE" -oj -l auto > "$TEMP_WHISPER_OUTPUT"

echo "Transcription complete. Formatting JSON output..."

# Check if whisper output is valid JSON
if ! jq . "$TEMP_WHISPER_OUTPUT" >/dev/null 2>&1; then
    echo "Error: whisper.cpp did not produce valid JSON. Raw output:" >&2
    cat "$TEMP_WHISPER_OUTPUT" >&2
    rm "$TEMP_WHISPER_OUTPUT"
    exit 1
fi

# Use jq to transform the whisper.cpp JSON to the desired format.
# whisper.cpp format: { "transcription": [ { "timestamps": {"from": "...", "to": "..."}, "text": "..." } ] }
# Desired format: { "meeting_id": "...", "segments": [ { "start": "...", "end": "...", "text": "..." } ] }
jq -n --arg meeting_id "$MEETING_ID" --slurpfile whisper "$TEMP_WHISPER_OUTPUT" '
{
  "meeting_id": $meeting_id,
  "segments": $whisper[0].transcription | map({
    "start": .timestamps.from,
    "end": .timestamps.to,
    "text": .text | ltrimstr(" ")
  })
}
' > "$OUTPUT_JSON_PATH"

# Clean up the temporary file
rm "$TEMP_WHISPER_OUTPUT"

echo "Successfully created transcript at '$OUTPUT_JSON_PATH'"
