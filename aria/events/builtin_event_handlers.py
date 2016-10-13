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

from ..storage.models import NodeInstance
from . import start_operation_signal


class _OperationToNodeInstanceState(dict):
    def __missing__(self, key):
        for cached_key, value in self.items():
            if key.startswith(cached_key):
                return value
        raise KeyError(key)

_operation_to_node_instance_state = _OperationToNodeInstanceState({
    'cloudify.interfaces.lifecycle.create': NodeInstance.INITIALIZING,
    'cloudify.interfaces.lifecycle.configure': NodeInstance.CONFIGURING,
    'cloudify.interfaces.lifecycle.start': NodeInstance.STARTING,
    'cloudify.interfaces.lifecycle.stop': NodeInstance.STOPPING,
    'cloudify.interfaces.lifecycle.delete': NodeInstance.DELETING
})


@start_operation_signal.connect
def _update_node_instance_state(sender, **kwargs):
    try:
        next_state = _operation_to_node_instance_state[sender.task_name]
    except KeyError:
        return
    node_instance = sender.context.node_instance
    node_instance.state = next_state
    sender.context.storage.node_instance.store(node_instance)
