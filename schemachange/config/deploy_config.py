from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any, Dict, Literal

from schemachange.common.utils import get_not_none_key_value, load_yaml_config
from schemachange.config.base import BaseConfig, SubCommand
from schemachange.config.change_history_table import ChangeHistoryTable
from schemachange.session.base import DatabaseType


@dataclasses.dataclass(frozen=True)
class DeployConfig(BaseConfig):
    subcommand: Literal["deploy"] = SubCommand.DEPLOY
    connections_file_path: Path | None = None
    change_history_table: ChangeHistoryTable | None = dataclasses.field(
        default_factory=ChangeHistoryTable
    )
    create_change_history_table: bool = False
    autocommit: bool = False
    dry_run: bool = False
    db_type: str | None = None
    query_tag: str | None = None
    force: bool = False
    from_version: str | None = None
    to_version: str | None = None

    @classmethod
    def factory(
        cls,
        config_file_path: Path,
        change_history_table: str | None = None,
        db_type: str | None = None,
        query_tag: str | None = None,
        force: bool = False,
        from_version: str | None = None,
        to_version: str | None = None,
        **kwargs,
    ):
        if "subcommand" in kwargs:
            kwargs.pop("subcommand")

        change_history_table = ChangeHistoryTable.from_str(
            table_str=change_history_table,
            include_schema=db_type not in DatabaseType.get_no_schema_databases(),
        )

        return super().factory(
            subcommand=SubCommand.DEPLOY,
            config_file_path=config_file_path,
            change_history_table=change_history_table,
            db_type=db_type,
            query_tag=query_tag,
            force=force,
            from_version=from_version,
            to_version=to_version,
            **kwargs,
        )

    def get_session_kwargs(self) -> Dict[str, Any]:
        session_kwargs = {
            "change_history_table": self.change_history_table,
            "autocommit": self.autocommit,
            "db_type": self.db_type,
            "query_tag": self.query_tag,
        }

        # Load YAML inputs and convert kebabs to snakes
        connections_info = {
            k.replace("-", "_"): v
            for (k, v) in load_yaml_config(self.connections_file_path).items()
        }

        session_kwargs = {**session_kwargs, "connections_info": connections_info}

        return get_not_none_key_value(data=session_kwargs)
