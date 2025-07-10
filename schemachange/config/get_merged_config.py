import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Union

import structlog

from schemachange.common.schema import ConfigArgsSchema
from schemachange.common.utils import (
    get_not_none_key_value,
    load_yaml_config,
    validate_directory,
    validate_file_path,
)
from schemachange.config.base import SubCommand
from schemachange.config.deploy_config import DeployConfig
from schemachange.config.parse_cli_args import parse_cli_args
from schemachange.config.render_config import RenderConfig


def get_yaml_config_kwargs(config_file_path: Optional[Path]) -> Dict:
    # Load YAML inputs and convert kebabs to snakes
    kwargs = {
        k.replace("-", "_"): v for (k, v) in load_yaml_config(config_file_path).items()
    }

    if "verbose" in kwargs:
        if kwargs["verbose"]:
            kwargs["log_level"] = logging.DEBUG
        kwargs.pop("verbose")

    if "vars" in kwargs:
        kwargs["config_vars"] = kwargs.pop("vars")

    return get_not_none_key_value(data=kwargs)


def get_merged_config(
    logger: structlog.BoundLogger,
) -> Union[DeployConfig, RenderConfig]:
    cli_kwargs = parse_cli_args(sys.argv[1:])
    logger.debug("cli_kwargs", **cli_kwargs)

    cli_config_vars = cli_kwargs.pop("config_vars")

    connections_file_path = validate_file_path(
        file_path=cli_kwargs.pop("connections_file_path", None)
    )

    config_folder = validate_directory(path=cli_kwargs.pop("config_folder", "."))
    config_file_name = cli_kwargs.pop("config_file_name")
    config_file_path = Path(config_folder) / config_file_name

    yaml_kwargs = get_yaml_config_kwargs(
        config_file_path=config_file_path,
    )
    logger.debug("yaml_kwargs", **yaml_kwargs)

    yaml_config_vars = yaml_kwargs.pop("config_vars", None)
    if yaml_config_vars is None:
        yaml_config_vars = {}

    if connections_file_path is None:
        connections_file_path = yaml_kwargs.pop("connections_file_path", None)

        if config_folder is not None and connections_file_path is not None:
            connections_file_path = config_folder / connections_file_path

        connections_file_path = validate_file_path(file_path=connections_file_path)

    config_vars = {
        **yaml_config_vars,
        **cli_config_vars,
    }

    # Override the YAML config with the CLI configuration
    kwargs = {
        "config_file_path": config_file_path,
        "config_vars": config_vars,
        **get_not_none_key_value(data=yaml_kwargs),
        **get_not_none_key_value(data=cli_kwargs),
    }
    if connections_file_path is not None:
        kwargs["connections_file_path"] = connections_file_path

    logger.debug("final kwargs", **kwargs)

    kwargs = ConfigArgsSchema().load(kwargs)
    if cli_kwargs["subcommand"] == SubCommand.DEPLOY:
        return DeployConfig.factory(**kwargs)
    elif cli_kwargs["subcommand"] == SubCommand.RENDER:
        return RenderConfig.factory(**kwargs)
    else:
        raise Exception(f"unhandled subcommand: {cli_kwargs['subcommand'] }")
