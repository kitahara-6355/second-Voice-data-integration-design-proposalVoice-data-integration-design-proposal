#!/bin/bash
#
# Description: This script syncs a Google Drive folder to a local directory using rclone.
# Usage: ./scripts/sync_drive.sh
#
# It assumes you have a configured rclone remote named 'gdrive'.
# Refer to docs/rclone_setup.md for setup instructions.

set -e

# --- Configuration ---
# The remote path on Google Drive. Change this if your folder is named differently.
REMOTE_PATH="gdrive:PixelRecordings"

# The local directory to sync to. The script assumes it's run from the project root.
LOCAL_PATH_RELATIVE="local_data/recordings"
# --- End Configuration ---

# Get the directory of the script to robustly find the project root
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_ROOT=$(realpath "$SCRIPT_DIR/..")
LOCAL_PATH_ABSOLUTE="$PROJECT_ROOT/$LOCAL_PATH_RELATIVE"

# Create the local directory if it doesn't exist.
mkdir -p "$LOCAL_PATH_ABSOLUTE"

echo "================================================="
echo "Starting rclone sync"
echo "From (Remote): $REMOTE_PATH"
echo "To (Local):    $LOCAL_PATH_ABSOLUTE"
echo "================================================="

# Run rclone sync command.
# --drive-use-trash=false: Permanently delete files from destination if they are removed from source.
# --transfers=4: Number of files to transfer in parallel.
# -P / --progress: Show progress during transfer.
rclone sync "$REMOTE_PATH" "$LOCAL_PATH_ABSOLUTE" --drive-use-trash=false --transfers=4 -P

echo
echo "Sync complete."
echo "Local files are in: $LOCAL_PATH_ABSOLUTE"
