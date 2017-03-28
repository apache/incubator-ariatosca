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

#TODO handle
if __name__ == '__main__' and __package__ is None:
    import aria.cli
    __package__ = 'aria.cli'

# from . import env
from . import logger
from .cli import aria
from .commands import service_templates
from .commands import node_templates
from .commands import services
from .commands import nodes
from .commands import workflows
from .commands import executions
from .commands import plugins
from .. import install_aria_extensions


@aria.group(name='aria')
@aria.options.verbose(expose_value=True)
@aria.options.version
def _aria(verbose):
    """ARIA's Command Line Interface

    To activate bash-completion. Run: `eval "$(_ARIA_COMPLETE=source aria)"`

    ARIA's working directory resides by default in ~/.aria. To change it, set
    the environment variable `ARIA_WORKDIR` to something else (e.g. /tmp/).
    """
    aria.set_cli_except_hook(verbose)


def _register_commands():
    """
    Register the CLI's commands.
    """

    _aria.add_command(service_templates.service_templates)
    _aria.add_command(node_templates.node_templates)
    _aria.add_command(services.services)
    _aria.add_command(nodes.nodes)
    _aria.add_command(workflows.workflows)
    _aria.add_command(executions.executions)
    _aria.add_command(plugins.plugins)


_register_commands()


def main():
    install_aria_extensions()
    _aria()


if __name__ == '__main__':
    main()
