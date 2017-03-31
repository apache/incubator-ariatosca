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

from threading import RLock

from ..modeling import models
from ..orchestrator.decorators import operation
from ..utils.collections import OrderedDict
from ..utils.console import puts, Colored
from ..utils.formatting import safe_repr


_TERMINAL_LOCK = RLock()


def convert_to_dry(service):
    """
    Converts all operations on the service (on workflows, node interfaces, and relationship
    interfaces) to run dryly.
    """

    for workflow in service.workflows.itervalues():
        convert_operation_to_dry(workflow)

    for node in service.nodes.itervalues():
        for interface in node.interfaces.itervalues():
            for oper in interface.operations.itervalues():
                convert_operation_to_dry(oper)
        for relationship in node.outbound_relationships:
            for interface in relationship.interfaces.itervalues():
                for oper in interface.operations.itervalues():
                    convert_operation_to_dry(oper)


def convert_operation_to_dry(oper):
    """
    Converts a single :class:`Operation` to run dryly.
    """

    plugin = oper.plugin_specification.name \
        if oper.plugin_specification is not None else None
    if oper.inputs is None:
        oper.inputs = OrderedDict()
    oper.inputs['_implementation'] = models.Parameter(name='_implementation',
                                                      type_name='string',
                                                      value=oper.implementation)
    oper.inputs['_plugin'] = models.Parameter(name='_plugin',
                                              type_name='string',
                                              value=plugin)
    oper.implementation = '{0}.{1}'.format(__name__, 'dry_operation')
    oper.plugin_specification = None


@operation
def dry_operation(ctx, _plugin, _implementation, **kwargs):
    """
    The dry operation simply prints out information about the operation to the console.
    """

    with _TERMINAL_LOCK:
        print ctx.name
        if hasattr(ctx, 'relationship'):
            puts('> Relationship: {0} -> {1}'.format(
                Colored.red(ctx.relationship.source_node.name),
                Colored.red(ctx.relationship.target_node.name)))
        else:
            puts('> Node: {0}'.format(Colored.red(ctx.node.name)))
        puts('  Operation: {0}'.format(Colored.green(ctx.name)))
        _dump_implementation(_plugin, _implementation)


def _dump_implementation(plugin, implementation):
    if plugin:
        puts('  Plugin: {0}'.format(Colored.magenta(plugin, bold=True)))
    if implementation:
        puts('  Implementation: {0}'.format(Colored.magenta(safe_repr(implementation))))
