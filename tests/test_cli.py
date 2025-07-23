import os
from unittest.mock import patch

from structlog.testing import capture_logs

from schemachange.cli import main
from schemachange.config.base import SubCommand
from schemachange.session.mysql_session import MySQLSession
from tests.conftest import TEST_DIR, mock_structlog_logger


@patch(
    "sys.argv",
    [
        "script_name.py",
        SubCommand.RENDER,
        "--script-path",
        "tests/resource/render_script.sql",
    ],
)
def test_render():
    os.environ["TEST_ENV_VAR"] = "data"
    with mock_structlog_logger() as _:
        with capture_logs() as cap_logs:
            main()

        render_log = [
            item
            for item in cap_logs
            if item["event"] == "Success" and item["log_level"] == "info"
        ]
        assert len(render_log) > 0
        assert render_log[0]["content"] == "SELECT data"
        assert (
            render_log[0]["checksum"]
            == "1424ebf029da1157d94a236c23bb527381a2a98a5b455091349501a9"
        )


@patch(
    "sys.argv",
    [
        "script_name.py",
        SubCommand.DEPLOY,
        "--config-folder",
        str(TEST_DIR / "resource"),
        "--config-file-name",
        "valid_config_file.yml",
        "--root-folder",
        "tests/resource/scripts/",
    ],
)
@patch.object(MySQLSession, "_connect")
@patch.object(MySQLSession, "reset_session")
@patch.object(MySQLSession, "reset_query_tag")
@patch.object(MySQLSession, "set_autocommit")
@patch.object(MySQLSession, "get_executed_query_data")
@patch.object(MySQLSession, "_commit")
@patch.object(MySQLSession, "_rollback")
@patch("mysql.connector.connection.MySQLCursor.execute")
@patch.object(MySQLSession, "cursor")
def test_deploy(
    mock__connect,
    mock_reset_session,
    mock_reset_query_tag,
    mock_set_autocommit,
    mock_get_executed_query_data,
    mock__commit,
    mock__rollback,
    mock_execute,
    mock_cursor,
):
    with mock_structlog_logger() as _:
        with capture_logs() as cap_logs:
            main()

        deploy_log = [
            item
            for item in cap_logs
            if item["event"] == "Completed successfully" and item["log_level"] == "info"
        ]
        assert len(deploy_log) > 0
        assert deploy_log[0]["scripts_applied"] == "3"
        assert deploy_log[0]["scripts_skipped"] == "0"
