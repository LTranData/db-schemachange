from typing import Any, Dict

import structlog

from schemachange.session.base import BaseSession, DatabaseType


def get_db_session(
    db_type: str, logger: structlog.BoundLogger, session_kwargs: Dict[str, Any]
) -> BaseSession:
    if db_type == DatabaseType.DATABRICKS:
        from schemachange.session.databricks_session import DatabricksSession

        db_session = DatabricksSession(logger=logger, session_kwargs=session_kwargs)
    elif db_type == DatabaseType.MYSQL:
        from schemachange.session.mysql_session import MySQLSession

        db_session = MySQLSession(logger=logger, session_kwargs=session_kwargs)
    elif db_type == DatabaseType.ORACLE:
        from schemachange.session.oracle_session import OracleSession

        db_session = OracleSession(logger=logger, session_kwargs=session_kwargs)
    elif db_type == DatabaseType.POSTGRES:
        from schemachange.session.postgres_session import PostgresSession

        db_session = PostgresSession(logger=logger, session_kwargs=session_kwargs)
    elif db_type == DatabaseType.SNOWFLAKE:
        from schemachange.session.snowflake_session import SnowflakeSession

        db_session = SnowflakeSession(logger=logger, session_kwargs=session_kwargs)
    elif db_type == DatabaseType.SQL_SERVER:
        from schemachange.session.sqlserver_session import SQLServerSession

        db_session = SQLServerSession(logger=logger, session_kwargs=session_kwargs)
    else:
        DatabaseType.validate_value(attr="db_type", value=db_type)

    return db_session
