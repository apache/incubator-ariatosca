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


from ... import mock

def assert_node_install_operations(operations, with_relationships=False):
    if with_relationships:
        all_operations = [
            'aria.interfaces.lifecycle.create',
            'aria.interfaces.relationship_lifecycle.preconfigure',
            'aria.interfaces.relationship_lifecycle.preconfigure',
            'aria.interfaces.lifecycle.configure',
            'aria.interfaces.relationship_lifecycle.postconfigure',
            'aria.interfaces.relationship_lifecycle.postconfigure',
            'aria.interfaces.lifecycle.start',
            'aria.interfaces.relationship_lifecycle.establish',
            'aria.interfaces.relationship_lifecycle.establish',
        ]

        for i, operation in enumerate(operations):
            assert operation.name.startswith(all_operations[i])
    else:
        for i, operation in enumerate(operations):
            assert operation.name.startswith(mock.operations.NODE_OPERATIONS_INSTALL[i])


def assert_node_uninstall_operations(operations, with_relationships=False):
    if with_relationships:
        all_operations = [
            'aria.interfaces.lifecycle.stop',
            'aria.interfaces.relationship_lifecycle.unlink',
            'aria.interfaces.relationship_lifecycle.unlink',
            'aria.interfaces.lifecycle.delete',
        ]

        for i, operation in enumerate(operations):
            assert operation.name.startswith(all_operations[i])
    else:
        for i, operation in enumerate(operations):
            assert operation.name.startswith(mock.operations.NODE_OPERATIONS_UNINSTALL[i])


def ctx_with_basic_graph():
    """
    Create the following graph in storage:
    dependency_node <------ dependent_node
    :return:
    """
    simple_context = mock.context.simple()
    dependency_node = mock.models.get_dependency_node()
    dependency_node_instance = mock.models.get_dependency_node_instance(
        dependency_node=dependency_node)

    relationship = mock.models.get_relationship(dependency_node)
    relationship_instance = mock.models.get_relationship_instance(
        relationship=relationship,
        target_instance=dependency_node_instance
    )

    dependent_node = mock.models.get_dependent_node(relationship)
    dependent_node_instance = mock.models.get_dependent_node_instance(
        dependent_node=dependent_node,
        relationship_instance=relationship_instance
    )

    simple_context.model.node.store(dependent_node)
    simple_context.model.node.store(dependency_node)
    simple_context.model.node_instance.store(dependent_node_instance)
    simple_context.model.node_instance.store(dependency_node_instance)
    simple_context.model.relationship.store(relationship)
    simple_context.model.relationship_instance.store(relationship_instance)

    return simple_context
