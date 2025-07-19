import datetime
import hashlib
import time
from collections import defaultdict
from textwrap import dedent, indent
from typing import Any, Dict, List, Optional, Tuple

import sqlparse
import structlog

from schemachange.common.utils import BaseEnum
from schemachange.config.change_history_table import ChangeHistoryTable
from schemachange.session.script import (
    DEPLOYABLE_SCRIPT_TYPES,
    AlwaysScript,
    RepeatableScript,
    RollbackScript,
    ScriptType,
    VersionedScript,
)

DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


class DDL(BaseEnum):
    CREATE = "CREATE"
    DROP = "DROP"
    ALTER = "ALTER"
    TRUNCATE = "TRUNCATE"
    COMMENT = "COMMENT"
    RENAME = "RENAME"
    SHOW = "SHOW"


class DQL(BaseEnum):
    SELECT = "SELECT"
    WITH = "WITH"


class DML(BaseEnum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOCK = "LOCK"
    CALL = "CALL"
    EXPLAIN_PLAN = "EXPLAIN PLAN"
    MERGE = "MERGE"
    UPSERT = "UPSERT"
    BULK_INSERT = "BULK INSERT"
    BULK_DELETE = "BULK DELETE"
    BULK_UPDATE = "BULK UPDATE"
    COPY_INTO = "COPY INTO"
    LOAD_DATA = "LOAD DATA"


class DCL(BaseEnum):
    GRANT = "GRANT"
    REVOKE = "REVOKE"
    DENY = "DENY"


class DatabaseType(BaseEnum):
    POSTGRES = "POSTGRES"
    SQL_SERVER = "SQL_SERVER"
    MYSQL = "MYSQL"
    ORACLE = "ORACLE"
    SNOWFLAKE = "SNOWFLAKE"
    DATABRICKS = "DATABRICKS"

    @classmethod
    def get_no_schema_databases(cls):
        return [DatabaseType.MYSQL, DatabaseType.ORACLE]


class ApplyStatus(BaseEnum):
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"
    ROLLED_BACK_FAILED = "ROLLED_BACK_FAILED"


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

    def clear(cls):
        _ = cls._instances.pop(cls, None)

    def clear_all(*args, **kwargs):
        Singleton._instances = {}


class BaseSession(metaclass=Singleton):
    def __init__(self, session_kwargs: Dict[str, Any], logger: structlog.BoundLogger):
        self.logger = logger
        self.change_history_table: ChangeHistoryTable = session_kwargs.get(
            "change_history_table"
        )
        self.autocommit = session_kwargs.get("autocommit")
        self.db_type = session_kwargs.get("db_type")
        self.connections_info = session_kwargs.get("connections_info")
        self.include_schema = self.db_type not in DatabaseType.get_no_schema_databases()
        self.user = None
        self._connection = None
        self._cursor = None

    @property
    def connection(self):
        if self._connection is None or not self._is_connection_alive():
            self._connect()
        return self._connection

    @property
    def cursor(self):
        if self._cursor is None or not self._is_connection_alive():
            self._cursor = self.connection.cursor()
        return self._cursor

    def _connect(self) -> None:
        pass

    def reset_session(self) -> None:
        pass

    def reset_query_tag(self, extra_tag=None) -> None:
        pass

    def fetch_change_history_metadata(self) -> List[Dict]:
        pass

    def create_change_history_schema(self, dry_run: bool) -> None:
        pass

    def set_autocommit(self, autocommit: bool) -> None:
        self._connection.autocommit = autocommit

    def _commit(self):
        self.connection.commit()

    def _rollback(self):
        self.connection.rollback()

    def execute_query_with_debug(self, query: str, dry_run: bool) -> None:
        if dry_run:
            self.logger.debug(
                "Running in dry-run mode. Skipping execution.",
                query=indent(dedent(query), prefix="\t"),
            )
        else:
            self.execute_query(query=dedent(query))

    def _is_connection_alive(self):
        if self._connection is None:
            return False
        try:
            self._cursor.execute("SELECT 1")
            self.get_executed_query_data(self._cursor)
            if not self.autocommit:
                self._connection.commit()
            return True
        except Exception:
            return False

    def get_executed_query_data(self, cursor) -> List[Dict[str, Any]]:
        columns = list(cursor.description)
        rows = cursor.fetchall()
        data = []
        for r in rows:
            tmp = {}
            for i, col in enumerate(columns):
                tmp[col[0].lower()] = r[i]
            data.append(tmp)

        return data

    def execute_query(self, query: str, params: Optional[Tuple] = None) -> Any:
        self.logger.debug(
            "Executing query",
            query=indent(query, prefix="\t"),
        )
        cursor = self.cursor
        normalized_query = query.strip().upper()
        is_ddl = normalized_query.startswith(tuple(DDL.items()))
        try:
            data = None

            if is_ddl:
                self.set_autocommit(autocommit=True)

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if is_ddl:
                self.set_autocommit(autocommit=self.autocommit)

            if normalized_query.startswith(tuple([*DQL.items(), DDL.SHOW])):
                data = self.get_executed_query_data(cursor)
            elif normalized_query.startswith(tuple(DML.items())):
                data = cursor.rowcount

            if not is_ddl and not self.autocommit:
                self._commit()

            return data
        except Exception as e:
            if not is_ddl and not self.autocommit:
                self._rollback()
            raise e

    def close(self) -> None:
        if self._cursor:
            self._cursor.close()
            self._cursor = None

        if self._connection:
            self._connection.close()
            self._connection = None

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
                INSTALLED_ON TIMESTAMP
            )
        """
        self.execute_query_with_debug(query=query, dry_run=dry_run)

    def change_history_table_exists(
        self, create_change_history_table: bool, dry_run: bool
    ) -> bool:
        change_history_metadata = self.fetch_change_history_metadata()
        if change_history_metadata:
            self.logger.info(
                f"Using existing change history table {self.change_history_table.fully_qualified}",
                last_altered=change_history_metadata[0].get("update_time"),
            )
            return True
        elif create_change_history_table:
            self.create_change_history_schema(dry_run=dry_run)
            self.create_change_history_table(dry_run=dry_run)
            if dry_run:
                return False
            self.logger.info("Created change history table")
            return True
        else:
            raise ValueError(
                f"Unable to find change history table {self.change_history_table.fully_qualified}"
            )

    def get_script_metadata(
        self, create_change_history_table: bool, dry_run: bool
    ) -> Tuple[
        Dict[str, Dict[str, str | int]] | None,
        Dict[str, List[str]] | None,
        str | int | None,
    ]:
        change_history_table_exists = self.change_history_table_exists(
            create_change_history_table=create_change_history_table,
            dry_run=dry_run,
        )
        if not change_history_table_exists:
            return {}, {}, None

        change_history, max_published_version = self.fetch_versioned_scripts()
        r_scripts_checksum = self.fetch_repeatable_scripts()

        self.logger.info(
            "Max applied change script version %(max_published_version)s"
            % {"max_published_version": max_published_version}
        )
        return change_history, r_scripts_checksum, max_published_version

    def fetch_repeatable_scripts(self) -> Dict[str, List[str]]:
        query = f"""\
        SELECT DISTINCT
            SCRIPT,
            FIRST_VALUE(CHECKSUM) OVER (
                PARTITION BY SCRIPT
                ORDER BY INSTALLED_ON DESC
            ) AS CHECKSUM
        FROM {self.change_history_table.fully_qualified}
        WHERE SCRIPT_TYPE = '{ScriptType.REPEATABLE}'
            AND STATUS = '{ApplyStatus.SUCCESS}'
            AND BATCH_STATUS = '{ApplyStatus.SUCCESS}'
        """
        data = self.execute_query(query=dedent(query))

        script_checksums: Dict[str, List[str]] = defaultdict(list)
        for item in data:
            script = item["script"]
            checksum = item["checksum"]

            script_checksums[script].append(checksum)

        return script_checksums

    def fetch_versioned_scripts(
        self,
    ) -> Tuple[Dict[str, Dict[str, str | int]], str | int | None]:
        query = f"""\
        SELECT VERSION, SCRIPT, CHECKSUM
        FROM {self.change_history_table.fully_qualified}
        WHERE SCRIPT_TYPE = '{ScriptType.VERSIONED}'
            AND STATUS = '{ApplyStatus.SUCCESS}'
            AND BATCH_STATUS = '{ApplyStatus.SUCCESS}'
            AND IS_FORCED = 'N'
        ORDER BY INSTALLED_ON DESC
        """
        data = self.execute_query(query=dedent(query))

        versioned_scripts: Dict[str, Dict[str, str | int]] = defaultdict(dict)
        versions: List[str | int | None] = []
        for item in data:
            version = item["version"]
            script = item["script"]
            checksum = item["checksum"]

            versions.append(version if version != "" else None)
            versioned_scripts[script] = {
                "version": version,
                "script": script,
                "checksum": checksum,
            }

        return versioned_scripts, versions[0] if versions else None

    def log_change_script(
        self,
        script: VersionedScript | RepeatableScript | AlwaysScript | RollbackScript,
        checksum: str,
        execution_time: int,
        status: str,
        batch_id: str,
        batch_status: str,
        force: bool,
    ) -> None:
        apply_user = f"'{self.user}'" if self.user else "NULL"
        query = f"""\
            INSERT INTO {self.change_history_table.fully_qualified} (
                VERSION,
                DESCRIPTION,
                SCRIPT,
                SCRIPT_TYPE,
                CHECKSUM,
                EXECUTION_TIME,
                STATUS,
                BATCH_ID,
                BATCH_STATUS,
                IS_FORCED,
                INSTALLED_BY,
                INSTALLED_ON
            ) VALUES (
                '{getattr(script, "version", "")}',
                '{script.description}',
                '{script.name}',
                '{script.type}',
                '{checksum}',
                {execution_time},
                '{status}',
                '{batch_id}',
                '{batch_status}',
                '{"Y" if force and script.type == ScriptType.VERSIONED else "N"}',
                {apply_user},
                '{datetime.datetime.now().strftime(DEFAULT_DATETIME_FORMAT)}'
            )
        """
        self.execute_query(query=dedent(query))

    def apply_change_script(
        self,
        script: VersionedScript | RepeatableScript | AlwaysScript | RollbackScript,
        script_content: str,
        dry_run: bool,
        logger: structlog.BoundLogger,
        batch_id: str,
        force: bool = False,
    ) -> None:
        if dry_run:
            logger.debug("Running in dry-run mode. Skipping execution")
            return
        logger.info("Applying change script")
        # Define a few other change related variables
        checksum = hashlib.sha224(script_content.encode("utf-8")).hexdigest()
        execution_time = 0

        # Execute the contents of the script
        if len(script_content) > 0:
            start = time.time()
            self.reset_session()
            self.reset_query_tag(extra_tag=script.name)
            try:
                for command in sqlparse.split(sql=script_content):
                    self.execute_query(query=command)
            except Exception as e:
                raise Exception(f"Failed to execute {script.name}") from e
            self.reset_query_tag()
            self.reset_session()
            end = time.time()
            execution_time = round(end - start)

        if script.type in DEPLOYABLE_SCRIPT_TYPES:
            self.log_change_script(
                script=script,
                checksum=checksum,
                execution_time=execution_time,
                status=ApplyStatus.SUCCESS,
                batch_id=batch_id,
                batch_status=ApplyStatus.IN_PROGRESS,
                force=force,
            )

    def update_batch_status(self, batch_id: str, batch_status: str) -> None:
        query = f"""\
            UPDATE {self.change_history_table.fully_qualified}
            SET BATCH_STATUS = '{batch_status}'
            WHERE BATCH_ID = '{batch_id}'
        """
        self.execute_query(query=dedent(query))

    def update_batch_script_status(
        self,
        script_name: str,
        script_type: str,
        checksum: str,
        status: str,
        batch_id: str,
    ) -> None:
        query = f"""\
            UPDATE {self.change_history_table.fully_qualified}
            SET STATUS = '{status}'
            WHERE BATCH_ID = '{batch_id}'
                AND SCRIPT = '{script_name}'
                AND SCRIPT_TYPE = '{script_type}'
                AND CHECKSUM = '{checksum}'
        """
        self.execute_query(query=dedent(query))

    def get_batch_by_id(self, batch_id: str) -> List[Dict[str, str]]:
        applied_script_types = [
            f"'{item}'"
            for item in ScriptType.items()
            if item in DEPLOYABLE_SCRIPT_TYPES
        ]
        query = f"""\
            SELECT SCRIPT, SCRIPT_TYPE, CHECKSUM, BATCH_ID, BATCH_STATUS
            FROM {self.change_history_table.fully_qualified}
            WHERE BATCH_ID = '{batch_id}'
                AND SCRIPT_TYPE IN ({', '.join(applied_script_types)})
                AND BATCH_STATUS != '{ApplyStatus.ROLLED_BACK}'
            ORDER BY INSTALLED_ON DESC
        """
        return self.execute_query(query=dedent(query))
