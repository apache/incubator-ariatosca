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

import click.testing

import aria.cli.commands as commands


def invoke(command_string):
    command_list = command_string.split()
    command, sub, args = command_list[0], command_list[1], command_list[2:]
    runner = click.testing.CliRunner()
    outcome = runner.invoke(getattr(
        getattr(commands, command), sub), args)
    return outcome
