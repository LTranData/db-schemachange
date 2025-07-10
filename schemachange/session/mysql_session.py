from typing import Dict, List

import mysql.connector

from schemachange.common.schema import MySQLConnectorArgsSchema
from schemachange.common.utils import get_connect_kwargs
from schemachange.session.base import BaseSession


class MySQLSession(BaseSession):
    def _connect(self):
        self.database = self.connections_info.get("database")
        self.user = self.connections_info.get("user")
        self._connection = mysql.connector.connect(
            **get_connect_kwargs(
                connections_info=self.connections_info,
                supported_args_schema=MySQLConnectorArgsSchema,
            )
        )
        self._cursor = self._connection.cursor()

    def fetch_change_history_metadata(self) -> List[Dict]:
        query = f"""\
            SELECT
                CREATE_TIME,
                UPDATE_TIME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE UPPER(TABLE_SCHEMA) = '{self.change_history_table.database_name}'
                AND UPPER(TABLE_NAME) = '{self.change_history_table.table_name}'
        """
        data = self.execute_query(query=query)

        return data

    def reset_session(self):
        if self.database:
            self.execute_query(query=f"USE {self.database}")

    def create_change_history_schema(self, dry_run: bool) -> None:
        query = (
            f"CREATE DATABASE IF NOT EXISTS {self.change_history_table.database_name}"
        )
        self.execute_query_with_debug(query=query, dry_run=dry_run)
