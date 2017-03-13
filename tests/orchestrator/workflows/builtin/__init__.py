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

from aria.orchestrator.workflows.builtin import workflows


def _assert_relationships(operations, expected_op_full_name, relationships=0):
    """

    :param operations: and iterable of operations
    :param expected_op_full_name: Note that source/target doesn't really matter since they are
    dropped
    :param relationships: the number of relationships
    :return:
    """
    expected_op_name = expected_op_full_name.rsplit('_', 1)[0]
    for _ in xrange(relationships):
        # Since the target and source operations start of the same way, we only need to retrieve the
        # suffix once
        operation = next(operations)
        relationship_id_1 = operation.actor.id
        edge1 = operation.runs_on
        _assert_cfg_interface_op(operation, expected_op_name)

        operation = next(operations)
        relationship_id_2 = operation.actor.id
        edge2 = operation.runs_on
        _assert_cfg_interface_op(operation, expected_op_name)

        assert relationship_id_1 == relationship_id_2
        assert edge1 != edge2


def assert_node_install_operations(operations, relationships=0):
    operations = iter(operations)

    _assert_std_interface_op(next(operations), workflows.NORMATIVE_CREATE)
    _assert_relationships(operations, workflows.NORMATIVE_PRE_CONFIGURE_SOURCE, relationships)
    _assert_std_interface_op(next(operations), workflows.NORMATIVE_CONFIGURE)
    _assert_relationships(operations, workflows.NORMATIVE_POST_CONFIGURE_SOURCE, relationships)
    _assert_std_interface_op(next(operations), workflows.NORMATIVE_START)
    _assert_relationships(operations, workflows.NORMATIVE_ADD_SOURCE, relationships)


def assert_node_uninstall_operations(operations, relationships=0):
    operations = iter(operations)

    _assert_std_interface_op(next(operations), workflows.NORMATIVE_STOP)
    _assert_relationships(operations, workflows.NORMATIVE_REMOVE_SOURCE, relationships)
    _assert_std_interface_op(next(operations), workflows.NORMATIVE_DELETE)


def _assert_cfg_interface_op(op, operation_name):
    # We need to remove the source/target
    assert op.operation_name.rsplit('_', 1)[0] == operation_name
    assert op.interface_name == workflows.NORMATIVE_CONFIGURE_INTERFACE


def _assert_std_interface_op(op, operation_name):
    assert op.operation_name == operation_name
    assert op.interface_name == workflows.NORMATIVE_STANDARD_INTERFACE
