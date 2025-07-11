from typing import Dict, List

from databricks import sql

from schemachange.common.schema import DatabricksConnectorArgsSchema
from schemachange.common.utils import get_connect_kwargs
from schemachange.session.base import BaseSession


class DatabricksSession(BaseSession):
    def _get_credentials_provider_config(self):
        from databricks.sdk.core import Config, oauth_service_principal

        config = Config(
            host=f"https://{self.server_hostname}",
            client_id=self.credentials_provider.get("client_id"),
            client_secret=self.credentials_provider.get("client_secret"),
        )

        return oauth_service_principal(config)

    def set_current_user(self):
        user_data = self.execute_query(query="SELECT current_user() AS _user")
        if user_data:
            self.user = user_data[0]["_user"]

    def _connect(self):
        self.init_kwargs = get_connect_kwargs(
            connections_info=self.connections_info,
            supported_args_schema=DatabricksConnectorArgsSchema,
        )
        self.server_hostname = self.init_kwargs.get("server_hostname")
        self.access_token = self.init_kwargs.get("access_token")
        self.credentials_provider = self.init_kwargs.get(
            "credentials_provider"
        )  # Should be a dictionary with client_id and client_secret
        self.auth_type = self.init_kwargs.get("auth_type")
        self.catalog = self.init_kwargs.get("catalog")
        self.schema = self.init_kwargs.get("schema")

        # Personal access token authentication
        if self.access_token is not None:
            if self.credentials_provider:
                self.init_kwargs.pop("credentials_provider")
            if self.auth_type:
                self.init_kwargs.pop("auth_type")

        # OAuth machine-to-machine (M2M) authentication
        elif self.credentials_provider is not None:
            self.init_kwargs["credentials_provider"] = (
                self._get_credentials_provider_config
            )
            if self.access_token:
                self.init_kwargs.pop("access_token")
            if self.auth_type:
                self.init_kwargs.pop("auth_type")

        # OAuth user-to-machine (U2M) authentication
        elif self.auth_type is not None:
            if self.credentials_provider:
                self.init_kwargs.pop("credentials_provider")
            if self.access_token:
                self.init_kwargs.pop("access_token")

        self._connection = sql.connect(**self.init_kwargs)
        self._cursor = self._connection.cursor()
        self.set_current_user()

    def set_autocommit(self, autocommit: bool) -> None:
        # No-op because Databricks does not support transactions
        pass

    def _commit(self):
        # No-op because Databricks does not support transactions
        pass

    def _rollback(self):
        # No-op because Databricks does not support transactions
        pass

    def fetch_change_history_metadata(self) -> List[Dict]:
        schemachange_database = self.change_history_table.database_name

        # Check if database exists yet
        database_data = self.execute_query(
            query=f"SHOW CATALOGS LIKE '{schemachange_database}'"
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
        if self.catalog:
            reset_query.append(f"USE CATALOG IDENTIFIER('{self.catalog}')")
        if self.schema:
            reset_query.append(f"USE SCHEMA IDENTIFIER('{self.schema}')")

        if reset_query:
            self.execute_query(query="\n".join(reset_query))

    def create_change_history_schema(self, dry_run: bool) -> None:
        schemachange_database = self.change_history_table.database_name
        schemachange_schema = self.change_history_table.schema_name

        # Check if database exists yet
        database_data = self.execute_query(
            query=f"SHOW CATALOGS LIKE '{schemachange_database}'"
        )
        if not database_data:
            raise Exception(
                f"Catalog '{schemachange_database}' of change history table does not exist. "
                "It should be created beforehand"
            )
        # Create schema within the schemachange database if not exists
        self.execute_query_with_debug(
            query=f"CREATE SCHEMA IF NOT EXISTS {schemachange_database}.{schemachange_schema}",
            dry_run=dry_run,
        )
