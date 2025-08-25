import pytest
from unittest.mock import patch, MagicMock
import json

from scripts import notify_slack

@patch('scripts.notify_slack.requests.post')
def test_send_slack_notification_formatting(mock_post):
    """
    Tests that the send_slack_notification function calls requests.post
    with a correctly formatted Block Kit payload.
    """
    test_url = "https://fake.slack.webhook.url"
    test_message = "This is a test message."

    # Call the function to be tested
    notify_slack.send_slack_notification(test_message, test_url)

    # Assert that requests.post was called once
    mock_post.assert_called_once()

    # Get the arguments passed to requests.post
    args, kwargs = mock_post.call_args

    # Check the URL
    assert args[0] == test_url

    # Check the headers
    assert 'headers' in kwargs
    assert kwargs['headers']['Content-Type'] == 'application/json'

    # Check the payload data
    assert 'data' in kwargs
    payload = json.loads(kwargs['data'])

    # Verify the structure of the Slack Block Kit payload
    assert 'blocks' in payload
    assert len(payload['blocks']) == 2
    assert payload['blocks'][0]['type'] == 'header'
    assert payload['blocks'][0]['text']['text'] == "🚨 Pipeline Alert"
    assert payload['blocks'][1]['type'] == 'section'
    assert payload['blocks'][1]['text']['text'] == test_message

@patch('scripts.notify_slack.send_slack_notification')
@patch('scripts.notify_slack.os.getenv')
def test_main_function_with_env_var(mock_getenv, mock_send_notification):
    """
    Tests the main guard (__name__ == "__main__") logic to ensure it
    calls the sender function when the webhook URL is set.
    """
    # Mock os.getenv to return a fake URL
    mock_getenv.return_value = "https://fake.slack.webhook.url"

    test_message = "Test message from main"

    # Mock sys.argv to simulate command-line arguments
    with patch('sys.argv', ['notify_slack.py', test_message]):
        # The script calls sys.exit on success, so we expect a SystemExit
        with pytest.raises(SystemExit) as e:
            notify_slack.main()
        assert e.value.code == 0

    # Assert that our sender function was called with the correct message
    mock_send_notification.assert_called_once_with(test_message, "https://fake.slack.webhook.url")

@patch('scripts.notify_slack.send_slack_notification')
@patch('scripts.notify_slack.os.getenv')
def test_main_function_without_env_var(mock_getenv, mock_send_notification):
    """
    Tests that the main guard does NOT call the sender function
    if the webhook URL environment variable is not set.
    """
    # Mock os.getenv to return None
    mock_getenv.return_value = None

    with patch('sys.argv', ['notify_slack.py', "some message"]):
        # The script should print a warning and exit gracefully (code 0)
        with pytest.raises(SystemExit) as e:
            notify_slack.main()

    assert e.type == SystemExit
    assert e.value.code == 0

    # Assert that the sender function was never called
    mock_send_notification.assert_not_called()

# Helper main function added to notify_slack.py to make it more testable
# This is a common pattern: wrap the main logic in a function.
# I will now modify notify_slack.py to incorporate this.
# Let's assume notify_slack.py is changed to have:
# def main():
#     # parser logic...
#     send_slack_notification(args.message, webhook_url)
#
# if __name__ == "__main__":
#     main()
# This makes the main logic callable for tests.
# The tests above are written with this assumption. I need to go and refactor notify_slack.py next.
# For now, this test file is complete based on that assumption.

# Let's refactor the test to not require a change to the source file for now.
# We can test the __main__ block by importing the module.
def run_module_main(monkeypatch, *argv):
    """Helper to run a module's __main__ block."""
    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["<script_name>", *argv])
        # A bit of a hack: runpy can execute a module's code as __main__
        import runpy
        runpy.run_module("scripts.notify_slack", run_name="__main__")

@patch('scripts.notify_slack.requests.post')
@patch('scripts.notify_slack.os.getenv')
def test_main_block_with_env_var(mock_getenv, mock_post, monkeypatch):
    """
    A more robust test of the __main__ block without refactoring the source.
    """
    mock_getenv.return_value = "https://fake.slack.webhook.url"

    with pytest.raises(SystemExit): # The script calls sys.exit(0) on success
        run_module_main(monkeypatch, "a test message")

    mock_post.assert_called_once()
    args, _ = mock_post.call_args
    assert args[0] == "https://fake.slack.webhook.url"

# The previous tests are actually better if I refactor the source.
# I will stick with the first set of tests and refactor notify_slack.py
# The test file itself is correct under this assumption.
# I will remove the less good tests.
del run_module_main
del test_main_block_with_env_var
