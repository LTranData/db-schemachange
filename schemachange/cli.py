import structlog

from schemachange.action.deploy import deploy
from schemachange.action.render import render
from schemachange.config.base import SubCommand
from schemachange.config.get_merged_config import get_merged_config
from schemachange.config.redact_config_secrets import redact_config_secrets
from schemachange.session.session_factory import get_db_session

module_logger = structlog.getLogger(__name__)
SCHEMACHANGE_VERSION = "0.0.9"


def main():
    config = get_merged_config(logger=module_logger)
    redact_config_secrets(config_secrets=config.secrets)

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(config.log_level),
    )
    logger = structlog.getLogger()
    logger = logger.bind(schemachange_version=SCHEMACHANGE_VERSION)
    config.log_details()

    if config.subcommand == SubCommand.RENDER:
        render(
            config=config,
            script_path=config.script_path,
            logger=logger,
        )
    else:
        db_session = get_db_session(
            db_type=config.db_type,
            logger=logger,
            session_kwargs=config.get_session_kwargs(),
        )
        deploy(config=config, db_session=db_session, logger=logger)


if __name__ == "__main__":
    main()
