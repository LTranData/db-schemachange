import structlog
import configparser
from pathlib import Path

from schemachange.action.deploy import deploy
from schemachange.action.render import render
from schemachange.action.rollback import rollback
from schemachange.config.base import SubCommand
from schemachange.config.get_merged_config import get_merged_config
from schemachange.config.redact_config_secrets import redact_config_secrets
from schemachange.session.session_factory import get_db_session

module_logger = structlog.getLogger(__name__)
ROOT_DIR = Path(__file__).parent.parent.resolve()


def get_schemachange_version():
    setup_file_path = ROOT_DIR / "setup.cfg"
    config = configparser.RawConfigParser()
    config.read(setup_file_path)

    if "metadata" in config and "version" in config["metadata"]:
        return config["metadata"]["version"]
    return None


def main():
    config = get_merged_config(logger=module_logger)
    redact_config_secrets(config_secrets=config.secrets)

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
    elif _subcommand == SubCommand.DEPLOY:
        db_session = get_db_session(
            db_type=config.db_type,
            logger=logger,
            session_kwargs=config.get_session_kwargs(),
        )
        deploy(config=config, db_session=db_session, logger=logger)
    elif _subcommand == SubCommand.ROLLBACK:
        db_session = get_db_session(
            db_type=config.db_type,
            logger=logger,
            session_kwargs=config.get_session_kwargs(),
        )
        rollback(config=config, db_session=db_session, logger=logger)
    else:
        SubCommand.validate_value(attr="subcommand", value=_subcommand)


if __name__ == "__main__":
    main()
