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
Aria's Executors Package
Path: aria.executors

API:
    - executors - set of every executor that bin register
    - executor - executor that bin register, and have the highest priority
    - ExecutorInformation - tool to register executor
    - Process - subprocess wrapper tool
    -

Plugins:
...
"""

import os

from ..tools.plugin import plugin_installer

__all__ = (
    'executors',
    'Process',
)


executors = {}


def executor_register_callback(module):
    global executors
    register_executor_func = getattr(module, 'register_executor', None)
    for executor in register_executor_func():
        executors[executor.__name__] = executor

plugin_installer(
    path=os.path.dirname(os.path.realpath(__file__)),
    plugin_suffix='_executor',
    callback=executor_register_callback,
    package=__package__)
