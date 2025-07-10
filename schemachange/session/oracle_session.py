from typing import Dict, List

import oracledb

from schemachange.common.schema import OracleConnectorArgsSchema
from schemachange.common.utils import get_connect_kwargs
from schemachange.session.base import BaseSession


class OracleSession(BaseSession):
    def _connect(self):
        self.service_name = self.connections_info.get("service_name")
        self.user = self.connections_info.get("user")
        self._connection = oracledb.connect(
            **get_connect_kwargs(
                connections_info=self.connections_info,
                supported_args_schema=OracleConnectorArgsSchema,
            )
        )
        self._cursor = self._connection.cursor()
        self.set_autocommit(autocommit=self.autocommit)

    def fetch_change_history_metadata(self) -> List[Dict]:
        query = f"""\
            SELECT
                CREATED AS CREATE_TIME,
                LAST_DDL_TIME AS UPDATE_TIME
            FROM
                all_objects
            WHERE
                object_type = 'TABLE'
                AND object_name = '{self.change_history_table.table_name}'
                AND owner = '{self.change_history_table.database_name}'
        """
        data = self.execute_query(query=query)

        return data

    def reset_session(self):
        if self.service_name:
            self.execute_query(
                query=f"ALTER SESSION SET CURRENT_SCHEMA = {self.service_name}"
            )

    def create_change_history_schema(self, dry_run: bool) -> None:
        query = (
            f"CREATE DATABASE IF NOT EXISTS {self.change_history_table.database_name}"
        )
        self.execute_query_with_debug(query=query, dry_run=dry_run)
