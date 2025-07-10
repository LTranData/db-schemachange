from pathlib import PosixPath
from unittest.mock import patch

import pytest
from marshmallow import exceptions

from schemachange.config.base import SubCommand
from schemachange.config.change_history_table import ChangeHistoryTable
from schemachange.config.get_merged_config import get_merged_config
from tests.conftest import TEST_DIR, mock_structlog_logger


@patch(
    "sys.argv",
    [
        "script_name.py",
        SubCommand.DEPLOY,
        "--config-folder",
        f"{TEST_DIR}/resource",
        "--config-file-name",
        "valid_config_file.yml",
    ],
)
def test_get_merged_config():
    with mock_structlog_logger() as mock_logger:
        data = get_merged_config(logger=mock_logger)
        assert data.__dict__ == {
            "subcommand": SubCommand.DEPLOY,
            "config_file_path": PosixPath(f"{TEST_DIR}/resource/valid_config_file.yml"),
            "root_folder": PosixPath("."),
            "modules_folder": None,
            "config_vars": {
                "var1": "value1",
                "var2": "value2",
                "secrets": {"var3": "value3"},
            },
            "secrets": {"value3"},
            "log_level": 20,
            "connections_file_path": PosixPath(
                f"{TEST_DIR}/resource/connections_config_file.yml"
            ),
            "change_history_table": ChangeHistoryTable(
                table_name="CHANGE_HISTORY", schema_name=None, database_name="METADATA"
            ),
            "create_change_history_table": False,
            "autocommit": False,
            "dry_run": False,
            "db_type": "MYSQL",
            "query_tag": "TEST_QUERY_TAG",
        }


@patch(
    "sys.argv",
    [
        "script_name.py",
        SubCommand.DEPLOY,
        "--config-folder",
        f"{TEST_DIR}/resource",
        "--config-file-name",
        "invalid_config_file.yml",
    ],
)
def test_get_merged_config_invalid():
    with mock_structlog_logger() as mock_logger:
        with pytest.raises(exceptions.ValidationError) as excinfo:
            get_merged_config(logger=mock_logger)
        assert "{'invalid_property': ['Unknown field.']}" in str(excinfo.value)


@patch(
    "sys.argv",
    [
        "script_name.py",
        SubCommand.RENDER,
        "--script-path",
        "tests/resource/render_script.sql",
    ],
)
def test_get_merged_config_for_render():
    with mock_structlog_logger() as mock_logger:
        data = get_merged_config(logger=mock_logger)
        assert data.__dict__ == {
            "subcommand": SubCommand.RENDER,
            "config_file_path": PosixPath("schemachange-config.yml"),
            "root_folder": PosixPath("."),
            "modules_folder": None,
            "config_vars": {},
            "secrets": set(),
            "log_level": 20,
            "script_path": PosixPath("tests/resource/render_script.sql"),
        }
