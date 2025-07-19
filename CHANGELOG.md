# Changelog
All notable changes to this project will be documented in this file.

*The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).*

## [1.1.0] - 2025-07-19

### Added

- Support aggressive deployment for specific versioned scripts

## [1.0.4] - 2025-07-18

### Added

- Support secrets filtering for connection detail logging

## [1.0.3] - 2025-07-17

### Changed

- Revert hardcoded lib version in schemachange cli.py

## [1.0.2] - 2025-07-17

### Changed

- Update README.md for `rollback` command

## [1.0.1] - 2025-07-17

### Changed

- Update README.md for `rollback` command

## [1.0.0] - 2025-07-17

### Added

- Add batch information for each deployment, as a foundation to implement Rollback functionality
- Add Rollback support to revert database changes, use with `rollback` subcommand

### Changed

- Standardize change history table record status and batch status update after applying changes


## [0.1.2] - 2025-07-12

### Fixed

- Fixed multi statement count exception for Snowflake and add default value for `session_parameters`

## [0.1.1] - 2025-07-12

### Changed

- Sync with new GitHub username

## [0.1.0] - 2025-07-12

### Fixed

- Hotfix session factory to support installation options

## [0.0.9] - 2025-07-12

### Changed

- Update `README.md` installation options instructions

## [0.0.8] - 2025-07-12

### Added

- Add installation options for specific connector

## [0.0.7] - 2025-07-12

### Changed

- Preserve query content in render step and remove semicolon from template query

## [0.0.6] - 2025-07-12

### Changed

- Add script content validation before action

## [0.0.5] - 2025-07-11

### Changed

- Use sqlparse instead of sqlglot for simple query splitting

## [0.0.4] - 2025-07-11

### Changed

- Use DATETIME2 for SQL Server and use sqlglot for parsing SQL file content

## [0.0.3] - 2025-07-11

### Changed

- Hotfix timestamp to microseconds for correct version order

## [0.0.2] - 2025-07-11

### Changed

- Update `README.md` for PyPI package link and Docker run instructions

## [0.0.1] - 2025-07-10

### Added

- Add support for Databricks, MySQL, Oracle, Postgres, Snowflake, and SQL Server

### Changed

- Complete refactor of source code, unit tests, and functionality