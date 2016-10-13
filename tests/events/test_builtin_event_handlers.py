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

import mock
import pytest

from aria.events.builtin_event_handlers import (_OperationToNodeInstanceState,
                                                _update_node_instance_state,
                                                _operation_to_node_instance_state)


OPERATIONS = [
    'cloudify.interfaces.lifecycle.create',
    'cloudify.interfaces.lifecycle.configure',
    'cloudify.interfaces.lifecycle.start',
    'cloudify.interfaces.lifecycle.stop',
    'cloudify.interfaces.lifecycle.delete',
]


class _Sender(object):
    def __init__(self, task_name):
        self.context = mock.MagicMock()
        self.task_name = task_name


def test_update_node_instance_state():
    for op in OPERATIONS:
        sender = _Sender(op)
        _update_node_instance_state(sender=sender)

        assert sender.context.storage.node_instance.store.called
        assert sender.context.storage.node_instance.store.call_args[0][0].state == \
               _operation_to_node_instance_state[op]

    sender = _Sender('non_existing_op')
    assert _update_node_instance_state(sender=sender) is None


def test_operation_to_node_instance_state():
    custom_op_to_node_state = _OperationToNodeInstanceState(dict(custom_op= 'CUSTOM_OP'))

    assert custom_op_to_node_state['custom_op'] == 'CUSTOM_OP'
    assert custom_op_to_node_state['custom_op_cached'] == 'CUSTOM_OP'
    with pytest.raises(KeyError):
        assert custom_op_to_node_state['non_existing_key']
