# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import random
import string
import tempfile
import StringIO

import fabric.api
import fabric.context_managers
import fabric.contrib.files

from .. import constants
from .. import exceptions
from .. import common
from .. import ctx_proxy
from . import tunnel


_PROXY_CLIENT_PATH = ctx_proxy.client.__file__
if _PROXY_CLIENT_PATH.endswith('.pyc'):
    _PROXY_CLIENT_PATH = _PROXY_CLIENT_PATH[:-1]


def run_commands(ctx, commands, fabric_env, use_sudo, hide_output, **_):
    """Runs the provider 'commands' in sequence

    :param commands: a list of commands to run
    :param fabric_env: fabric configuration
    """
    with fabric.api.settings(_hide_output(ctx, groups=hide_output),
                             **_fabric_env(ctx, fabric_env, warn_only=True)):
        for command in commands:
            ctx.logger.info('Running command: {0}'.format(command))
            run = fabric.api.sudo if use_sudo else fabric.api.run
            result = run(command)
            if result.failed:
                raise exceptions.ProcessException(
                    command=result.command,
                    exit_code=result.return_code,
                    stdout=result.stdout,
                    stderr=result.stderr)


def run_script(ctx, script_path, fabric_env, process, use_sudo, hide_output, **kwargs):
    process = process or {}
    paths = _Paths(base_dir=process.get('base_dir', constants.DEFAULT_BASE_DIR),
                   local_script_path=common.download_script(ctx, script_path))
    with fabric.api.settings(_hide_output(ctx, groups=hide_output),
                             **_fabric_env(ctx, fabric_env, warn_only=False)):
        # the remote host must have the ctx before running any fabric scripts
        if not fabric.contrib.files.exists(paths.remote_ctx_path):
            # there may be race conditions with other operations that
            # may be running in parallel, so we pass -p to make sure
            # we get 0 exit code if the directory already exists
            fabric.api.run('mkdir -p {0} && mkdir -p {1}'.format(paths.remote_scripts_dir,
                                                                 paths.remote_work_dir))
            # this file has to be present before using ctx
            fabric.api.put(_PROXY_CLIENT_PATH, paths.remote_ctx_path)
        process = common.create_process_config(
            script_path=paths.remote_script_path,
            process=process,
            operation_kwargs=kwargs,
            quote_json_env_vars=True)
        fabric.api.put(paths.local_script_path, paths.remote_script_path)
        with ctx_proxy.server.CtxProxy(ctx, _patch_ctx) as proxy:
            local_port = proxy.port
            with fabric.context_managers.cd(process.get('cwd', paths.remote_work_dir)):  # pylint: disable=not-context-manager
                with tunnel.remote(ctx, local_port=local_port) as remote_port:
                    local_socket_url = proxy.socket_url
                    remote_socket_url = local_socket_url.replace(str(local_port), str(remote_port))
                    env_script = _write_environment_script_file(
                        process=process,
                        paths=paths,
                        local_socket_url=local_socket_url,
                        remote_socket_url=remote_socket_url)
                    fabric.api.put(env_script, paths.remote_env_script_path)
                    try:
                        command = 'source {0} && {1}'.format(paths.remote_env_script_path,
                                                             process['command'])
                        run = fabric.api.sudo if use_sudo else fabric.api.run
                        run(command)
                    except exceptions.TaskException:
                        return common.check_error(ctx, reraise=True)
            return common.check_error(ctx)


def _patch_ctx(ctx):
    common.patch_ctx(ctx)
    original_download_resource = ctx.download_resource
    original_download_resource_and_render = ctx.download_resource_and_render

    def _download_resource(func, destination, **kwargs):
        handle, temp_local_path = tempfile.mkstemp()
        os.close(handle)
        try:
            func(destination=temp_local_path, **kwargs)
            return fabric.api.put(temp_local_path, destination)
        finally:
            os.remove(temp_local_path)

    def download_resource(destination, path=None):
        _download_resource(
            func=original_download_resource,
            destination=destination,
            path=path)
    ctx.download_resource = download_resource

    def download_resource_and_render(destination, path=None, variables=None):
        _download_resource(
            func=original_download_resource_and_render,
            destination=destination,
            path=path,
            variables=variables)
    ctx.download_resource_and_render = download_resource_and_render


def _hide_output(ctx, groups):
    """ Hides Fabric's output for every 'entity' in `groups` """
    groups = set(groups or [])
    if not groups.issubset(constants.VALID_FABRIC_GROUPS):
        ctx.task.abort('`hide_output` must be a subset of {0} (Provided: {1})'
                       .format(', '.join(constants.VALID_FABRIC_GROUPS), ', '.join(groups)))
    return fabric.api.hide(*groups)


def _fabric_env(ctx, fabric_env, warn_only):
    """Prepares fabric environment variables configuration"""
    ctx.logger.debug('Preparing fabric environment...')
    env = constants.FABRIC_ENV_DEFAULTS.copy()
    env.update(fabric_env or {})
    env.setdefault('warn_only', warn_only)
    if 'host_string' not in env:
        env['host_string'] = ctx.task.runs_on.ip
    # validations
    if not env.get('host_string'):
        ctx.task.abort('`host_string` not supplied and ip cannot be deduced automatically')
    if not (env.get('password') or env.get('key_filename') or env.get('key')):
        ctx.task.abort(
            'Access credentials not supplied '
            '(you must supply at least one of `key_filename`, `key` or `password`)')
    if not env.get('user'):
        ctx.task.abort('`user` not supplied')
    ctx.logger.debug('Environment prepared successfully')
    return env


def _write_environment_script_file(process, paths, local_socket_url, remote_socket_url):
    env_script = StringIO.StringIO()
    env = process['env']
    env['PATH'] = '{0}:$PATH'.format(paths.remote_ctx_dir)
    env['PYTHONPATH'] = '{0}:$PYTHONPATH'.format(paths.remote_ctx_dir)
    env_script.write('chmod +x {0}\n'.format(paths.remote_script_path))
    env_script.write('chmod +x {0}\n'.format(paths.remote_ctx_path))
    env.update({
        ctx_proxy.client.CTX_SOCKET_URL: remote_socket_url,
        'LOCAL_{0}'.format(ctx_proxy.client.CTX_SOCKET_URL): local_socket_url
    })
    for key, value in env.iteritems():
        env_script.write('export {0}={1}\n'.format(key, value))
    return env_script


class _Paths(object):

    def __init__(self, base_dir, local_script_path):
        self.local_script_path = local_script_path
        self.remote_ctx_dir = base_dir
        self.base_script_path = os.path.basename(self.local_script_path)
        self.remote_ctx_path = '{0}/ctx'.format(self.remote_ctx_dir)
        self.remote_scripts_dir = '{0}/scripts'.format(self.remote_ctx_dir)
        self.remote_work_dir = '{0}/work'.format(self.remote_ctx_dir)
        random_suffix = ''.join(random.choice(string.ascii_lowercase + string.digits)
                                for _ in range(8))
        remote_path_suffix = '{0}-{1}'.format(self.base_script_path, random_suffix)
        self.remote_env_script_path = '{0}/env-{1}'.format(self.remote_scripts_dir,
                                                           remote_path_suffix)
        self.remote_script_path = '{0}/{1}'.format(self.remote_scripts_dir, remote_path_suffix)
