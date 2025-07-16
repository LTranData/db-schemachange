from __future__ import annotations

import dataclasses
from typing import Literal, Dict, Any

from schemachange.config.base import SubCommand
from schemachange.config.deploy_config import DeployConfig

# Rollback config should be same with deploy config
# plus batch_id attribute
@dataclasses.dataclass(frozen=True)
class RollbackConfig(DeployConfig):
    subcommand: Literal["rollback"] = SubCommand.ROLLBACK
    batch_id: str | None = None

    @classmethod
    def factory(
        cls,
        batch_id: str,
        **kwargs,
    ):
        if "subcommand" in kwargs:
            kwargs.pop("subcommand")

        return super().factory(
            subcommand=SubCommand.ROLLBACK,
            batch_id=batch_id,
            **kwargs,
        )
    
    def get_session_kwargs(self) -> Dict[str, Any]:
        return super().get_session_kwargs()