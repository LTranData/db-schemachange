from marshmallow import Schema, exceptions, fields, validates_schema

from schemachange.config.base import SubCommand

OPTIONAL_ARGS = {"required": False, "allow_none": True}


class DatabricksCredentialsProviderSchema(Schema):
    client_id = fields.String(required=True, allow_none=True)
    client_secret = fields.String(required=True, allow_none=True)


class DatabricksConnectorArgsSchema(Schema):
    # https://docs.databricks.com/aws/en/dev-tools/python-sql-connector#connection-class
    server_hostname = fields.String(**OPTIONAL_ARGS)
    http_path = fields.String(**OPTIONAL_ARGS)
    access_token = fields.String(**OPTIONAL_ARGS)
    auth_type = fields.String(**OPTIONAL_ARGS)
    credentials_provider = fields.Nested(
        DatabricksCredentialsProviderSchema, **OPTIONAL_ARGS
    )
    password = fields.String(**OPTIONAL_ARGS)
    username = fields.String(**OPTIONAL_ARGS)
    session_configuration = fields.Dict(
        keys=fields.String(), values=fields.Raw(), **OPTIONAL_ARGS
    )
    http_headers = fields.List(
        fields.Tuple((fields.String(), fields.String())), **OPTIONAL_ARGS
    )
    catalog = fields.String(**OPTIONAL_ARGS)
    schema = fields.String(**OPTIONAL_ARGS)
    use_cloud_fetch = fields.Boolean(**OPTIONAL_ARGS)
    user_agent_entry = fields.String(**OPTIONAL_ARGS)
    # Additional parameters from databricks/sql/client.py::Connection
    use_inline_params = fields.Boolean(**OPTIONAL_ARGS)
    oauth_client_id = fields.String(**OPTIONAL_ARGS)
    oauth_redirect_port = fields.Integer(**OPTIONAL_ARGS)
    experimental_oauth_persistence = fields.Raw(**OPTIONAL_ARGS)


class MySQLConnectorArgsSchema(Schema):
    # https://dev.mysql.com/doc/connector-python/en/connector-python-connectargs.html
    database = fields.String(**OPTIONAL_ARGS)
    user = fields.String(**OPTIONAL_ARGS)
    password = fields.String(**OPTIONAL_ARGS)
    password1 = fields.String(**OPTIONAL_ARGS)
    password2 = fields.String(**OPTIONAL_ARGS)
    password3 = fields.String(**OPTIONAL_ARGS)
    host = fields.String(**OPTIONAL_ARGS)
    port = fields.Integer(**OPTIONAL_ARGS)
    unix_socket = fields.String(**OPTIONAL_ARGS)
    use_unicode = fields.Boolean(**OPTIONAL_ARGS)
    charset = fields.String(**OPTIONAL_ARGS)
    collation = fields.String(**OPTIONAL_ARGS)
    converter_class = fields.Raw(**OPTIONAL_ARGS)
    converter_str_fallback = fields.Boolean(**OPTIONAL_ARGS)
    autocommit = fields.Boolean(**OPTIONAL_ARGS)
    time_zone = fields.String(**OPTIONAL_ARGS)
    sql_mode = fields.String(**OPTIONAL_ARGS)
    get_warnings = fields.Boolean(**OPTIONAL_ARGS)
    raise_on_warnings = fields.Boolean(**OPTIONAL_ARGS)
    connection_timeout = fields.Float(**OPTIONAL_ARGS)
    read_timeout = fields.Float(**OPTIONAL_ARGS)
    write_timeout = fields.Float(**OPTIONAL_ARGS)
    client_flags = fields.String(**OPTIONAL_ARGS)
    compress = fields.Boolean(**OPTIONAL_ARGS)
    buffered = fields.Boolean(**OPTIONAL_ARGS)
    raw = fields.Boolean(**OPTIONAL_ARGS)
    ssl_ca = fields.String(**OPTIONAL_ARGS)
    ssl_cert = fields.String(**OPTIONAL_ARGS)
    ssl_key = fields.String(**OPTIONAL_ARGS)
    ssl_verify_cert = fields.Boolean(**OPTIONAL_ARGS)
    ssl_verify_identity = fields.Boolean(**OPTIONAL_ARGS)
    ssl_cipher = fields.String(**OPTIONAL_ARGS)
    tls_ciphersuites = fields.String(**OPTIONAL_ARGS)
    ssl_disabled = fields.Boolean(**OPTIONAL_ARGS)
    tls_versions = fields.List(fields.String(), **OPTIONAL_ARGS)
    passwd = fields.String(**OPTIONAL_ARGS)
    db = fields.String(**OPTIONAL_ARGS)
    connect_timeout = fields.Float(**OPTIONAL_ARGS)
    dsn = fields.String(**OPTIONAL_ARGS)
    force_ipv6 = fields.Boolean(**OPTIONAL_ARGS)
    auth_plugin = fields.String(**OPTIONAL_ARGS)
    allow_local_infile = fields.Boolean(**OPTIONAL_ARGS)
    allow_local_infile_in_path = fields.String(**OPTIONAL_ARGS)
    consume_results = fields.Boolean(**OPTIONAL_ARGS)
    conn_attrs = fields.Dict(keys=fields.String(), values=fields.Raw(), **OPTIONAL_ARGS)
    dns_srv = fields.String(**OPTIONAL_ARGS)
    use_pure = fields.Boolean(**OPTIONAL_ARGS)
    krb_service_principal = fields.String(**OPTIONAL_ARGS)
    oci_config_file = fields.String(**OPTIONAL_ARGS)
    oci_config_profile = fields.String(**OPTIONAL_ARGS)
    webauthn_callback = fields.Raw(**OPTIONAL_ARGS)
    kerberos_auth_mode = fields.String(**OPTIONAL_ARGS)
    init_command = fields.String(**OPTIONAL_ARGS)
    openid_token_file = fields.String(**OPTIONAL_ARGS)
    fido_callback = fields.Raw(**OPTIONAL_ARGS)
    pool_name = fields.String(**OPTIONAL_ARGS)
    pool_size = fields.Integer(**OPTIONAL_ARGS)
    pool_reset_session = fields.Boolean(**OPTIONAL_ARGS)
    failover = fields.String(**OPTIONAL_ARGS)
    option_files = fields.String(**OPTIONAL_ARGS)
    option_groups = fields.List(fields.String(), **OPTIONAL_ARGS)


class OracleConnectorArgsSchema(Schema):
    # oracledb/connection.py::connect
    dsn = fields.String(**OPTIONAL_ARGS)
    pool = fields.Raw(**OPTIONAL_ARGS)
    pool_alias = fields.String(**OPTIONAL_ARGS)
    conn_class = fields.Raw(**OPTIONAL_ARGS)
    params = fields.Raw(**OPTIONAL_ARGS)
    user = fields.String(**OPTIONAL_ARGS)
    proxy_user = fields.String(**OPTIONAL_ARGS)
    password = fields.String(**OPTIONAL_ARGS)
    newpassword = fields.String(**OPTIONAL_ARGS)
    wallet_password = fields.String(**OPTIONAL_ARGS)
    access_token = fields.String(**OPTIONAL_ARGS)
    host = fields.String(**OPTIONAL_ARGS)
    port = fields.Integer(**OPTIONAL_ARGS)
    protocol = fields.String(**OPTIONAL_ARGS)
    https_proxy = fields.String(**OPTIONAL_ARGS)
    https_proxy_port = fields.Integer(**OPTIONAL_ARGS)
    service_name = fields.String(**OPTIONAL_ARGS)
    instance_name = fields.String(**OPTIONAL_ARGS)
    sid = fields.String(**OPTIONAL_ARGS)
    server_type = fields.String(**OPTIONAL_ARGS)
    cclass = fields.String(**OPTIONAL_ARGS)
    purity = fields.Raw(**OPTIONAL_ARGS)
    expire_time = fields.Integer(**OPTIONAL_ARGS)
    retry_count = fields.Integer(**OPTIONAL_ARGS)
    retry_delay = fields.Integer(**OPTIONAL_ARGS)
    tcp_connect_timeout = fields.Float(**OPTIONAL_ARGS)
    ssl_server_dn_match = fields.Boolean(**OPTIONAL_ARGS)
    ssl_server_cert_dn = fields.String(**OPTIONAL_ARGS)
    wallet_location = fields.String(**OPTIONAL_ARGS)
    events = fields.Boolean(**OPTIONAL_ARGS)
    externalauth = fields.Boolean(**OPTIONAL_ARGS)
    mode = fields.Raw(**OPTIONAL_ARGS)
    disable_oob = fields.Boolean(**OPTIONAL_ARGS)
    stmtcachesize = fields.Integer(**OPTIONAL_ARGS)
    edition = fields.String(**OPTIONAL_ARGS)
    tag = fields.String(**OPTIONAL_ARGS)
    matchanytag = fields.Boolean(**OPTIONAL_ARGS)
    config_dir = fields.String(**OPTIONAL_ARGS)
    appcontext = fields.List(fields.Raw(), **OPTIONAL_ARGS)
    shardingkey = fields.List(fields.Raw(), **OPTIONAL_ARGS)
    supershardingkey = fields.List(fields.Raw(), **OPTIONAL_ARGS)
    debug_jdwp = fields.String(**OPTIONAL_ARGS)
    connection_id_prefix = fields.String(**OPTIONAL_ARGS)
    ssl_context = fields.Raw(**OPTIONAL_ARGS)
    sdu = fields.Integer(**OPTIONAL_ARGS)
    pool_boundary = fields.String(**OPTIONAL_ARGS)
    use_tcp_fast_open = fields.Boolean(**OPTIONAL_ARGS)
    ssl_version = fields.Raw(**OPTIONAL_ARGS)
    program = fields.String(**OPTIONAL_ARGS)
    machine = fields.String(**OPTIONAL_ARGS)
    terminal = fields.String(**OPTIONAL_ARGS)
    osuser = fields.String(**OPTIONAL_ARGS)
    driver_name = fields.String(**OPTIONAL_ARGS)
    use_sni = fields.Boolean(**OPTIONAL_ARGS)
    thick_mode_dsn_passthrough = fields.Boolean(**OPTIONAL_ARGS)
    extra_auth_params = fields.String(**OPTIONAL_ARGS)
    handle = fields.Integer(**OPTIONAL_ARGS)


class PostgresConnectorArgsSchema(Schema):
    # psycopg/connection.py::connect
    conninfo = fields.String(**OPTIONAL_ARGS)
    autocommit = fields.Boolean(**OPTIONAL_ARGS)
    prepare_threshold = fields.Integer(**OPTIONAL_ARGS)
    context = fields.Raw(**OPTIONAL_ARGS)
    row_factory = fields.Raw(**OPTIONAL_ARGS)
    cursor_factory = fields.Raw(**OPTIONAL_ARGS)
    # https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-PARAMKEYWORDS
    host = fields.String(**OPTIONAL_ARGS)
    hostaddr = fields.String(**OPTIONAL_ARGS)
    port = fields.String(**OPTIONAL_ARGS)
    dbname = fields.String(**OPTIONAL_ARGS)
    user = fields.String(**OPTIONAL_ARGS)
    password = fields.String(**OPTIONAL_ARGS)
    passfile = fields.String(**OPTIONAL_ARGS)
    require_auth = fields.String(**OPTIONAL_ARGS)
    channel_binding = fields.String(**OPTIONAL_ARGS)
    connect_timeout = fields.String(**OPTIONAL_ARGS)
    client_encoding = fields.String(**OPTIONAL_ARGS)
    options = fields.String(**OPTIONAL_ARGS)
    application_name = fields.String(**OPTIONAL_ARGS)
    fallback_application_name = fields.String(**OPTIONAL_ARGS)
    keepalives = fields.String(**OPTIONAL_ARGS)
    keepalives_idle = fields.String(**OPTIONAL_ARGS)
    keepalives_interval = fields.String(**OPTIONAL_ARGS)
    keepalives_count = fields.String(**OPTIONAL_ARGS)
    tcp_user_timeout = fields.String(**OPTIONAL_ARGS)
    replication = fields.String(**OPTIONAL_ARGS)
    gssencmode = fields.String(**OPTIONAL_ARGS)
    sslmode = fields.String(**OPTIONAL_ARGS)
    requiressl = fields.String(**OPTIONAL_ARGS)
    sslnegotiation = fields.String(**OPTIONAL_ARGS)
    sslcompression = fields.String(**OPTIONAL_ARGS)
    sslcert = fields.String(**OPTIONAL_ARGS)
    sslkey = fields.String(**OPTIONAL_ARGS)
    sslpassword = fields.String(**OPTIONAL_ARGS)
    sslcertmode = fields.String(**OPTIONAL_ARGS)
    sslrootcert = fields.String(**OPTIONAL_ARGS)
    sslcrl = fields.String(**OPTIONAL_ARGS)
    sslcrldir = fields.String(**OPTIONAL_ARGS)
    sslsni = fields.String(**OPTIONAL_ARGS)
    requirepeer = fields.String(**OPTIONAL_ARGS)
    ssl_min_protocol_version = fields.String(**OPTIONAL_ARGS)
    ssl_max_protocol_version = fields.String(**OPTIONAL_ARGS)
    krbsrvname = fields.String(**OPTIONAL_ARGS)
    gsslib = fields.String(**OPTIONAL_ARGS)
    gssdelegation = fields.String(**OPTIONAL_ARGS)
    service = fields.String(**OPTIONAL_ARGS)
    target_session_attrs = fields.String(**OPTIONAL_ARGS)
    load_balance_hosts = fields.String(**OPTIONAL_ARGS)


class SnowflakeConnectorArgsSchema(Schema):
    # snowflake/connector/connection.py::DEFAULT_CONFIGURATION
    dsn = fields.String(**OPTIONAL_ARGS)
    user = fields.String(**OPTIONAL_ARGS)
    password = fields.String(**OPTIONAL_ARGS)
    host = fields.String(**OPTIONAL_ARGS)
    port = fields.String(**OPTIONAL_ARGS)
    database = fields.String(**OPTIONAL_ARGS)
    proxy_host = fields.String(**OPTIONAL_ARGS)
    proxy_port = fields.String(**OPTIONAL_ARGS)
    proxy_user = fields.String(**OPTIONAL_ARGS)
    proxy_password = fields.String(**OPTIONAL_ARGS)
    protocol = fields.String(**OPTIONAL_ARGS)
    warehouse = fields.String(**OPTIONAL_ARGS)
    region = fields.String(**OPTIONAL_ARGS)
    account = fields.String(**OPTIONAL_ARGS)
    schema = fields.String(**OPTIONAL_ARGS)
    role = fields.String(**OPTIONAL_ARGS)
    session_id = fields.String(**OPTIONAL_ARGS)
    login_timeout = fields.Integer(**OPTIONAL_ARGS)
    network_timeout = fields.Integer(**OPTIONAL_ARGS)
    socket_timeout = fields.Integer(**OPTIONAL_ARGS)
    external_browser_timeout = fields.Integer(**OPTIONAL_ARGS)
    backoff_policy = fields.Raw(**OPTIONAL_ARGS)
    passcode_in_password = fields.Boolean(**OPTIONAL_ARGS)
    passcode = fields.String(**OPTIONAL_ARGS)
    private_key = fields.String(**OPTIONAL_ARGS)
    private_key_file = fields.String(**OPTIONAL_ARGS)
    private_key_file_pwd = fields.String(**OPTIONAL_ARGS)
    token = fields.String(**OPTIONAL_ARGS)
    token_file_path = fields.String(**OPTIONAL_ARGS)
    authenticator = fields.String(**OPTIONAL_ARGS)
    workload_identity_provider = fields.Raw(**OPTIONAL_ARGS)
    workload_identity_entra_resource = fields.String(**OPTIONAL_ARGS)
    mfa_callback = fields.Raw(**OPTIONAL_ARGS)
    password_callback = fields.Raw(**OPTIONAL_ARGS)
    auth_class = fields.Raw(**OPTIONAL_ARGS)
    application = fields.String(**OPTIONAL_ARGS)
    internal_application_name = fields.String(**OPTIONAL_ARGS)
    internal_application_version = fields.String(**OPTIONAL_ARGS)
    disable_ocsp_checks = fields.Boolean(**OPTIONAL_ARGS)
    ocsp_fail_open = fields.Boolean(**OPTIONAL_ARGS)
    inject_client_pause = fields.Integer(**OPTIONAL_ARGS)
    session_parameters = fields.Dict(
        keys=fields.String(),
        values=fields.Raw(),
        load_default={"MULTI_STATEMENT_COUNT": "0"},
        **OPTIONAL_ARGS,
    )
    autocommit = fields.Boolean(**OPTIONAL_ARGS)
    client_session_keep_alive = fields.Boolean(**OPTIONAL_ARGS)
    client_session_keep_alive_heartbeat_frequency = fields.Integer(**OPTIONAL_ARGS)
    client_prefetch_threads = fields.Integer(**OPTIONAL_ARGS)
    client_fetch_threads = fields.Integer(**OPTIONAL_ARGS)
    client_fetch_use_mp = fields.Boolean(**OPTIONAL_ARGS)
    numpy = fields.Boolean(**OPTIONAL_ARGS)
    ocsp_response_cache_filename = fields.String(**OPTIONAL_ARGS)
    converter_class = fields.Raw(**OPTIONAL_ARGS)
    validate_default_parameters = fields.Boolean(**OPTIONAL_ARGS)
    probe_connection = fields.Boolean(**OPTIONAL_ARGS)
    paramstyle = fields.String(**OPTIONAL_ARGS)
    timezone = fields.String(**OPTIONAL_ARGS)
    consent_cache_id_token = fields.Boolean(**OPTIONAL_ARGS)
    service_name = fields.String(**OPTIONAL_ARGS)
    support_negative_year = fields.Boolean(**OPTIONAL_ARGS)
    log_max_query_length = fields.Integer(**OPTIONAL_ARGS)
    disable_request_pooling = fields.Boolean(**OPTIONAL_ARGS)
    client_store_temporary_credential = fields.Boolean(**OPTIONAL_ARGS)
    client_request_mfa_token = fields.Boolean(**OPTIONAL_ARGS)
    use_openssl_only = fields.Boolean(**OPTIONAL_ARGS)
    arrow_number_to_decimal = fields.Boolean(**OPTIONAL_ARGS)
    enable_stage_s3_privatelink_for_us_east_1 = fields.Boolean(**OPTIONAL_ARGS)
    reuse_results = fields.Boolean(**OPTIONAL_ARGS)
    interpolate_empty_sequences = fields.Boolean(**OPTIONAL_ARGS)
    enable_connection_diag = fields.Boolean(**OPTIONAL_ARGS)
    connection_diag_log_path = fields.String(**OPTIONAL_ARGS)
    connection_diag_whitelist_path = fields.String(**OPTIONAL_ARGS)
    connection_diag_allowlist_path = fields.String(**OPTIONAL_ARGS)
    log_imported_packages_in_telemetry = fields.Boolean(**OPTIONAL_ARGS)
    disable_query_context_cache = fields.Boolean(**OPTIONAL_ARGS)
    json_result_force_utf8_decoding = fields.Boolean(**OPTIONAL_ARGS)
    server_session_keep_alive = fields.Boolean(**OPTIONAL_ARGS)
    enable_retry_reason_in_query_response = fields.Boolean(**OPTIONAL_ARGS)
    session_token = fields.String(**OPTIONAL_ARGS)
    master_token = fields.String(**OPTIONAL_ARGS)
    master_validity_in_seconds = fields.Integer(**OPTIONAL_ARGS)
    disable_console_login = fields.Boolean(**OPTIONAL_ARGS)
    debug_arrow_chunk = fields.Boolean(**OPTIONAL_ARGS)
    disable_saml_url_check = fields.Boolean(**OPTIONAL_ARGS)
    iobound_tpe_limit = fields.Integer(**OPTIONAL_ARGS)
    oauth_client_id = fields.String(**OPTIONAL_ARGS)
    oauth_client_secret = fields.String(**OPTIONAL_ARGS)
    oauth_authorization_url = fields.String(**OPTIONAL_ARGS)
    oauth_token_request_url = fields.String(**OPTIONAL_ARGS)
    oauth_redirect_uri = fields.String(**OPTIONAL_ARGS)
    oauth_scope = fields.String(**OPTIONAL_ARGS)
    oauth_disable_pkce = fields.Boolean(**OPTIONAL_ARGS)
    oauth_enable_refresh_tokens = fields.Boolean(**OPTIONAL_ARGS)
    oauth_enable_single_use_refresh_tokens = fields.Boolean(**OPTIONAL_ARGS)
    check_arrow_conversion_error_on_every_column = fields.Boolean(**OPTIONAL_ARGS)
    external_session_id = fields.String(**OPTIONAL_ARGS)


class SQLServerConnectorArgsSchema(Schema):
    # pymssql/_pymssql.pyi::connect
    server = fields.String(**OPTIONAL_ARGS)
    user = fields.String(**OPTIONAL_ARGS)
    password = fields.String(**OPTIONAL_ARGS)
    database = fields.String(**OPTIONAL_ARGS)
    timeout = fields.Integer(**OPTIONAL_ARGS)
    login_timeout = fields.Integer(**OPTIONAL_ARGS)
    charset = fields.String(**OPTIONAL_ARGS)
    as_dict = fields.Boolean(**OPTIONAL_ARGS)
    host = fields.String(**OPTIONAL_ARGS)
    appname = fields.String(**OPTIONAL_ARGS)
    port = fields.String(**OPTIONAL_ARGS)
    encryption = fields.String(**OPTIONAL_ARGS)
    read_only = fields.Boolean(**OPTIONAL_ARGS)
    conn_properties = fields.List(fields.String(), **OPTIONAL_ARGS)
    autocommit = fields.Boolean(**OPTIONAL_ARGS)
    tds_version = fields.String(**OPTIONAL_ARGS)
    use_datetime2 = fields.Boolean(**OPTIONAL_ARGS)
    arraysize = fields.Integer(**OPTIONAL_ARGS)


class ConfigArgsSchema(Schema):
    db_type = fields.String(**OPTIONAL_ARGS)
    connections_file_path = fields.Raw(**OPTIONAL_ARGS)
    subcommand = fields.String(**OPTIONAL_ARGS)
    config_folder = fields.String(**OPTIONAL_ARGS)
    config_file_name = fields.String(**OPTIONAL_ARGS)
    config_file_path = fields.Raw(**OPTIONAL_ARGS)
    root_folder = fields.String(**OPTIONAL_ARGS)
    modules_folder = fields.String(**OPTIONAL_ARGS)
    config_vars = fields.Dict(
        keys=fields.String(), values=fields.Raw(), **OPTIONAL_ARGS
    )
    secrets = fields.Raw(**OPTIONAL_ARGS)
    verbose = fields.Boolean(**OPTIONAL_ARGS)
    change_history_table = fields.String(**OPTIONAL_ARGS)
    create_change_history_table = fields.Boolean(**OPTIONAL_ARGS)
    autocommit = fields.Boolean(**OPTIONAL_ARGS)
    dry_run = fields.Boolean(**OPTIONAL_ARGS)
    script_path = fields.String(**OPTIONAL_ARGS)
    log_level = fields.Integer(**OPTIONAL_ARGS)
    query_tag = fields.String(**OPTIONAL_ARGS)
    batch_id = fields.String(**OPTIONAL_ARGS)
    force = fields.Boolean(**OPTIONAL_ARGS)
    from_version = fields.String(**OPTIONAL_ARGS)
    to_version = fields.String(**OPTIONAL_ARGS)

    @validates_schema()
    def validate_args(self, data, **kwargs):
        db_type = data.get("db_type")
        connections_file_path = data.get("connections_file_path")
        subcommand = data.get("subcommand")
        batch_id = data.get("batch_id")
        script_path = data.get("script_path")
        force = data.get("force")
        from_version = data.get("from_version")
        to_version = data.get("to_version")
        error_messages = []

        if subcommand == SubCommand.DEPLOY or subcommand == SubCommand.ROLLBACK:
            if not db_type:
                error_messages.append(
                    "'db_type' config is missing for deploy command. "
                    "Please specify either in CLI parameters or YAML config file"
                )
            if not connections_file_path:
                error_messages.append(
                    "'connections_file_path' config is missing for deploy command. "
                    "Please specify either in CLI parameters or YAML config file"
                )

            if subcommand == SubCommand.DEPLOY and force:
                if not from_version or not to_version:
                    error_messages.append(
                        "Aggressive deployment requires from_version and to_version "
                        "of versioned scripts to be defined"
                    )

            if subcommand == SubCommand.ROLLBACK:
                if not batch_id:
                    error_messages.append(
                        "'batch_id' config is missing for rollback command. "
                        "Please specify in CLI parameters"
                    )
        elif subcommand == SubCommand.RENDER:
            if not script_path:
                error_messages.append(
                    "'script_path' config is missing for render command. "
                    "Please specify in CLI parameters"
                )
        else:
            error_messages.append(f"'subcommand' should be one of {SubCommand.items()}")

        if error_messages:
            raise exceptions.ValidationError(message=error_messages)
