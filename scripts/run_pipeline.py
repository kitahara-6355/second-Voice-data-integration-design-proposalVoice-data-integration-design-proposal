import argparse
import subprocess
from pathlib import Path
import sys

# --- Configuration ---
RECORDINGS_DIR = Path("local_data/recordings")
TRANSCRIPTS_DIR = Path("local_data/transcripts")
SCRIPTS_DIR = Path("scripts")
AUDIO_EXTENSIONS = [".m4a", ".mp3", ".wav", ".aac"]

def notify_slack(message: str):
    """Helper function to call the Slack notification script."""
    print("  > Sending failure notification to Slack...")
    notifier_script = str(SCRIPTS_DIR / "notify_slack.py")
    subprocess.run([sys.executable, notifier_script, message], text=True)

def run_command(command: list[str]):
    """Runs a command as a subprocess and checks for errors."""
    command_str = ' '.join(command)
    print(f"  > Running: {command_str}")
    try:
        if command[0] == 'python':
            command[0] = sys.executable
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        return True, result
    except subprocess.CalledProcessError as e:
        print(f"\n--- ERROR ---", file=sys.stderr)
        error_message = (
            f"*Pipeline Step Failed*\n"
            f"```\nCommand: {command_str}\nExit Code: {e.returncode}\n"
            f"--- Stderr ---\n{e.stderr or 'No stderr.'}\n```"
        )
        notify_slack(error_message)
        return False, e

def find_new_files():
    """Compares recordings and transcripts directories to find new files."""
    if not RECORDINGS_DIR.exists():
        print(f"⚠️ Recordings directory not found at '{RECORDINGS_DIR}'. Please create it or sync from Drive first.")
        return None
    TRANSCRIPTS_DIR.mkdir(exist_ok=True)
    existing_recordings = {p.stem for p in RECORDINGS_DIR.glob("*") if p.suffix in AUDIO_EXTENSIONS}
    processed_transcripts = {p.stem for p in TRANSCRIPTS_DIR.glob("*.json")}
    return existing_recordings - processed_transcripts

def main(sync_first: bool):
    """Main function to orchestrate the data processing pipeline."""
    print("🚀 Starting the Pixel Recordings Analytics Pipeline")
    print("-" * 50)

    if sync_first:
        print("STEP 1: Syncing new recordings from Google Drive...")
        sync_script = str(SCRIPTS_DIR / ("sync_drive.ps1" if sys.platform == "win32" else "sync_drive.sh"))
        success, _ = run_command([sync_script])
        if not success:
            print("❌ Halting pipeline due to sync failure.", file=sys.stderr)
            sys.exit(1)
        print("✅ Sync complete.")
        print("-" * 50)

    print("STEP 2: Finding new recordings to process...")
    new_files_to_process = find_new_files()

    if new_files_to_process is None or not new_files_to_process:
        print("✅ No new recordings to process. All up to date!")
        sys.exit(0)

    print(f"🔥 Found {len(new_files_to_process)} new recording(s): {', '.join(new_files_to_process)}")
    print("-" * 50)

    print(f"STEP 3: Processing {len(new_files_to_process)} file(s)...")
    success_log, failure_log = [], []

    for filename_stem in new_files_to_process:
        print(f"\n▶️ Processing: {filename_stem}")
        audio_file = next(RECORDINGS_DIR.glob(f"{filename_stem}.*"), None)
        if not audio_file:
            print(f"  - ❌ Could not find audio file for {filename_stem}. Skipping.", file=sys.stderr)
            failure_log.append((filename_stem, "Audio file not found"))
            continue

        transcript_json_path = TRANSCRIPTS_DIR / f"{filename_stem}.json"
        pipeline_steps = [
            ("Transcribe", [str(SCRIPTS_DIR / ("transcribe_whisper.ps1" if sys.platform == "win32" else "transcribe_whisper.sh")), str(audio_file)]),
            ("Embed & Upsert", ["python", str(SCRIPTS_DIR / "embed_and_upsert.py"), "--input", str(transcript_json_path)]),
            ("Sync to Firestore", ["python", str(SCRIPTS_DIR / "sync_to_firestore.py"), str(transcript_json_path)]),
            ("Sync to Notion", ["python", str(SCRIPTS_DIR / "sync_to_notion.py"), str(transcript_json_path)]),
        ]

        file_failed = False
        for name, command in pipeline_steps:
            print(f"  - Running step: {name}")
            success, _ = run_command(command)
            if not success:
                print(f"  - ❌ Step '{name}' failed for {filename_stem}. Halting processing for this file.", file=sys.stderr)
                failure_log.append((filename_stem, f"Failed at step: {name}"))
                file_failed = True
                break

        if not file_failed:
            print(f"  - ✅ Successfully processed {filename_stem}!")
            success_log.append(filename_stem)

    print("\n" + "-" * 50)
    print("🏁 Pipeline run finished.")
    print(f"✅ Successfully processed: {len(success_log)} file(s): {', '.join(success_log)}")

    if failure_log:
        print(f"❌ Failed to process: {len(failure_log)} file(s)")
        for filename, reason in failure_log:
            print(f"  - {filename} ({reason})", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated pipeline to process new Pixel recordings.")
    parser.add_argument("--sync-first", action="store_true", help="Run rclone sync from Google Drive before processing.")
    args = parser.parse_args()
    main(args.sync_first)
