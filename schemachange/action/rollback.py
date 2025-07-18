from __future__ import annotations

import structlog

from schemachange.common.utils import validate_script_content
from schemachange.config.rollback_config import RollbackConfig
from schemachange.jinja.jinja_template_processor import JinjaTemplateProcessor
from schemachange.session.base import ApplyStatus, BaseSession
from schemachange.session.script import ScriptType, get_all_scripts_recursively


def rollback(
    config: RollbackConfig, db_session: BaseSession, logger: structlog.BoundLogger
):
    batch_id = config.batch_id
    logger.info(
        "Starting rollback",
        dry_run=config.dry_run,
        batch_id=batch_id,
        change_history_table=db_session.change_history_table.fully_qualified,
        autocommit=db_session.autocommit,
        db_type=db_session.db_type,
        connections_info=db_session.connections_info,
    )

    try:
        scripts_applied = 0
        batch_data = db_session.get_batch_by_id(batch_id=batch_id)

        if not batch_data:
            logger.info("No batch data for this batch id", batch_id=batch_id)
            return

        local_rollback_scripts = {}
        all_scripts = get_all_scripts_recursively(
            root_directory=config.root_folder,
        )
        for _, script in all_scripts.items():
            if script.type == ScriptType.ROLLBACK:
                local_rollback_scripts[script.name] = script

        # Should rollback from latest to earliest INSTALLED_ON script
        # Hence, loop by batch_data because it is already sorted
        for deployed_script in batch_data:
            script_name = deployed_script["script"]
            # Script that is eligible for rollback
            eligible_script = local_rollback_scripts.get(
                f"{ScriptType.ROLLBACK}_{script_name}"
            )

            if not eligible_script:
                logger.info("No rollback script for", script_name=script_name)
                continue

            script_log = logger.bind(
                # The logging keys will be sorted alphabetically.
                # Appending 'a' is a lazy way to get the script name to appear at the start of the log
                a_script_name=eligible_script.name,
                script_version=getattr(script, "version", "N/A"),
            )

            # Always process with jinja engine
            jinja_processor = JinjaTemplateProcessor(
                project_root=config.root_folder, modules_folder=config.modules_folder
            )
            content = jinja_processor.render(
                jinja_processor.relpath(eligible_script.file_path),
                config.config_vars,
            )

            validate_script_content(
                script_name=eligible_script.name, script_content=content
            )
            db_session.apply_change_script(
                script=eligible_script,
                script_content=content,
                dry_run=config.dry_run,
                logger=script_log,
                batch_id=batch_id,
            )

            db_session.update_batch_script_status(
                script_name=script_name,
                script_type=deployed_script["script_type"],
                checksum=deployed_script["checksum"],
                status=ApplyStatus.ROLLED_BACK,
                batch_id=batch_id,
            )
            scripts_applied += 1

        db_session.update_batch_status(
            batch_id=batch_id, batch_status=ApplyStatus.ROLLED_BACK
        )
        logger.info(
            "Completed successfully",
            scripts_applied=scripts_applied,
        )
        db_session.close()
    except Exception as e:
        db_session.update_batch_status(
            batch_id=batch_id, batch_status=ApplyStatus.ROLLED_BACK_FAILED
        )
        db_session.close()
        raise Exception("Rollback failed") from e
