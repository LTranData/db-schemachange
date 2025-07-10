from __future__ import annotations

import argparse
import json
import logging
import sys
from enum import Enum
from typing import Dict

import structlog

from schemachange.common.utils import get_not_none_key_value
from schemachange.config.base import SubCommand
from schemachange.session.base import DatabaseType

logger = structlog.getLogger(__name__)


class DeprecateConnectionArgAction(argparse.Action):
    def __init__(self, *args, **kwargs):
        self.call_count = 0
        if "help" in kwargs:
            kwargs["help"] = (
                f'[DEPRECATED - Set in connections-config.yml instead.] {kwargs["help"]}'
            )
        super().__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if self.call_count == 0:
            sys.stderr.write(
                f"{', '.join(self.option_strings)} is deprecated. It will be ignored in future versions.\n"
            )
            sys.stderr.write(self.help + "\n")
        self.call_count += 1
        setattr(namespace, self.dest, values)


def parse_cli_args(args) -> Dict:
    parser = argparse.ArgumentParser(
        prog="schemachange",
        description="Apply schema changes to a database. Full readme at "
        "https://github.com/lam1051999/db-schemachange",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--config-folder",
        type=str,
        default=".",
        help="The folder to look in for the schemachange-config.yml file "
        "(the default is the current working directory)",
        required=False,
    )
    parent_parser.add_argument(
        "--config-file-name",
        type=str,
        default="schemachange-config.yml",
        help="The schemachange config YAML file name. Must be in the directory supplied as the config-folder "
        "(Default: schemachange-config.yml)",
        required=False,
    )
    parent_parser.add_argument(
        "-f",
        "--root-folder",
        type=str,
        help="The root folder for the database change scripts",
        required=False,
    )
    parent_parser.add_argument(
        "-m",
        "--modules-folder",
        type=str,
        help="The modules folder for jinja macros and templates to be used across multiple scripts",
        required=False,
    )
    parent_parser.add_argument(
        "--vars",
        type=json.loads,
        help='Define values for the variables to replaced in change scripts, given in JSON format (e.g. {"variable1": '
        '"value1", "variable2": "value2"})',
        required=False,
    )
    parent_parser.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        const=True,
        default=None,
        help="Display verbose debugging details during execution (the default is False)",
        required=False,
    )

    subcommands = parser.add_subparsers(dest="subcommand")
    parser_deploy = subcommands.add_parser(SubCommand.DEPLOY, parents=[parent_parser])

    parser_deploy.register("action", "deprecate", DeprecateConnectionArgAction)
    parser_deploy.add_argument(
        "--db-type",
        type=str,
        help="Database type that schemachange run against",
        required=False,
        choices=DatabaseType.items(),
    )
    parser_deploy.add_argument(
        "--connections-file-path",
        type=str,
        help="File path to connections-config.yml",
        required=False,
    )
    parser_deploy.add_argument(
        "-c",
        "--change-history-table",
        type=str,
        help="Used to override the default name of the change history table (the default is "
        "METADATA.SCHEMACHANGE.CHANGE_HISTORY)",
        required=False,
    )
    parser_deploy.add_argument(
        "--create-change-history-table",
        action="store_const",
        const=True,
        default=None,
        help="Create the change history schema and table, if they do not exist (the default is False)",
        required=False,
    )
    parser_deploy.add_argument(
        "-ac",
        "--autocommit",
        action="store_const",
        const=True,
        default=None,
        help="Enable autocommit feature for DML commands (the default is False)",
        required=False,
    )
    parser_deploy.add_argument(
        "--dry-run",
        action="store_const",
        const=True,
        default=None,
        help="Run schemachange in dry run mode (the default is False)",
        required=False,
    )
    parser_render = subcommands.add_parser(
        SubCommand.RENDER,
        description="Renders a script to the console, used to check and verify jinja output from scripts.",
        parents=[parent_parser],
    )
    parser_render.add_argument(
        "--script-path", type=str, help="Path to the script to render"
    )

    # The original parameters did not support subcommands. Check if a subcommand has been supplied
    # if not default to deploy to match original behaviour.
    if len(args) == 0 or not any(
        subcommand in args[0].upper()
        for subcommand in [item.upper() for item in SubCommand.items()]
    ):
        args = [SubCommand.DEPLOY] + args

    parsed_args = parser.parse_args(args)

    parsed_kwargs = parsed_args.__dict__

    if "log_level" in parsed_kwargs and isinstance(parsed_kwargs["log_level"], Enum):
        parsed_kwargs["log_level"] = parsed_kwargs["log_level"].value

    parsed_kwargs["config_vars"] = {}
    if "vars" in parsed_kwargs:
        config_vars = parsed_kwargs.pop("vars")
        if config_vars is not None:
            parsed_kwargs["config_vars"] = config_vars

    if "verbose" in parsed_kwargs:
        parsed_kwargs["log_level"] = (
            logging.DEBUG if parsed_kwargs["verbose"] else logging.INFO
        )
        parsed_kwargs.pop("verbose")

    return get_not_none_key_value(data=parsed_kwargs)
