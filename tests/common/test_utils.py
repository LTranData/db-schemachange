import os
from pathlib import Path
from unittest.mock import patch

import pytest
from marshmallow import Schema, exceptions, fields

from schemachange.common.utils import (
    BaseEnum,
    get_config_secrets,
    get_connect_kwargs,
    get_identifier_string,
    get_not_none_key_value,
    load_yaml_config,
    validate_config_vars,
    validate_directory,
    validate_file_path,
)
from tests.conftest import TEST_DIR


class TestBaseEnum:
    class MyEnum(BaseEnum):
        VALUE_A = "value_a"
        VALUE_B = "value_b"

    def test_items(self):
        assert sorted(self.MyEnum.items()) == sorted(["value_a", "value_b"])

    def test_validate_value_valid(self):
        self.MyEnum.validate_value("test_attr", "value_a")

    def test_validate_value_invalid(self):
        with pytest.raises(ValueError) as excinfo:
            self.MyEnum.validate_value("test_attr", "invalid_value")
        assert (
            "Invalid value 'test_attr', should be one of ['value_a', 'value_b'], actual 'invalid_value'"
            in str(excinfo.value)
        )


def test_get_not_none_key_value():
    assert get_not_none_key_value({"a": 1, "b": None, "c": 3}) == {"a": 1, "c": 3}
    assert get_not_none_key_value({"a": 1, "b": 2}) == {"a": 1, "b": 2}
    assert get_not_none_key_value({}) == {}
    assert get_not_none_key_value({"a": None}) == {}


def test_get_identifier_string_valid():
    assert (
        get_identifier_string("my_identifier_123", "column_name") == "my_identifier_123"
    )
    assert get_identifier_string("ANOTHER_ID", "table_name") == "ANOTHER_ID"
    assert get_identifier_string("id", "id_field") == "id"


def test_get_identifier_string_none():
    assert get_identifier_string(None, "column_name") is None


def test_get_identifier_string_invalid():
    with pytest.raises(ValueError) as excinfo:
        get_identifier_string("invalid id", "column_name")
    assert (
        "Invalid column_name: invalid id. Should contain alphanumeric characters and underscores only"
        in str(excinfo.value)
    )

    with pytest.raises(ValueError) as excinfo:
        get_identifier_string("invalid-id", "column_name")
    assert (
        "Invalid column_name: invalid-id. Should contain alphanumeric characters and underscores only"
        in str(excinfo.value)
    )

    with pytest.raises(ValueError) as excinfo:
        get_identifier_string("invalid!", "column_name")
    assert (
        "Invalid column_name: invalid!. Should contain alphanumeric characters and underscores only"
        in str(excinfo.value)
    )

    with pytest.raises(ValueError) as excinfo:
        get_identifier_string("", "column_name")
    assert (
        "Invalid column_name: . Should contain alphanumeric characters and underscores only"
        in str(excinfo.value)
    )


def test_get_config_secrets_simple():
    config_vars = {
        "user": "test_user",
        "password_SECRET": "my_secret_password",
        "api_key": "some_key",
    }
    assert get_config_secrets(config_vars) == {"my_secret_password"}


def test_get_config_secrets_nested_secrets_key():
    config_vars = {
        "db": {
            "host": "localhost",
            "secrets": {
                "db_password": "db_secret_value",
                "another_secret": "another_secret_value ",
            },
        },
        "app_key": "app_value",
    }
    assert get_config_secrets(config_vars) == {
        "db_secret_value",
        "another_secret_value",
    }


def test_get_config_secrets_mixed():
    config_vars = {
        "user": "test_user",
        "password_SECRET": "my_secret_password",
        "db": {
            "host": "localhost",
            "secrets": {
                "db_password": "db_secret_value",
            },
            "non_secret_config": "some_value",
        },
        "api_key_SECRET": "api_secret_value",
        "normal_var": "normal_value",
    }
    expected_secrets = {
        "my_secret_password",
        "db_secret_value",
        "api_secret_value",
        "some_value",
    }
    assert get_config_secrets(config_vars) == expected_secrets


def test_get_config_secrets_none_input():
    assert get_config_secrets(None) == set()


def test_get_config_secrets_empty_dict():
    assert get_config_secrets({}) == set()


def test_get_config_secrets_no_secrets():
    config_vars = {
        "user": "test_user",
        "api_key": "some_key",
        "db": {
            "host": "localhost",
            "port": 5432,
        },
    }
    assert get_config_secrets(config_vars) == set()


def test_validate_file_path_valid(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text("content")
    assert validate_file_path(p) == p
    assert validate_file_path(str(p)) == p


def test_validate_file_path_none():
    assert validate_file_path(None) is None


def test_validate_file_path_non_existent(tmp_path):
    p = tmp_path / "non_existent.txt"
    with pytest.raises(ValueError) as excinfo:
        validate_file_path(p)
    assert f"invalid file path: {str(p)}" in str(excinfo.value)


def test_validate_file_path_is_directory(tmp_path):
    d = tmp_path / "my_dir"
    d.mkdir()
    with pytest.raises(ValueError) as excinfo:
        validate_file_path(d)
    assert f"invalid file path: {str(d)}" in str(excinfo.value)


def test_validate_directory_valid(tmp_path):
    d = tmp_path / "my_dir"
    d.mkdir()
    assert validate_directory(d) == d
    assert validate_directory(str(d)) == d


def test_validate_directory_none():
    assert validate_directory(None) is None


def test_validate_directory_non_existent(tmp_path):
    d = tmp_path / "non_existent_dir"
    with pytest.raises(ValueError) as excinfo:
        validate_directory(d)
    assert f"Path is not valid directory: {str(d)}" in str(excinfo.value)


def test_validate_directory_is_file(tmp_path):
    f = tmp_path / "my_file.txt"
    f.write_text("some content")
    with pytest.raises(ValueError) as excinfo:
        validate_directory(f)
    assert f"Path is not valid directory: {str(f)}" in str(excinfo.value)


def test_validate_config_vars_valid():
    config = {"param1": "value1", "param2": 123}
    assert validate_config_vars(config) == config


def test_validate_config_vars_none():
    assert validate_config_vars(None) == {}


def test_validate_config_vars_not_dict():
    with pytest.raises(ValueError) as excinfo:
        validate_config_vars("not_a_dict")
    assert (
        "config_vars did not parse correctly, please check its configuration: not_a_dict"
        in str(excinfo.value)
    )

    with pytest.raises(ValueError) as excinfo:
        validate_config_vars(["list_item"])
    assert (
        "config_vars did not parse correctly, please check its configuration: ['list_item']"
        in str(excinfo.value)
    )


def test_validate_config_vars_reserved_key():
    config = {"param1": "value1", "schemachange": "reserved_value"}
    with pytest.raises(ValueError) as excinfo:
        validate_config_vars(config)
    assert (
        "The variable 'schemachange' has been reserved for use by schemachange, please use a different name"
        in str(excinfo.value)
    )


def test_validate_config_vars_empty_dict():
    assert validate_config_vars({}) == {}


def test_load_yaml_config():
    os.environ["TEST_ENV_VAR"] = "data"
    config_file_path = Path(f"{TEST_DIR}/resource/config_file.yml")
    assert load_yaml_config(config_file_path=config_file_path) == {
        "prop_1": "value_1",
        "prop_2": {"sub_prop_1": "sub_value_1", "sub_prop_2": "sub_value_2"},
        "prop_3": "data",
    }


@patch.object(Path, "is_file")
def test_load_yaml_config_none_path(mock_is_file):
    mock_is_file.return_value = False
    result = load_yaml_config(None)
    mock_is_file.assert_not_called()
    assert result == {}


class MockSchema(Schema):
    param1 = fields.String(required=True, allow_none=True)
    param2 = fields.Integer(required=True, allow_none=True)
    param3 = fields.String(required=False, allow_none=True)


def test_get_connect_kwargs():
    connections_info = {"param1": "value1", "param2": 123, "param3": "value3"}
    result = get_connect_kwargs(connections_info, MockSchema)
    assert result == {"param1": "value1", "param2": 123, "param3": "value3"}


def test_get_connect_kwargs_all_present():
    connections_info = {"param1": "value1", "param2": 123, "param3": None}
    result = get_connect_kwargs(connections_info, MockSchema)
    assert result == {"param1": "value1", "param2": 123}


def test_get_connect_kwargs_redundant_param():
    connections_info = {
        "param1": "value1",
        "param2": 123,
        "param3": "value3",
        "param4": "value4",
    }
    with pytest.raises(exceptions.ValidationError) as excinfo:
        get_connect_kwargs(connections_info, MockSchema)
    assert "{'param4': ['Unknown field.']}" in str(excinfo.value)
