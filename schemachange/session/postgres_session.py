from typing import Dict, List

import psycopg

from schemachange.common.schema import PostgresConnectorArgsSchema
from schemachange.common.utils import get_connect_kwargs
from schemachange.config.change_history_table import ChangeHistoryTable
from schemachange.session.base import BaseSession


class PostgresSession(BaseSession):
    def _connect(self):
        self.user = self.connections_info.get("user")
        self.dbname = self.connections_info.get("dbname")
        self.change_history_table = ChangeHistoryTable.from_str(
            table_str=f"{self.dbname}.{self.change_history_table.schema_name}.{self.change_history_table.table_name}",
            include_schema=self.include_schema,
        )
        self._connection = psycopg.connect(
            **get_connect_kwargs(
                connections_info=self.connections_info,
                supported_args_schema=PostgresConnectorArgsSchema,
            )
        )
        self._cursor = self._connection.cursor()

    def fetch_change_history_metadata(self) -> List[Dict]:
        query = f"""\
            SELECT 1
            FROM INFORMATION_SCHEMA.TABLES
            WHERE LOWER(TABLE_SCHEMA) = LOWER('{self.change_history_table.schema_name}')
                AND LOWER(TABLE_NAME) = LOWER('{self.change_history_table.table_name}')
        """
        data = self.execute_query(query=query)

        return data

    def create_change_history_schema(self, dry_run: bool) -> None:
        self.logger.info(
            f"Using current session database '{self.dbname}' "
            "for creating change history table"
        )
        query = f"CREATE SCHEMA IF NOT EXISTS {self.change_history_table.schema_name}"
        self.execute_query_with_debug(query=query, dry_run=dry_run)
