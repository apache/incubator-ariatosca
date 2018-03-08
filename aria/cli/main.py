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

"""
Executable entry point into the CLI.
"""

from aria import install_aria_extensions
from aria.cli import commands
from aria.cli.core import aria


@aria.group(name='aria')
@aria.options.verbose()
@aria.options.version
def _aria():
    """
    ARIA's Command Line Interface.

    To activate bash-completion run::

        eval "$(_ARIA_COMPLETE=source aria)"

    ARIA's working directory resides by default in "~/.aria". To change it, set the environment
    variable ARIA_WORKDIR to something else (e.g. "/tmp/").
    """
    aria.set_cli_except_hook()


def _register_commands():
    """
    Register the CLI's commands.
    """

    _aria.add_command(commands.type_definitions.type_definitions)
    _aria.add_command(commands.service_templates.service_templates)
    _aria.add_command(commands.node_templates.node_templates)
    _aria.add_command(commands.services.services)
    _aria.add_command(commands.nodes.nodes)
    _aria.add_command(commands.workflows.workflows)
    _aria.add_command(commands.executions.executions)
    _aria.add_command(commands.plugins.plugins)
    _aria.add_command(commands.logs.logs)
    _aria.add_command(commands.reset.reset)


def main():
    install_aria_extensions()
    _register_commands()
    _aria()


if __name__ == '__main__':
    main()
