import structlog

from schemachange.action.deploy import deploy
from schemachange.action.render import render
from schemachange.action.rollback import rollback
from schemachange.common.utils import get_config_secrets
from schemachange.config.base import SubCommand
from schemachange.config.get_merged_config import get_merged_config
from schemachange.config.redact_config_secrets import redact_config_secrets
from schemachange.session.session_factory import get_db_session

module_logger = structlog.getLogger(__name__)


def get_schemachange_version():
    return "1.1.0"


def main():
    config = get_merged_config(logger=module_logger)
    session_kwargs = config.get_session_kwargs()

    config_secrets = get_config_secrets(session_kwargs.get("connections_info")).union(
        get_config_secrets(config.config_vars)
    )
    redact_config_secrets(config_secrets=config_secrets)
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(config.log_level),
    )
    logger = structlog.getLogger()
    logger = logger.bind(schemachange_version=get_schemachange_version())
    config.log_details()
    _subcommand = config.subcommand

    if _subcommand == SubCommand.RENDER:
        render(
            config=config,
            script_path=config.script_path,
            logger=logger,
        )
    else:
        db_session = get_db_session(
            db_type=config.db_type,
            logger=logger,
            session_kwargs=session_kwargs,
        )
        if _subcommand == SubCommand.DEPLOY:
            deploy(config=config, db_session=db_session, logger=logger)
        elif _subcommand == SubCommand.ROLLBACK:
            rollback(config=config, db_session=db_session, logger=logger)


if __name__ == "__main__":
    main()
