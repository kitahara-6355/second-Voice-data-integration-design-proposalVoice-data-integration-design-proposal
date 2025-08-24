<#
.SYNOPSIS
    Transcribes an audio file using whisper.cpp and outputs a structured JSON file.

.DESCRIPTION
    This script requires a compiled whisper.cpp executable. It takes an audio file as input,
    transcribes it, and formats the output into a JSON file with a meeting_id and segments.

.PARAMETER InputFile
    (Required) The path to the audio file (e.g., WAV, MP3) to be transcribed.

.EXAMPLE
    .\scripts\transcribe_whisper.ps1 -InputFile "C:\path\to\your\audio.wav"

.NOTES
    Dependencies:
    - whisper.cpp: Must be compiled. https://github.com/ggerganov/whisper.cpp
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$InputFile
)

# --- Configuration ---
# Adjust these paths based on your whisper.cpp installation location.
# Assumes whisper.cpp is cloned in the same parent directory as this project.
$whisperCppDir = "..\whisper.cpp"
$whisperExecutable = Join-Path -Path $whisperCppDir -ChildPath "main.exe"
# Recommend starting with a base model. Change as needed.
$modelPath = Join-Path -Path $whisperCppDir -ChildPath "models\ggml-base.en.bin"

# Output directory for final transcripts
$transcriptsDir = "local_data\transcripts"
# --- End Configuration ---

# --- Pre-flight Checks ---
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$projectRoot = (Resolve-Path (Join-Path -Path $scriptDir -ChildPath "..")).Path

$whisperExecutable = Join-Path -Path $projectRoot -ChildPath $whisperExecutable
$modelPath = Join-Path -Path $projectRoot -ChildPath $modelPath
$transcriptsDir = Join-Path -Path $projectRoot -ChildPath $transcriptsDir

if (-not (Test-Path -Path $whisperExecutable -PathType Leaf)) {
    Write-Error "whisper.cpp executable not found at '$whisperExecutable'. Please check the configuration in this script."
    exit 1
}
if (-not (Test-Path -Path $modelPath -PathType Leaf)) {
    Write-Error "Model file not found at '$modelPath'. Please download a model and/or check the configuration."
    exit 1
}
if (-not (Test-Path -Path $InputFile -PathType Leaf)) {
    Write-Error "Input file not found at '$InputFile'."
    exit 1
}

# --- Main Logic ---
$meetingId = [System.IO.Path]::GetFileNameWithoutExtension($InputFile)
$outputJsonPath = Join-Path -Path $transcriptsDir -ChildPath "${meetingId}.json"
$tempWhisperOutput = New-TemporaryFile

if (-not (Test-Path -Path $transcriptsDir -PathType Container)) {
    New-Item -ItemType Directory -Path $transcriptsDir | Out-Null
}

Write-Host "Transcribing '$InputFile'..."
Write-Host "Meeting ID: $meetingId"

# Run whisper.cpp
# Using & to execute and redirecting stdout to the temp file.
& $whisperExecutable -m $modelPath -f $InputFile -oj -l auto | Out-File -FilePath $tempWhisperOutput.FullName -Encoding utf8

Write-Host "Transcription complete. Formatting JSON output..."

# Read and parse the temporary JSON output
$whisperContent = Get-Content -Path $tempWhisperOutput.FullName -Raw
try {
    $whisperData = $whisperContent | ConvertFrom-Json
}
catch {
    Write-Error "whisper.cpp did not produce valid JSON. Raw output:"
    Write-Error $whisperContent
    Remove-Item -Path $tempWhisperOutput.FullName
    exit 1
}


# Create the final structured object
$finalSegments = @()
foreach ($segment in $whisperData.transcription) {
    $finalSegments += [PSCustomObject]@{
        start = $segment.timestamps.from
        end   = $segment.timestamps.to
        text  = $segment.text.TrimStart()
    }
}

$finalObject = [PSCustomObject]@{
    meeting_id = $meetingId
    segments   = $finalSegments
}

# Convert the final object to JSON and save it
$finalObject | ConvertTo-Json -Depth 5 | Set-Content -Path $outputJsonPath -Encoding utf8

# Clean up the temporary file
Remove-Item -Path $tempWhisperOutput.FullName

Write-Host "Successfully created transcript at '$outputJsonPath'"
