from typing import Dict, List

import pymssql

from schemachange.common.schema import SQLServerConnectorArgsSchema
from schemachange.common.utils import get_connect_kwargs
from schemachange.session.base import BaseSession


class SQLServerSession(BaseSession):
    def _connect(self):
        self.user = self.connections_info.get("user")
        self.database = self.connections_info.get("database")
        self._connection = pymssql.connect(
            **get_connect_kwargs(
                connections_info=self.connections_info,
                supported_args_schema=SQLServerConnectorArgsSchema,
            )
        )
        self._cursor = self._connection.cursor()

    def set_autocommit(self, autocommit: bool) -> None:
        self._connection.autocommit(autocommit)

    def create_change_history_table(self, dry_run: bool) -> None:
        query = f"""\
            CREATE TABLE {self.change_history_table.fully_qualified} (
                VERSION VARCHAR(1000),
                DESCRIPTION VARCHAR(1000),
                SCRIPT VARCHAR(1000),
                SCRIPT_TYPE VARCHAR(1000),
                CHECKSUM VARCHAR(1000),
                EXECUTION_TIME BIGINT,
                STATUS VARCHAR(1000),
                BATCH_ID VARCHAR(1000),
                BATCH_STATUS VARCHAR(1000),
                IS_FORCED VARCHAR(1000),
                INSTALLED_BY VARCHAR(1000),
                INSTALLED_ON DATETIME2
            )
        """
        self.execute_query_with_debug(query=query, dry_run=dry_run)

    def fetch_change_history_metadata(self) -> List[Dict]:
        schemachange_database = self.change_history_table.database_name

        # Check if database exists yet
        database_data = self.execute_query(
            query=f"SELECT 1 FROM sys.databases WHERE name = '{schemachange_database}'"
        )
        if not database_data:
            return []

        query = f"""\
            SELECT 1
            FROM {self.change_history_table.database_name}.INFORMATION_SCHEMA.TABLES
            WHERE LOWER(TABLE_CATALOG) = LOWER('{self.change_history_table.database_name}')
                AND LOWER(TABLE_SCHEMA) = LOWER('{self.change_history_table.schema_name}')
                AND LOWER(TABLE_NAME) = LOWER('{self.change_history_table.table_name}')
                AND TABLE_TYPE = 'BASE TABLE'
        """
        data = self.execute_query(query=query)

        return data

    def reset_session(self):
        if self.database:
            self.execute_query(query=f"USE {self.database}")

    def create_change_history_schema(self, dry_run: bool) -> None:
        schemachange_database = self.change_history_table.database_name
        schemachange_schema = self.change_history_table.schema_name

        # Check if database exists yet
        database_data = self.execute_query(
            query=f"SELECT 1 FROM sys.databases WHERE name = '{schemachange_database}'"
        )
        if not database_data:
            raise Exception(
                f"Database '{schemachange_database}' of change history table does not exist. "
                "It should be created beforehand"
            )

        # Create schema within the schemachange database if not exists
        if not dry_run:
            self.execute_query(query=f"USE {schemachange_database}")
        schema_data = self.execute_query(
            query=f"SELECT 1 FROM sys.schemas WHERE name = '{schemachange_schema}'"
        )
        if not schema_data:
            self.execute_query_with_debug(
                query=f"CREATE SCHEMA {schemachange_schema}", dry_run=dry_run
            )
