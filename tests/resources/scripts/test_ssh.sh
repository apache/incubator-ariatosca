#!/bin/bash

set -u
set -e

test_run_script_basic() {
    ctx node attributes test_value $test_value
}

test_run_script_as_sudo() {
    mkdir -p /opt/test_dir
}

test_run_script_default_base_dir() {
    ctx node attributes work_dir $PWD
}

test_run_script_with_hide() {
    true
}

test_run_script_process_config() {
    ctx node attributes env_value $test_value_env
    ctx node attributes bash_version $BASH_VERSION
    ctx node attributes arg1_value $1
    ctx node attributes arg2_value $2
    ctx node attributes cwd $PWD
    ctx node attributes ctx_path $(which ctx)
}

test_run_script_command_prefix() {
    ctx node attributes dollar_dash $-
}

test_run_script_reuse_existing_ctx_1() {
    ctx node attributes test_value1 $test_value1
}

test_run_script_reuse_existing_ctx_2() {
    ctx node attributes test_value2 $test_value2
}

test_run_script_download_resource_plain() {
    local destination=$(mktemp)
    ctx download-resource ${destination} test_resource
    ctx node attributes test_value "$(cat ${destination})"
}

test_run_script_download_resource_and_render() {
    local destination=$(mktemp)
    ctx download-resource-and-render ${destination} test_resource
    ctx node attributes test_value "$(cat ${destination})"
}

test_run_script_inputs_as_env_variables_no_override() {
    ctx node attributes test_value "$custom_env_var"
}

test_run_script_inputs_as_env_variables_process_env_override() {
    ctx node attributes test_value "$custom_env_var"
}

test_run_script_error_in_script() {
    ctx property-that-does-not-exist
}

test_run_script_abort_immediate() {
    ctx task abort abort-message
}

test_run_script_retry() {
    ctx task retry retry-message
}

test_run_script_abort_error_ignored_by_script() {
    set +e
    ctx task abort abort-message
}

# Injected by test
${test_operation} $@
