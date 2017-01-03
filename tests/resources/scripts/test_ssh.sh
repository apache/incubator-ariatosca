#!/bin/bash

set -u
set -e

test_run_script_basic() {
    ctx node-instance runtime-properties test_value $test_value
}

test_run_script_as_sudo() {
    mkdir -p /opt/test_dir
}

test_run_script_default_base_dir() {
    ctx node-instance runtime-properties work_dir $PWD
}

test_run_script_with_hide() {
    true
}

test_run_script_process_config() {
    ctx node-instance runtime-properties env_value $test_value_env
    ctx node-instance runtime-properties bash_version $BASH_VERSION
    ctx node-instance runtime-properties arg1_value $1
    ctx node-instance runtime-properties arg2_value $2
    ctx node-instance runtime-properties cwd $PWD
    ctx node-instance runtime-properties ctx_path $(which ctx)
}

test_run_script_command_prefix() {
    ctx node-instance runtime-properties dollar_dash $-
}

test_run_script_reuse_existing_ctx_1() {
    ctx node-instance runtime-properties test_value1 $test_value1
}

test_run_script_reuse_existing_ctx_2() {
    ctx node-instance runtime-properties test_value2 $test_value2
}

test_run_script_download_resource_plain() {
    local destination=$(mktemp)
    ctx download-resource ${destination} test_resource
    ctx node-instance runtime-properties test_value "$(cat ${destination})"
}

test_run_script_download_resource_and_render() {
    local destination=$(mktemp)
    ctx download-resource-and-render ${destination} test_resource
    ctx node-instance runtime-properties test_value "$(cat ${destination})"
}

test_run_script_inputs_as_env_variables_no_override() {
    ctx node-instance runtime-properties test_value "$custom_env_var"
}

test_run_script_inputs_as_env_variables_process_env_override() {
    ctx node-instance runtime-properties test_value "$custom_env_var"
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
