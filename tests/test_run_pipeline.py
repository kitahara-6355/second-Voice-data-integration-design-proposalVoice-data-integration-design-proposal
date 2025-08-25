import pytest
from unittest.mock import patch, MagicMock

from scripts import run_pipeline

@patch('scripts.run_pipeline.find_new_files', return_value=set())
def test_no_new_files(mock_find_files):
    """
    Tests that the script exits gracefully when no new files are found.
    """
    with pytest.raises(SystemExit) as e:
        run_pipeline.main(sync_first=False)

    mock_find_files.assert_called_once()
    assert e.value.code == 0

@patch('scripts.run_pipeline.run_command', return_value=(True, None))
@patch('scripts.run_pipeline.find_new_files', return_value={'new_meeting_file'})
@patch('pathlib.Path.glob', return_value=iter([MagicMock(name='found_audio_file')]))
def test_one_new_file_processing(mock_glob, mock_find_files, mock_run_command):
    """
    Tests that the pipeline steps are called for a single new file.
    """
    run_pipeline.main(sync_first=False)

    mock_find_files.assert_called_once()

    # Expect 4 processing steps to be called for the one file
    assert mock_run_command.call_count == 4

    # Check that the first call is to the 'transcribe' script
    first_call_args = mock_run_command.call_args_list[0].args[0]
    assert 'transcribe_whisper' in first_call_args[0]

    # Check that the last call is to the 'notion' script
    last_call_args = mock_run_command.call_args_list[3].args[0]
    assert 'sync_to_notion.py' in last_call_args[1]

@patch('scripts.run_pipeline.run_command')
@patch('scripts.run_pipeline.find_new_files', return_value={'file1', 'file2'})
@patch('pathlib.Path.glob')
def test_multiple_new_files_processing(mock_glob, mock_find_files, mock_run_command):
    """
    Tests that the pipeline steps are called for multiple new files.
    """
    # Make the glob mock return a specific mock file for each expected call
    def glob_side_effect(pattern):
        if pattern == "file1.*":
            return iter([MagicMock(name='file1.m4a')])
        if pattern == "file2.*":
            return iter([MagicMock(name='file2.m4a')])
        return iter([])

    mock_glob.side_effect = glob_side_effect

    # Mock run_command to always succeed
    mock_run_command.return_value = (True, None)

    # The script will exit with 1 if any files fail, so we don't expect an exit here.
    run_pipeline.main(sync_first=False)

    mock_find_files.assert_called_once()

    # Expect 4 steps for each of the 2 files = 8 total calls
    assert mock_run_command.call_count == 8

@patch('scripts.run_pipeline.run_command')
@patch('scripts.run_pipeline.find_new_files', return_value={'file1'})
@patch('pathlib.Path.glob', return_value=iter([MagicMock(name='found_audio_file')]))
def test_pipeline_stops_for_failed_step(mock_glob, mock_find_files, mock_run_command):
    """
    Tests that if one step fails, subsequent steps for that file are not run.
    """
    # Simulate failure on the first step (transcription)
    mock_run_command.side_effect = [
        (False, MagicMock()), # Fail transcribe
        # The other calls should not happen
        (True, None),
        (True, None),
        (True, None),
    ]

    with pytest.raises(SystemExit) as e:
        run_pipeline.main(sync_first=False)

    # The pipeline should exit with 1 due to the failure log
    assert e.value.code == 1

    # Assert that run_command was only called once (for the failing step)
    mock_run_command.assert_called_once()
