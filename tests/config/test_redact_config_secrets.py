import copy
import warnings
from unittest.mock import Mock, patch

import pytest
from structlog import PrintLogger

from schemachange.config.redact_config_secrets import (
    get_redact_config_secrets_processor,
    redact_config_secrets,
)


# Fixtures
@pytest.fixture
def config_secrets():
    """Sample set of secrets for testing."""
    return {"secret123", "password456", "token789"}


@pytest.fixture
def mock_logger():
    """Mock PrintLogger for testing."""
    return Mock(spec=PrintLogger)


@pytest.fixture
def processor(config_secrets):
    """Processor function configured with test secrets."""
    return get_redact_config_secrets_processor(config_secrets)


@pytest.fixture
def sample_secrets():
    """Alternative fixture providing a different set of secrets."""
    return {"secret_key", "password123", "api_token_xyz"}


@pytest.fixture
def complex_event_dict():
    """Complex event dictionary for comprehensive testing."""
    return {
        "event": "complex_operation",
        "user": {
            "id": 123,
            "credentials": ["password123", "backup_secret_key"],
            "metadata": {
                "last_login": "2023-01-01",
                "tokens": {"access": "api_token_xyz", "refresh": "refresh_token"},
            },
        },
        "operation_details": ("create", "user", {"secret": "secret_key"}),
        "flags": {"has_secret_key", "is_admin", "verified"},
    }


# Tests for get_redact_config_secrets_processor
def test_redact_simple_string_values(processor, mock_logger):
    """Test redaction of simple string values in event dict."""
    event_dict = {
        "event": "user login",
        "password": "secret123",
        "token": "token789",
        "username": "john_doe",
    }

    result = processor(mock_logger, "info", event_dict)

    assert result["password"] == "*" * len("secret123")
    assert result["token"] == "*" * len("token789")
    assert result["username"] == "john_doe"  # Not redacted
    assert result["event"] == "user login"


def test_redact_nested_dict_values(processor, mock_logger):
    """Test redaction of secrets in nested dictionaries."""
    event_dict = {
        "event": "nested test",
        "user": {
            "name": "john",
            "credentials": {"password": "secret123", "api_key": "token789"},
        },
    }

    result = processor(mock_logger, "info", event_dict)

    assert result["user"]["credentials"]["password"] == "*" * len("secret123")
    assert result["user"]["credentials"]["api_key"] == "*" * len("token789")
    assert result["user"]["name"] == "john"


def test_redact_list_values(processor, mock_logger):
    """Test redaction of secrets in lists."""
    event_dict = {
        "event": "list test",
        "passwords": ["secret123", "password456", "safe_value"],
        "mixed_list": [{"secret": "token789"}, "normal_string"],
    }

    result = processor(mock_logger, "info", event_dict)

    assert result["passwords"][0] == "*" * len("secret123")
    assert result["passwords"][1] == "*" * len("password456")
    assert result["passwords"][2] == "safe_value"
    assert result["mixed_list"][0]["secret"] == "*" * len("token789")
    assert result["mixed_list"][1] == "normal_string"


def test_redact_set_values(processor, mock_logger):
    """Test redaction of secrets in sets."""
    event_dict = {
        "event": "set test",
        "secret_set": {"secret123", "password456", "safe_value"},
    }

    result = processor(mock_logger, "info", event_dict)

    redacted_set = result["secret_set"]
    assert "*" * len("secret123") in redacted_set
    assert "*" * len("password456") in redacted_set
    assert "safe_value" in redacted_set


def test_redact_tuple_values(processor, mock_logger):
    """Test redaction of secrets in tuples."""
    event_dict = {
        "event": "tuple test",
        "secret_tuple": ("secret123", "password456", "safe_value"),
    }

    result = processor(mock_logger, "info", event_dict)

    assert result["secret_tuple"][0] == "*" * len("secret123")
    assert result["secret_tuple"][1] == "*" * len("password456")
    assert result["secret_tuple"][2] == "safe_value"
    assert isinstance(result["secret_tuple"], tuple)


def test_redact_non_string_converted_to_string(processor, mock_logger):
    """Test redaction of non-string values that get converted to strings."""
    event_dict = {
        "event": "non-string test",
        "number_secret": 123456,  # Will be converted to string
        "bool_value": True,
    }

    result = processor(mock_logger, "info", event_dict)

    # Numbers and booleans are converted to strings, so check the string representation
    # If "secret123" was in the string representation, it would be redacted
    assert result["number_secret"] == "123456"  # No secrets in this number
    assert result["bool_value"] == "True"


def test_deep_nesting_warning(processor, mock_logger):
    """Test that deeply nested structures trigger a warning."""
    # Create a deeply nested structure (level > 6)
    nested_dict = {"level": 0}
    current = nested_dict
    for i in range(8):  # Create 8 levels of nesting
        current["next"] = {"level": i + 1, "secret": "secret123"}
        current = current["next"]

    event_dict = {"event": "deep nesting test", "data": nested_dict}

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        processor(mock_logger, "info", event_dict)

        # Should have triggered a warning about deep nesting
        assert len(w) > 0
        assert "Unable to redact deeply nested secrets" in str(w[0].message)


def test_string_conversion_exception(processor, mock_logger):
    """Test handling of objects that can't be converted to strings."""

    class UnconvertibleObject:
        def __str__(self):
            raise Exception("Cannot convert to string")

    event_dict = {"event": "conversion error test", "bad_object": UnconvertibleObject()}

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        processor(mock_logger, "info", event_dict)

        # Should have triggered a warning about unable to redact
        assert len(w) > 0
        assert "Unable to redact" in str(w[0].message)
        assert "UnconvertibleObject" in str(w[0].message)


def test_partial_string_replacement(processor, mock_logger):
    """Test that secrets are replaced within larger strings."""
    event_dict = {
        "event": "partial replacement test",
        "message": "The secret is secret123 and token is token789",
        "url": "https://api.example.com?token=token789&user=john",
    }

    result = processor(mock_logger, "info", event_dict)

    expected_message = (
        f"The secret is {'*' * len('secret123')} and token is {'*' * len('token789')}"
    )
    expected_url = f"https://api.example.com?token={'*' * len('token789')}&user=john"

    assert result["message"] == expected_message
    assert result["url"] == expected_url


def test_empty_secrets_set(mock_logger):
    """Test behavior with empty secrets set."""
    processor = get_redact_config_secrets_processor(set())
    event_dict = {"event": "empty secrets test", "password": "secret123"}

    result = processor(mock_logger, "info", event_dict)

    # Nothing should be redacted
    assert result["password"] == "secret123"


def test_original_dict_not_modified(processor, mock_logger):
    """Test that the original event_dict is not modified."""
    original_dict = {
        "event": "immutability test",
        "password": "secret123",
        "nested": {"token": "token789"},
    }

    # Create a copy to compare against
    dict_copy = copy.deepcopy(original_dict)

    result = processor(mock_logger, "info", original_dict)

    # Original should be unchanged
    assert original_dict == dict_copy
    # But result should be redacted
    assert result["password"] == "*" * len("secret123")
    assert result["nested"]["token"] == "*" * len("token789")


def test_multiple_occurrences_of_same_secret(processor, mock_logger):
    """Test that all occurrences of the same secret are redacted."""
    event_dict = {
        "event": "multiple occurrences test",
        "field1": "secret123",
        "field2": "prefix_secret123_suffix",
        "field3": ["secret123", "other", "secret123"],
    }

    result = processor(mock_logger, "info", event_dict)

    redacted_secret = "*" * len("secret123")
    assert result["field1"] == redacted_secret
    assert result["field2"] == f"prefix_{redacted_secret}_suffix"
    assert result["field3"][0] == redacted_secret
    assert result["field3"][2] == redacted_secret
    assert result["field3"][1] == "other"


# Tests for redact_config_secrets function
@patch("structlog.get_config")
@patch("structlog.configure")
def test_redact_config_secrets_with_secrets(mock_configure, mock_get_config):
    """Test redact_config_secrets adds processor when secrets are provided."""
    # Mock the current structlog configuration
    mock_processor1 = Mock()
    mock_processor2 = Mock()
    mock_config = {"processors": [mock_processor1, mock_processor2]}
    mock_get_config.return_value = mock_config

    config_secrets = {"secret123", "password456"}

    redact_config_secrets(config_secrets)

    # Should have called get_config
    mock_get_config.assert_called_once()

    # Should have called configure with updated processors
    mock_configure.assert_called_once()
    call_args = mock_configure.call_args[1]

    # Should have 3 processors now (2 original + 1 redaction processor)
    assert len(call_args["processors"]) == 3

    # Redaction processor should be inserted before the last one
    assert call_args["processors"][0] == mock_processor1
    assert call_args["processors"][2] == mock_processor2
    # call_args["processors"][1] should be our redaction processor


@patch("structlog.get_config")
@patch("structlog.configure")
def test_redact_config_secrets_with_empty_secrets(mock_configure, mock_get_config):
    """Test redact_config_secrets does nothing when no secrets provided."""
    config_secrets = set()

    redact_config_secrets(config_secrets)

    # Should not have called get_config or configure
    mock_get_config.assert_not_called()
    mock_configure.assert_not_called()


@patch("structlog.get_config")
@patch("structlog.configure")
def test_redact_config_secrets_with_none(mock_configure, mock_get_config):
    """Test redact_config_secrets does nothing when None is provided."""
    config_secrets = None

    redact_config_secrets(config_secrets)

    # Should not have called get_config or configure
    mock_get_config.assert_not_called()
    mock_configure.assert_not_called()


@patch("structlog.get_config")
@patch("structlog.configure")
def test_redact_config_secrets_processor_insertion_order(
    mock_configure, mock_get_config
):
    """Test that the redaction processor is inserted in the correct position."""
    # Mock configuration with multiple processors
    processor1 = Mock()
    processor2 = Mock()
    final_processor = Mock()

    mock_config = {"processors": [processor1, processor2, final_processor]}
    mock_get_config.return_value = mock_config

    config_secrets = {"secret123"}

    redact_config_secrets(config_secrets)

    call_args = mock_configure.call_args[1]
    processors = call_args["processors"]

    # Should have 4 processors now
    assert len(processors) == 4

    # Order should be: processor1, processor2, redaction_processor, final_processor
    assert processors[0] == processor1
    assert processors[1] == processor2
    assert processors[3] == final_processor
    # processors[2] should be our redaction processor


# Integration and end-to-end tests
def test_end_to_end_redaction():
    """Test the complete flow from configuration to log redaction."""
    config_secrets = {"api_key_123", "password_xyz"}
    processor = get_redact_config_secrets_processor(config_secrets)

    # Simulate a complex log event
    event_dict = {
        "event": "user authentication",
        "timestamp": "2023-01-01T12:00:00Z",
        "user_id": 12345,
        "request": {
            "headers": {
                "authorization": "Bearer api_key_123",
                "user-agent": "MyApp/1.0",
            },
            "body": {"username": "john_doe", "password": "password_xyz"},
        },
        "response": {"status": 200, "tokens": ["api_key_123", "refresh_token_456"]},
    }

    result = processor(Mock(spec=PrintLogger), "info", event_dict)

    # Verify comprehensive redaction
    assert (
        result["request"]["headers"]["authorization"]
        == f"Bearer {'*' * len('api_key_123')}"
    )
    assert result["request"]["body"]["password"] == "*" * len("password_xyz")
    assert result["response"]["tokens"][0] == "*" * len("api_key_123")
    assert result["response"]["tokens"][1] == "refresh_token_456"  # Not redacted

    # Verify non-secret data is preserved (converted to string)
    assert result["user_id"] == "12345"  # Numbers are converted to strings
    assert result["request"]["body"]["username"] == "john_doe"
    assert result["response"]["status"] == "200"  # Numbers are converted to strings


def test_with_complex_fixtures(sample_secrets, complex_event_dict):
    """Test using pytest fixtures with complex data structures."""
    processor = get_redact_config_secrets_processor(sample_secrets)
    result = processor(Mock(spec=PrintLogger), "info", complex_event_dict)

    # Verify redaction worked with fixtures
    assert result["user"]["credentials"][0] == "*" * len("password123")

    # For sets, check that the secret was redacted within the string "has_secret_key"
    redacted_flags = result["flags"]
    has_redacted_secret = any(
        "has_" + "*" * len("secret_key") in flag for flag in redacted_flags
    )
    assert has_redacted_secret, f"Expected redacted secret in flags: {redacted_flags}"

    assert result["user"]["metadata"]["tokens"]["access"] == "*" * len("api_token_xyz")
    assert result["operation_details"][2]["secret"] == "*" * len("secret_key")


def test_processor_returns_callable():
    """Test that get_redact_config_secrets_processor returns a callable."""
    config_secrets = {"test_secret"}
    processor = get_redact_config_secrets_processor(config_secrets)

    assert callable(processor)


def test_processor_signature():
    """Test that the returned processor has the expected signature."""
    config_secrets = {"test_secret"}
    processor = get_redact_config_secrets_processor(config_secrets)

    # Should be able to call with logger, method_name, and event_dict
    mock_logger = Mock(spec=PrintLogger)
    event_dict = {"event": "test", "secret": "test_secret"}

    result = processor(mock_logger, "info", event_dict)

    assert isinstance(result, dict)
    assert result["secret"] == "*" * len("test_secret")


def test_non_string_values_converted_to_strings(processor, mock_logger):
    """Test that non-string values are converted to strings during processing."""
    event_dict = {
        "event": "type conversion test",
        "integer": 12345,
        "float": 3.14159,
        "boolean": True,
        "none_value": None,
        "list_with_number": [123, "text"],
    }

    result = processor(mock_logger, "info", event_dict)

    # All values should be converted to strings
    assert result["integer"] == "12345"
    assert result["float"] == "3.14159"
    assert result["boolean"] == "True"
    assert result["none_value"] == "None"
    assert result["list_with_number"][0] == "123"
    assert result["list_with_number"][1] == "text"


def test_secret_in_converted_string(mock_logger):
    """Test redaction when secret appears in string conversion of non-string value."""
    # Use a secret that could appear in string conversion
    config_secrets = {"123"}
    processor = get_redact_config_secrets_processor(config_secrets)

    event_dict = {
        "event": "conversion redaction test",
        "number_with_secret": 12345,  # Contains "123"
        "safe_number": 9876,
    }

    result = processor(mock_logger, "info", event_dict)

    # The "123" within "12345" should be redacted
    assert result["number_with_secret"] == "***45"
    assert result["safe_number"] == "9876"


def test_overlapping_secrets_order_dependency():
    """Test that overlapping secrets are handled based on iteration order."""
    # Test with different orderings to document the behavior
    config_secrets1 = {"secret", "secret123"}
    config_secrets2 = {"secret123", "secret"}

    processor1 = get_redact_config_secrets_processor(config_secrets1)
    processor2 = get_redact_config_secrets_processor(config_secrets2)

    event_dict = {"event": "test", "value": "secret123"}

    result1 = processor1(Mock(spec=PrintLogger), "info", event_dict)
    result2 = processor2(Mock(spec=PrintLogger), "info", event_dict)

    # Document that the result depends on the order of secrets processing
    # One of these should be fully redacted, the other partially
    assert result1["value"] in ["*********", "******123"]
    assert result2["value"] in ["*********", "******123"]
