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

import itertools

from ...utils.collections import StrictDict, prune, OrderedDict
from ...utils.formatting import as_raw
from ...utils.console import puts
from .types import TypeHierarchy
from .utils import generate_id_string


class IdType(object):
    LOCAL_SERIAL = 0
    """
    Locally unique serial ID: a running integer.
    """

    LOCAL_RANDOM = 1
    """
    Locally unique ID: 6 random safe characters.
    """

    UNIVERSAL_RANDOM = 2
    """
    Universally unique ID (UUID): 25 random safe characters.
    """


class ModelingContext(object):
    """
    Properties:

    * :code:`model`: The generated service model
    * :code:`instance`: The generated service instance
    * :code:`node_id_format`: Format for node instance IDs 
    * :code:`id_type`: Type of IDs to use for instances
    * :code:`id_max_length`: Maximum allowed instance ID length
    * :code:`inputs`: Dict of inputs values
    * :code:`node_types`: The generated hierarchy of node types
    * :code:`group_types`: The generated hierarchy of group types
    * :code:`capability_types`: The generated hierarchy of capability types
    * :code:`relationship_types`: The generated hierarchy of relationship types
    * :code:`policy_types`: The generated hierarchy of policy types
    * :code:`policy_trigger_types`: The generated hierarchy of policy trigger types
    * :code:`artifact_types`: The generated hierarchy of artifact types
    * :code:`interface_types`: The generated hierarchy of interface types
    """

    def __init__(self):
        self.model = None
        self.instance = None
        self.node_id_format = '{template}_{id}'
        #self.id_type = IdType.LOCAL_SERIAL
        #self.id_type = IdType.LOCAL_RANDOM
        self.id_type = IdType.UNIVERSAL_RANDOM
        self.id_max_length = 63 # See: http://www.faqs.org/rfcs/rfc1035.html
        self.inputs = StrictDict(key_class=basestring)
        self.node_types = TypeHierarchy()
        self.group_types = TypeHierarchy()
        self.capability_types = TypeHierarchy()
        self.relationship_types = TypeHierarchy()
        self.policy_types = TypeHierarchy()
        self.policy_trigger_types = TypeHierarchy()
        self.artifact_types = TypeHierarchy()
        self.interface_types = TypeHierarchy()

        self._serial_id_counter = itertools.count(1)
        self._locally_unique_ids = set()

    def generate_node_id(self, template_name):
        return self.node_id_format.format(
            template=template_name,
            id=self.generate_id())

    def generate_id(self):
        if self.id_type == IdType.LOCAL_SERIAL:
            return self._serial_id_counter.next()

        elif self.id_type == IdType.LOCAL_RANDOM:
            the_id = generate_id_string(6)
            while the_id in self._locally_unique_ids:
                the_id = generate_id_string(6)
            self._locally_unique_ids.add(the_id)
            return the_id

        return generate_id_string()

    def set_input(self, name, value):
        self.inputs[name] = value
        # TODO: coerce to validate type

    @property
    def types_as_raw(self):
        return OrderedDict((
            ('node_types', as_raw(self.node_types)),
            ('group_types', as_raw(self.group_types)),
            ('capability_types', as_raw(self.capability_types)),
            ('relationship_types', as_raw(self.relationship_types)),
            ('policy_types', as_raw(self.policy_types)),
            ('policy_trigger_types', as_raw(self.policy_trigger_types)),
            ('artifact_types', as_raw(self.artifact_types)),
            ('interface_types', as_raw(self.interface_types))))

    @property
    def model_as_raw(self):
        raw = self.model.as_raw
        prune(raw)
        return raw

    @property
    def instance_as_raw(self):
        raw = self.instance.as_raw
        prune(raw)
        return raw

    def dump_types(self, context):
        if self.node_types.children:
            puts('Node types:')
            self.node_types.dump(context)
        if self.group_types.children:
            puts('Group types:')
            self.group_types.dump(context)
        if self.capability_types.children:
            puts('Capability types:')
            self.capability_types.dump(context)
        if self.relationship_types.children:
            puts('Relationship types:')
            self.relationship_types.dump(context)
        if self.policy_types.children:
            puts('Policy types:')
            self.policy_types.dump(context)
        if self.policy_trigger_types.children:
            puts('Policy trigger types:')
            self.policy_trigger_types.dump(context)
        if self.artifact_types.children:
            puts('Artifact types:')
            self.artifact_types.dump(context)
        if self.interface_types.children:
            puts('Interface types:')
            self.interface_types.dump(context)
