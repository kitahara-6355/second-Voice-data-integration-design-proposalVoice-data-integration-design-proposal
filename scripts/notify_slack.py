import argparse
import os
import sys
import json

try:
    import requests
except ImportError:
    print("Error: 'requests' library not found. Please run 'pip install -r scripts/requirements.txt'", file=sys.stderr)
    sys.exit(1)

def send_slack_notification(message: str, webhook_url: str):
    """
    Sends a formatted notification to a Slack webhook URL.
    """
    try:
        payload = {
            "blocks": [
                {"type": "header", "text": {"type": "plain_text", "text": "🚨 Pipeline Alert", "emoji": True}},
                {"type": "section", "text": {"type": "mrkdwn", "text": message}}
            ]
        }
        response = requests.post(webhook_url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        print("Successfully sent notification to Slack.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending notification to Slack: {e}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)

def main():
    """
    Main function to parse arguments and send notification.
    """
    parser = argparse.ArgumentParser(description="Send a notification message to a Slack channel.")
    parser.add_argument("message", type=str, help="The message to be sent. Supports Slack's mrkdwn.")
    args = parser.parse_args()

    webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    if not webhook_url:
        print("Warning: SLACK_WEBHOOK_URL environment variable is not set. Cannot send notification.", file=sys.stderr)
        sys.exit(0)

    if not args.message:
        print("Warning: No message provided. Nothing to send.", file=sys.stderr)
        sys.exit(0)

    send_slack_notification(args.message, webhook_url)
    sys.exit(0) # Explicitly exit with success code

if __name__ == "__main__":
    main()
