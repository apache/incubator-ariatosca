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

from aria.orchestrator import operation
from . import local as local_operations
from .ssh import operations as ssh_operations


@operation
def run_script_locally(ctx,
                       script_path,
                       process=None,
                       **kwargs):
    return local_operations.run_script(
        ctx=ctx,
        script_path=script_path,
        process=process,
        **kwargs)


@operation
def run_script_with_ssh(ctx,
                        script_path,
                        fabric_env=None,
                        process=None,
                        use_sudo=False,
                        hide_output=None,
                        **kwargs):
    return ssh_operations.run_script(
        ctx=ctx,
        script_path=script_path,
        fabric_env=fabric_env,
        process=process,
        use_sudo=use_sudo,
        hide_output=hide_output,
        **kwargs)


@operation
def run_commands_with_ssh(ctx,
                          commands,
                          fabric_env=None,
                          use_sudo=False,
                          hide_output=None,
                          **_):
    return ssh_operations.run_commands(
        ctx=ctx,
        commands=commands,
        fabric_env=fabric_env,
        use_sudo=use_sudo,
        hide_output=hide_output)
