import dataclasses
from unittest.mock import patch

import pytest

from schemachange.config.change_history_table import ChangeHistoryTable


@patch("schemachange.common.utils.get_identifier_string")
def test_change_history_table_init(mock_get_identifier):
    # Test that the class initializes with default values
    mock_get_identifier.side_effect = lambda input_value, input_type: input_value

    table = ChangeHistoryTable()

    assert table.table_name == "CHANGE_HISTORY"
    assert table.schema_name == "SCHEMACHANGE"
    assert table.database_name == "METADATA"


def test_change_history_table_fully_qualified_with_schema():
    # Test the fully_qualified property with schema
    table = ChangeHistoryTable(
        table_name="TEST_TABLE", schema_name="TEST_SCHEMA", database_name="TEST_DB"
    )

    assert table.fully_qualified == "TEST_DB.TEST_SCHEMA.TEST_TABLE"


def test_change_history_table_fully_qualified_without_schema():
    # Test the fully_qualified property without schema
    table = ChangeHistoryTable(
        table_name="TEST_TABLE", schema_name="", database_name="TEST_DB"
    )

    assert table.fully_qualified == "TEST_DB.TEST_TABLE"


@patch("schemachange.common.utils.get_identifier_string")
def test_from_str_default_values_with_schema(mock_get_identifier):
    # Test from_str with None input and include_schema=True
    mock_get_identifier.side_effect = lambda input_value, input_type: input_value

    table = ChangeHistoryTable.from_str(None, include_schema=True)

    assert table.table_name == "CHANGE_HISTORY"
    assert table.schema_name == "SCHEMACHANGE"
    assert table.database_name == "METADATA"


@patch("schemachange.common.utils.get_identifier_string")
def test_from_str_default_values_without_schema(mock_get_identifier):
    # Test from_str with None input and include_schema=False
    mock_get_identifier.side_effect = lambda input_value, input_type: input_value

    table = ChangeHistoryTable.from_str(None, include_schema=False)

    assert table.table_name == "CHANGE_HISTORY"
    assert table.schema_name is None
    assert table.database_name == "METADATA"


@patch("schemachange.common.utils.get_identifier_string")
def test_from_str_one_part_with_schema(mock_get_identifier):
    # Test from_str with one-part name and include_schema=True
    mock_get_identifier.side_effect = lambda input_value, input_type: input_value

    table = ChangeHistoryTable.from_str("CUSTOM_TABLE", include_schema=True)

    assert table.table_name == "CUSTOM_TABLE"
    assert table.schema_name == "SCHEMACHANGE"
    assert table.database_name == "METADATA"


@patch("schemachange.common.utils.get_identifier_string")
def test_from_str_one_part_without_schema(mock_get_identifier):
    # Test from_str with one-part name and include_schema=False
    mock_get_identifier.side_effect = lambda input_value, input_type: input_value

    table = ChangeHistoryTable.from_str("CUSTOM_TABLE", include_schema=False)

    assert table.table_name == "CUSTOM_TABLE"
    assert table.schema_name is None
    assert table.database_name == "METADATA"


@patch("schemachange.common.utils.get_identifier_string")
def test_from_str_two_parts_with_schema(mock_get_identifier):
    # Test from_str with two-part name and include_schema=True
    mock_get_identifier.side_effect = lambda input_value, input_type: input_value

    table = ChangeHistoryTable.from_str(
        "CUSTOM_SCHEMA.CUSTOM_TABLE", include_schema=True
    )

    assert table.table_name == "CUSTOM_TABLE"
    assert table.schema_name == "CUSTOM_SCHEMA"
    assert table.database_name == "METADATA"


@patch("schemachange.common.utils.get_identifier_string")
def test_from_str_two_parts_without_schema(mock_get_identifier):
    # Test from_str with two-part name and include_schema=False
    mock_get_identifier.side_effect = lambda input_value, input_type: input_value

    table = ChangeHistoryTable.from_str("CUSTOM_DB.CUSTOM_TABLE", include_schema=False)

    assert table.table_name == "CUSTOM_TABLE"
    assert table.schema_name is None
    assert table.database_name == "CUSTOM_DB"


@patch("schemachange.common.utils.get_identifier_string")
def test_from_str_three_parts_with_schema(mock_get_identifier):
    # Test from_str with three-part name and include_schema=True
    mock_get_identifier.side_effect = lambda input_value, input_type: input_value

    table = ChangeHistoryTable.from_str(
        "CUSTOM_DB.CUSTOM_SCHEMA.CUSTOM_TABLE", include_schema=True
    )

    assert table.table_name == "CUSTOM_TABLE"
    assert table.schema_name == "CUSTOM_SCHEMA"
    assert table.database_name == "CUSTOM_DB"


@patch("schemachange.common.utils.get_identifier_string")
def test_from_str_three_parts_without_schema_raises_error(mock_get_identifier):
    # Test from_str with three-part name and include_schema=False (should raise ValueError)
    mock_get_identifier.side_effect = lambda input_value, input_type: input_value

    with pytest.raises(ValueError) as excinfo:
        ChangeHistoryTable.from_str(
            "CUSTOM_DB.CUSTOM_SCHEMA.CUSTOM_TABLE", include_schema=False
        )

    assert "Invalid change history table name" in str(excinfo.value)
    assert "expect maximum 2 parts" in str(excinfo.value)


@patch("schemachange.common.utils.get_identifier_string")
def test_from_str_four_parts_with_schema_raises_error(mock_get_identifier):
    # Test from_str with four-part name and include_schema=True (should raise ValueError)
    mock_get_identifier.side_effect = lambda input_value, input_type: input_value

    with pytest.raises(ValueError) as excinfo:
        ChangeHistoryTable.from_str("A.B.C.D", include_schema=True)

    assert "Invalid change history table name" in str(excinfo.value)


def test_change_history_table_is_frozen():
    # Test that the dataclass is frozen (immutable)
    table = ChangeHistoryTable()

    with pytest.raises(dataclasses.FrozenInstanceError):
        table.table_name = "NEW_TABLE"
