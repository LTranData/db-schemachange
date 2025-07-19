from __future__ import annotations

import hashlib
import re
import uuid
from typing import List

import structlog

from schemachange.common.utils import validate_script_content
from schemachange.config.deploy_config import DeployConfig
from schemachange.jinja.jinja_template_processor import JinjaTemplateProcessor
from schemachange.session.base import ApplyStatus, BaseSession
from schemachange.session.script import (
    DEPLOYABLE_SCRIPT_TYPES,
    ScriptType,
    get_all_scripts_recursively,
)


def alphanum_convert(text: str):
    if text.isdigit():
        return int(text)
    return text.lower()


# This function will return a list containing the parts of the key (split by number parts)
# Each number is converted to and integer and string parts are left as strings
# This will enable correct sorting in python when the lists are compared
# e.g. get_alphanum_key('1.2.2') results in ['', 1, '.', 2, '.', 2, '']
def get_alphanum_key(key: str | int | None) -> List:
    if key == "" or key is None:
        return []
    alphanum_key = [alphanum_convert(c) for c in re.split("([0-9]+)", key)]
    return alphanum_key


def sorted_alphanumeric(data):
    return sorted(data, key=get_alphanum_key)


def deploy(
    config: DeployConfig, db_session: BaseSession, logger: structlog.BoundLogger
):
    batch_id = str(uuid.uuid4())
    logger.info(
        "Starting deploy",
        dry_run=config.dry_run,
        batch_id=batch_id,
        change_history_table=db_session.change_history_table.fully_qualified,
        autocommit=db_session.autocommit,
        db_type=db_session.db_type,
        connections_info=db_session.connections_info,
    )

    try:
        if config.force:
            logger.info(
                "Running aggressive deployment mode for versioned scripts",
                from_version=config.from_version,
                to_version=config.to_version,
            )

        (
            versioned_scripts,
            r_scripts_checksum,
            max_published_version,
        ) = db_session.get_script_metadata(
            create_change_history_table=config.create_change_history_table,
            dry_run=config.dry_run,
        )

        max_published_version = get_alphanum_key(max_published_version)

        # Find all scripts in the root folder (recursively) and sort them correctly
        all_scripts = get_all_scripts_recursively(
            root_directory=config.root_folder,
        )
        all_script_names = list(all_scripts.keys())
        # Sort scripts such that versioned scripts get applied first and then the repeatable ones.
        all_script_names_sorted = (
            sorted_alphanumeric(
                [
                    script
                    for script in all_script_names
                    if script[0] == ScriptType.VERSIONED.lower()
                ]
            )
            + sorted_alphanumeric(
                [
                    script
                    for script in all_script_names
                    if script[0] == ScriptType.REPEATABLE.lower()
                ]
            )
            + sorted_alphanumeric(
                [
                    script
                    for script in all_script_names
                    if script[0] == ScriptType.ALWAYS.lower()
                ]
            )
        )

        scripts_skipped = 0
        scripts_applied = 0

        # Loop through each script in order and apply any required changes
        for script_name in all_script_names_sorted:
            script = all_scripts[script_name]
            script_type = script.type

            if script_type not in DEPLOYABLE_SCRIPT_TYPES:
                continue

            script_log = logger.bind(
                # The logging keys will be sorted alphabetically.
                # Appending 'a' is a lazy way to get the script name to appear at the start of the log
                a_script_name=script.name,
                script_version=getattr(script, "version", "N/A"),
            )
            # Always process with jinja engine
            jinja_processor = JinjaTemplateProcessor(
                project_root=config.root_folder, modules_folder=config.modules_folder
            )
            content = jinja_processor.render(
                jinja_processor.relpath(script.file_path),
                config.config_vars,
            )

            checksum_current = hashlib.sha224(content.encode("utf-8")).hexdigest()

            # Apply a versioned-change script only if the version is newer than the most recent change in the database
            # Apply any other scripts, i.e. repeatable scripts, irrespective of the most recent change in the database
            if script_type == ScriptType.VERSIONED:
                script_metadata = versioned_scripts.get(script.name)
                script_version = script.version

                if config.force:
                    if (
                        get_alphanum_key(script_version)
                        < get_alphanum_key(config.from_version)
                    ) or (
                        get_alphanum_key(script_version)
                        > get_alphanum_key(config.to_version)
                    ):
                        script_log.debug(
                            "Skipping versioned script because it's not in aggressive deployment version range",
                            script_version=script_version,
                        )
                        scripts_skipped += 1
                        continue
                else:
                    if (
                        max_published_version is not None
                        and get_alphanum_key(script_version) <= max_published_version
                    ):
                        if script_metadata is None:
                            script_log.debug(
                                "Skipping versioned script because it's older than the most recently applied change",
                                max_published_version=max_published_version,
                            )
                            scripts_skipped += 1
                            continue
                        else:
                            script_log.debug(
                                "Script has already been applied",
                                max_published_version=max_published_version,
                            )
                            if script_metadata["checksum"] != checksum_current:
                                script_log.info(
                                    "Script checksum has drifted since application"
                                )

                            scripts_skipped += 1
                            continue

            # Apply only R scripts where the checksum changed compared to the last execution of snowchange
            if script_type == ScriptType.REPEATABLE:
                # check if R file was already executed
                if (
                    r_scripts_checksum is not None
                ) and script.name in r_scripts_checksum:
                    checksum_last = r_scripts_checksum[script.name][0]
                else:
                    checksum_last = ""

                # check if there is a change of the checksum in the script
                if checksum_current == checksum_last:
                    script_log.debug(
                        "Skipping change script because there is no change since the last execution"
                    )
                    scripts_skipped += 1
                    continue

            validate_script_content(script_name=script.name, script_content=content)
            db_session.apply_change_script(
                script=script,
                script_content=content,
                dry_run=config.dry_run,
                logger=script_log,
                batch_id=batch_id,
                force=config.force,
            )

            scripts_applied += 1

        db_session.update_batch_status(
            batch_id=batch_id, batch_status=ApplyStatus.SUCCESS
        )
        logger.info(
            "Completed successfully",
            scripts_applied=scripts_applied,
            scripts_skipped=scripts_skipped,
        )
        db_session.close()
    except Exception as e:
        db_session.update_batch_status(
            batch_id=batch_id, batch_status=ApplyStatus.FAILED
        )
        db_session.close()
        raise Exception("Deploy failed") from e
