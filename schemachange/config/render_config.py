from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Literal

from schemachange.common.utils import validate_file_path
from schemachange.config.base import BaseConfig, SubCommand


@dataclasses.dataclass(frozen=True)
class RenderConfig(BaseConfig):
    script_path: Path | None = None
    subcommand: Literal["render"] = SubCommand.RENDER

    @classmethod
    def factory(
        cls,
        script_path: Path | str,
        **kwargs,
    ):
        # Ignore Deploy arguments
        field_names = [field.name for field in dataclasses.fields(RenderConfig)]
        kwargs = {k: v for k, v in kwargs.items() if k in field_names}

        if "subcommand" in kwargs:
            kwargs.pop("subcommand")

        return super().factory(
            subcommand=SubCommand.RENDER,
            script_path=validate_file_path(file_path=script_path),
            **kwargs,
        )

    def __post_init__(self):
        if self.script_path is None:
            raise TypeError(
                "RenderConfig is missing 1 required argument: 'script_path'"
            )
