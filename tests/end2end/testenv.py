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

import sys

import pytest
import sh


@pytest.fixture
def testenv(tmpdir, request, monkeypatch):
    test_name = request.node.name
    workdir = str(tmpdir)

    # setting the workdir environment variable for the CLI to work with
    monkeypatch.setenv('ARIA_WORKDIR', workdir)
    return TestEnvironment(workdir, test_name)


class TestEnvironment(object):

    def __init__(self, workdir, test_name):
        self.workdir = workdir
        self.test_name = test_name

        self.cli = self._get_cli()
        env = self._get_aria_env()
        self.model_storage = env.model_storage
        self.resource_storage = env.resource_storage
        self.plugin_manager = env.plugin_manager

    def install_service(self, service_template_path, dry=False, service_template_name=None,
                        service_name=None):
        service_template_name = service_template_name or self.test_name
        service_name = service_name or self.test_name

        self.cli.service_templates.store(service_template_path, service_template_name)
        self.cli.services.create(service_name, service_template_name=service_template_name)
        self.execute_workflow(service_name, 'install', dry=dry)
        return service_name

    def uninstall_service(self, service_name=None, service_template_name=None, dry=False,
                          force_service_delete=False):
        service_name = service_name or self.test_name
        self.execute_workflow(service_name, 'uninstall', dry=dry)
        self.cli.services.delete(service_name, force=force_service_delete)
        self.cli.service_templates.delete(service_template_name or self.test_name)

    def execute_workflow(self, service_name, workflow_name, dry=False):
        self.cli.executions.start(workflow_name, service_name=service_name, dry=dry)

    def verify_clean_storage(self):
        assert len(self.model_storage.service_template.list()) == 0
        assert len(self.model_storage.service.list()) == 0
        assert len(self.model_storage.execution.list()) == 0
        assert len(self.model_storage.node_template.list()) == 0
        assert len(self.model_storage.node.list()) == 0
        assert len(self.model_storage.log.list()) == 0

    def _get_cli(self):
        cli = sh.aria.bake(_out=sys.stdout.write, _err=sys.stderr.write)

        # the `sh` library supports underscore-dash auto-replacement for commands and option flags
        # yet not for subcommands (e.g. `aria service-templates`); The following class fixes this.
        class PatchedCli(object):
            def __getattr__(self, attr):
                if '_' in attr:
                    return cli.bake(attr.replace('_', '-'))
                return getattr(cli, attr)

            def __call__(self, *args, **kwargs):
                # this is to support the `aria` command itself (e.g. `aria --version` calls)
                return cli(*args, **kwargs)

        return PatchedCli()

    def _get_aria_env(self):
        # a somewhat hackish but most simple way of acquiring environment context such as
        # the model storage, resource storage etc.
        # note that the `ARIA_WORKDIR` environment variable must be exported before the import
        # below is used, as the import itself will initialize the `.aria` directory.
        from aria.cli import env as cli_env
        reload(cli_env)  # reloading the module in-between tests
        return cli_env.env
