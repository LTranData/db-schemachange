from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Set

import jinja2
import structlog
import yaml
from marshmallow import Schema

from schemachange.jinja.jinja_env_var import JinjaEnvVar

logger = structlog.getLogger(__name__)

# Words with alphanumeric characters and underscores only
identifier_pattern = re.compile(r"^[\w]+$")


class BaseEnum:
    @classmethod
    def items(cls) -> List[str]:
        return [
            v for k, v in cls.__dict__.items() if isinstance(v, str) and k[:2] != "__"
        ]

    @classmethod
    def validate_value(cls, attr, value) -> None:
        valid_values = cls.items()
        if value not in valid_values:
            raise ValueError(
                f"Invalid value '{attr}', should be one of {valid_values}, actual '{value}'"
            )


def get_not_none_key_value(data: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in data.items() if v is not None}


def get_identifier_string(input_value: str, input_type: str) -> str | None:
    if input_value is None:
        return None
    elif identifier_pattern.match(input_value):
        return input_value
    else:
        raise ValueError(
            f"Invalid {input_type}: {input_value}. Should contain alphanumeric characters and underscores only"
        )


def get_config_secrets(config_vars: Dict[str, Dict | str] | None) -> Set[str]:
    """Extracts all secret values from the vars attributes in config"""

    def inner_extract_dictionary_secrets(
        dictionary: Dict[str, Dict | str] | None,
        child_of_secrets: bool = False,
    ) -> Set[str]:
        """Considers any key with the word secret in the name as a secret or
        all values as secrets if a child of a key named secrets.

        defined as an inner/ nested function to provide encapsulation
        """
        extracted_secrets: set[str] = set()

        if not dictionary:
            return extracted_secrets

        for key, value in dictionary.items():
            if isinstance(value, dict):
                if key == "secrets":
                    child_of_secrets = True
                extracted_secrets = (
                    extracted_secrets
                    | inner_extract_dictionary_secrets(value, child_of_secrets)
                )
            elif child_of_secrets or "SECRET" in key.upper():
                extracted_secrets.add(value.strip())

        return extracted_secrets

    return inner_extract_dictionary_secrets(config_vars)


def validate_file_path(file_path: Path | str | None) -> Path | None:
    if file_path is None:
        return None
    if isinstance(file_path, str):
        file_path = Path(file_path)
    if not file_path.is_file():
        raise ValueError(f"invalid file path: {str(file_path)}")
    return file_path


def validate_directory(path: Path | str | None) -> Path | None:
    if path is None:
        return None
    if isinstance(path, str):
        path = Path(path)
    if not path.is_dir():
        raise ValueError(f"Path is not valid directory: {str(path)}")
    return path


def validate_config_vars(config_vars: str | Dict | None) -> Dict:
    if config_vars is None:
        return {}

    if not isinstance(config_vars, dict):
        raise ValueError(
            f"config_vars did not parse correctly, please check its configuration: {config_vars}"
        )

    if "schemachange" in config_vars.keys():
        raise ValueError(
            "The variable 'schemachange' has been reserved for use by schemachange, please use a different name"
        )

    return config_vars


def load_yaml_config(config_file_path: Path | None) -> Dict[str, Any]:
    """
    Loads the schemachange config file and processes with jinja templating engine
    """
    config = dict()

    # First read in the yaml config file, if present
    if config_file_path is not None and config_file_path.is_file():
        with config_file_path.open() as config_file:
            # Run the config file through the jinja engine to give access to environmental variables
            # The config file does not have the same access to the jinja functionality that a script
            # has.
            config_template = jinja2.Template(
                config_file.read(),
                undefined=jinja2.StrictUndefined,
                extensions=[JinjaEnvVar],
            )

            raw_config = config_template.render()
            if raw_config:
                # The FullLoader parameter handles the conversion from YAML scalar values to Python the dictionary format
                config = yaml.load(raw_config, Loader=yaml.FullLoader)
        logger.info("Using config file", config_file_path=str(config_file_path))
    return config


def get_connect_kwargs(connections_info: Dict[str, Any], supported_args_schema: Schema):
    connect_kwargs = supported_args_schema().load(connections_info)
    return get_not_none_key_value(data=connect_kwargs)
