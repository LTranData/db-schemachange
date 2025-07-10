import copy
from unittest.mock import patch

import pytest

# Import the functions to test
from schemachange.config.redact_config_secrets import (
    get_redact_config_secrets_processor,
    redact_config_secrets,
)


def test_redact_config_secrets_processor_with_string_secrets():
    # Setup
    config_secrets = {"password123", "api_key_xyz"}
    processor = get_redact_config_secrets_processor(config_secrets)

    # Test data
    event_dict = {
        "event": "login_attempt",
        "user": "test_user",
        "credentials": "password123",
        "headers": {"Authorization": "Bearer api_key_xyz"},
    }

    # Execute
    result = processor(None, "", copy.deepcopy(event_dict))

    # Assert
    assert result["event"] == "login_attempt"
    assert result["user"] == "test_user"
    assert result["credentials"] == "*" * len("password123")
    assert result["headers"]["Authorization"] == "Bearer " + "*" * len("api_key_xyz")


def test_redact_config_secrets_processor_with_integer_secrets():
    # Setup
    config_secrets = {"123", "456"}
    processor = get_redact_config_secrets_processor(config_secrets)

    # Test data
    event_dict = {"event": "transaction", "amount": 123, "reference": "payment-456-789"}

    # Execute
    result = processor(None, "", copy.deepcopy(event_dict))

    # Assert
    assert result["event"] == "transaction"
    assert str(result["amount"]) == "***"  # 123 replaced with ***
    assert result["reference"] == "payment-***-789"  # 456 replaced with ***


def test_redact_config_secrets_processor_with_nested_dict():
    # Setup
    config_secrets = {"secret_token"}
    processor = get_redact_config_secrets_processor(config_secrets)

    # Test data with nested dictionary
    event_dict = {
        "event": "api_call",
        "request": {
            "headers": {"auth": {"token": "secret_token"}},
            "body": "data with secret_token embedded",
        },
    }

    # Execute
    result = processor(None, "", copy.deepcopy(event_dict))

    # Assert
    assert result["event"] == "api_call"
    assert result["request"]["headers"]["auth"]["token"] == "*" * len("secret_token")
    assert (
        result["request"]["body"]
        == "data with " + "*" * len("secret_token") + " embedded"
    )


def test_redact_config_secrets_processor_with_deep_nesting_warning():
    # Setup
    config_secrets = {"deep_secret"}
    processor = get_redact_config_secrets_processor(config_secrets)

    # Create a deeply nested dictionary that exceeds the nesting limit (6)
    event_dict = {"event": "deep_test"}
    nested_dict = event_dict
    for i in range(8):  # Create 8 levels of nesting
        nested_dict["level"] = {}
        nested_dict = nested_dict["level"]

    nested_dict["secret"] = "deep_secret"

    # Execute with warning capture
    with pytest.warns(UserWarning) as record:
        processor(None, "", copy.deepcopy(event_dict))

    # Assert warning was raised
    assert len(record) > 0
    assert "Unable to redact deeply nested secrets" in str(record[0].message)


def test_redact_config_secrets_processor_with_unsupported_type_warning():
    # Setup
    config_secrets = {"secret"}
    processor = get_redact_config_secrets_processor(config_secrets)

    # Test data with unsupported type (list)
    event_dict = {"event": "test_unsupported", "data": ["item1", "item2"]}

    # Execute with warning capture
    with pytest.warns(UserWarning) as record:
        processor(None, "", copy.deepcopy(event_dict))

    # Assert warning was raised
    assert len(record) > 0
    assert "Unable to redact list log arguments" in str(record[0].message)


def test_redact_config_secrets_processor_with_empty_secrets():
    # Setup
    config_secrets = set()
    processor = get_redact_config_secrets_processor(config_secrets)

    # Test data
    event_dict = {"event": "test_empty", "sensitive": "password123"}

    # Execute
    result = processor(None, "", copy.deepcopy(event_dict))

    # Assert - nothing should be redacted
    assert result["event"] == "test_empty"
    assert result["sensitive"] == "password123"


@patch("structlog.get_config")
@patch("structlog.configure")
def test_redact_config_secrets_with_secrets(mock_configure, mock_get_config):
    # Setup
    config_secrets = {"test_secret"}
    mock_processors = ["processor1", "processor2"]
    mock_get_config.return_value = {"processors": mock_processors}

    # Execute
    redact_config_secrets(config_secrets)

    # Assert
    mock_get_config.assert_called_once()
    mock_configure.assert_called_once()

    # Check that our processor was inserted at the right position
    call_args = mock_configure.call_args[1]
    assert len(call_args["processors"]) == len(mock_processors)
    assert call_args["processors"][
        -2
    ]  # Check that the processor was inserted at the second-to-last position


@patch("structlog.get_config")
@patch("structlog.configure")
def test_redact_config_secrets_with_empty_secrets(mock_configure, mock_get_config):
    # Setup
    config_secrets = set()

    # Execute
    redact_config_secrets(config_secrets)

    # Assert - structlog should not be reconfigured
    mock_get_config.assert_not_called()
    mock_configure.assert_not_called()
