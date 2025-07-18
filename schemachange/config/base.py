from __future__ import annotations

import dataclasses
import logging
from abc import ABC
from pathlib import Path
from typing import Any, Dict, Literal, TypeVar

import structlog

from schemachange.common.utils import BaseEnum, validate_config_vars, validate_directory

logger = structlog.getLogger(__name__)
T = TypeVar("T", bound="BaseConfig")


class SubCommand(BaseEnum):
    DEPLOY = "deploy"
    RENDER = "render"
    ROLLBACK = "rollback"


@dataclasses.dataclass(frozen=True)
class BaseConfig(ABC):
    subcommand: Literal["deploy", "render", "rollback"]
    config_file_path: Path | None = None
    root_folder: Path | None = Path(".")
    modules_folder: Path | None = None
    config_vars: dict = dataclasses.field(default_factory=dict)
    log_level: int = logging.INFO

    @classmethod
    def factory(
        cls,
        subcommand: Literal["deploy", "render", "rollback"],
        config_file_path: Path,
        root_folder: Path | str | None = Path("."),
        modules_folder: Path | str | None = None,
        config_vars: str | dict | None = None,
        log_level: int = logging.INFO,
        **kwargs,
    ):
        return cls(
            subcommand=subcommand,
            config_file_path=config_file_path,
            root_folder=validate_directory(path=root_folder),
            modules_folder=validate_directory(path=modules_folder),
            config_vars=validate_config_vars(config_vars=config_vars),
            log_level=log_level,
            **kwargs,
        )

    def log_details(self):
        logger.info("Using root folder", root_folder=str(self.root_folder))
        if self.modules_folder:
            logger.info(
                "Using Jinja modules folder", modules_folder=str(self.modules_folder)
            )

        logger.info("Using variables", vars=self.config_vars)

    def get_session_kwargs(self) -> Dict[str, Any]:
        return {}
