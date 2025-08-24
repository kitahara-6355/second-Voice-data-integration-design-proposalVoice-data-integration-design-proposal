<#
.SYNOPSIS
    This script syncs a Google Drive folder to a local directory using rclone.

.DESCRIPTION
    It assumes you have a configured rclone remote named 'gdrive'.
    Refer to docs/rclone_setup.md for setup instructions.

.EXAMPLE
    .\scripts\sync_drive.ps1
#>

# --- Configuration ---
# The remote path on Google Drive. Change this if your folder is named differently.
$remotePath = "gdrive:PixelRecordings"

# The local directory to sync to.
$localSubPath = "local_data\recordings"
# --- End Configuration ---

# Get the project root directory based on the script's location
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$projectRoot = (Resolve-Path (Join-Path -Path $scriptDir -ChildPath "..")).Path
$localPath = Join-Path -Path $projectRoot -ChildPath $localSubPath

# Ensure the local directory exists.
if (-not (Test-Path -Path $localPath -PathType Container)) {
    Write-Host "Local directory not found. Creating it at: $localPath"
    New-Item -ItemType Directory -Path $localPath | Out-Null
}

Write-Host "================================================="
Write-Host "Starting rclone sync"
Write-Host "From (Remote): $remotePath"
Write-Host "To (Local):    $localPath"
Write-Host "================================================="

# Run rclone sync command.
# --drive-use-trash=false: Permanently delete files from destination if they are removed from source.
# --transfers=4: Number of files to transfer in parallel.
# -P / --progress: Show progress during transfer.
try {
    rclone sync $remotePath $localPath --drive-use-trash=false --transfers=4 -P
}
catch {
    Write-Error "Rclone command failed. Please ensure rclone is installed and configured correctly."
    Write-Error $_
    exit 1
}

Write-Host ""
Write-Host "Sync complete."
Write-Host "Local files are in: $localPath"
