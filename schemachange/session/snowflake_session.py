from typing import Dict, List

import snowflake.connector

from schemachange.common.schema import SnowflakeConnectorArgsSchema
from schemachange.common.utils import get_connect_kwargs
from schemachange.session.base import BaseSession


class SnowflakeSession(BaseSession):
    def _connect(self):
        self.user = self.connections_info.get("user")
        self.warehouse = self.connections_info.get("warehouse")
        self.role = self.connections_info.get("role")
        self.database = self.connections_info.get("database")
        self.schema = self.connections_info.get("schema")
        self._connection = snowflake.connector.connect(
            **get_connect_kwargs(
                connections_info=self.connections_info,
                supported_args_schema=SnowflakeConnectorArgsSchema,
            )
        )
        self._cursor = self._connection.cursor()

    def set_autocommit(self, autocommit: bool) -> None:
        self._connection.autocommit(autocommit)

    def fetch_change_history_metadata(self) -> List[Dict]:
        schemachange_database = self.change_history_table.database_name

        # Check if database exists yet
        database_data = self.execute_query(
            query=f"SHOW DATABASES LIKE '{schemachange_database}'"
        )
        if not database_data:
            return []

        query = f"""\
            SELECT
                CREATED AS CREATE_TIME,
                LAST_ALTERED AS UPDATE_TIME
            FROM {self.change_history_table.database_name}.INFORMATION_SCHEMA.TABLES
            WHERE UPPER(TABLE_SCHEMA) = UPPER('{self.change_history_table.schema_name}')
                AND UPPER(TABLE_NAME) = UPPER('{self.change_history_table.table_name}')
        """
        data = self.execute_query(query=query)

        return data

    def reset_session(self):
        reset_query = []
        if self.role:
            reset_query.append(f"USE ROLE IDENTIFIER('{self.role}')")
        if self.warehouse:
            reset_query.append(f"USE WAREHOUSE IDENTIFIER('{self.warehouse}')")
        if self.database:
            reset_query.append(f"USE DATABASE IDENTIFIER('{self.database}')")
        if self.schema:
            reset_query.append(f"USE SCHEMA IDENTIFIER('{self.schema}')")

        if reset_query:
            self.execute_query(query="\n".join(reset_query))

    def create_change_history_schema(self, dry_run: bool) -> None:
        schemachange_database = self.change_history_table.database_name
        schemachange_schema = self.change_history_table.schema_name

        # Check if database exists yet
        database_data = self.execute_query(
            query=f"SHOW DATABASES LIKE '{schemachange_database}'"
        )
        if not database_data:
            raise Exception(
                f"Database '{schemachange_database}' of change history table does not exist. "
                "It should be created beforehand"
            )

        # Create schema within the schemachange database if not exists
        self.execute_query_with_debug(
            query=f"CREATE SCHEMA IF NOT EXISTS {schemachange_database}.{schemachange_schema}",
            dry_run=dry_run,
        )
