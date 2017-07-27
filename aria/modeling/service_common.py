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
ARIA modeling service common module
"""

# pylint: disable=no-self-argument, no-member, abstract-method

from sqlalchemy import (
    Column,
    Text,
    Boolean
)
from sqlalchemy.ext.declarative import declared_attr

from ..utils import (
    collections,
    formatting
)
from .mixins import InstanceModelMixin, TemplateModelMixin, ParameterMixin
from . import relationship


class OutputBase(ParameterMixin):
    """
    Output parameter or declaration for an output parameter.
    """

    __tablename__ = 'output'

    # region many_to_one relationships

    @declared_attr
    def service_template(cls):
        """
        Containing service template (can be ``None``).

        :type: :class:`ServiceTemplate`
        """
        return relationship.many_to_one(cls, 'service_template')

    @declared_attr
    def service(cls):
        """
        Containing service (can be ``None``).

        :type: :class:`ServiceTemplate`
        """
        return relationship.many_to_one(cls, 'service')

    # endregion

    # region foreign keys

    @declared_attr
    def service_template_fk(cls):
        return relationship.foreign_key('service_template', nullable=True)

    @declared_attr
    def service_fk(cls):
        return relationship.foreign_key('service', nullable=True)

    # endregion


class InputBase(ParameterMixin):
    """
    Input parameter or declaration for an input parameter.
    """

    __tablename__ = 'input'

    required = Column(Boolean, doc="""
    Is the input mandatory.

    :type: :obj:`bool`
    """)

    @classmethod
    def wrap(cls, name, value, description=None, required=True):  # pylint: disable=arguments-differ
        input = super(InputBase, cls).wrap(name, value, description)
        input.required = required
        return input

    # region many_to_one relationships

    @declared_attr
    def service_template(cls):
        """
        Containing service template (can be ``None``).

        :type: :class:`ServiceTemplate`
        """
        return relationship.many_to_one(cls, 'service_template')

    @declared_attr
    def service(cls):
        """
        Containing service (can be ``None``).

        :type: :class:`Service`
        """
        return relationship.many_to_one(cls, 'service')

    @declared_attr
    def interface(cls):
        """
        Containing interface (can be ``None``).

        :type: :class:`Interface`
        """
        return relationship.many_to_one(cls, 'interface')

    @declared_attr
    def operation(cls):
        """
        Containing operation (can be ``None``).

        :type: :class:`Operation`
        """
        return relationship.many_to_one(cls, 'operation')

    @declared_attr
    def interface_template(cls):
        """
        Containing interface template (can be ``None``).

        :type: :class:`InterfaceTemplate`
        """
        return relationship.many_to_one(cls, 'interface_template')

    @declared_attr
    def operation_template(cls):
        """
        Containing operation template (can be ``None``).

        :type: :class:`OperationTemplate`
        """
        return relationship.many_to_one(cls, 'operation_template')

    @declared_attr
    def execution(cls):
        """
        Containing execution (can be ``None``).

        :type: :class:`Execution`
        """
        return relationship.many_to_one(cls, 'execution')

    # endregion

    # region foreign keys

    @declared_attr
    def service_template_fk(cls):
        return relationship.foreign_key('service_template', nullable=True)

    @declared_attr
    def service_fk(cls):
        return relationship.foreign_key('service', nullable=True)

    @declared_attr
    def interface_fk(cls):
        return relationship.foreign_key('interface', nullable=True)

    @declared_attr
    def operation_fk(cls):
        return relationship.foreign_key('operation', nullable=True)

    @declared_attr
    def interface_template_fk(cls):
        return relationship.foreign_key('interface_template', nullable=True)

    @declared_attr
    def operation_template_fk(cls):
        return relationship.foreign_key('operation_template', nullable=True)

    @declared_attr
    def execution_fk(cls):
        return relationship.foreign_key('execution', nullable=True)

    @declared_attr
    def task_fk(cls):
        return relationship.foreign_key('task', nullable=True)

    # endregion


class ConfigurationBase(ParameterMixin):
    """
    Configuration parameter.
    """

    __tablename__ = 'configuration'

    # region many_to_one relationships

    @declared_attr
    def operation_template(cls):
        """
        Containing operation template (can be ``None``).

        :type: :class:`OperationTemplate`
        """
        return relationship.many_to_one(cls, 'operation_template')

    @declared_attr
    def operation(cls):
        """
        Containing operation (can be ``None``).

        :type: :class:`Operation`
        """
        return relationship.many_to_one(cls, 'operation')

    # endregion

    # region foreign keys

    @declared_attr
    def operation_template_fk(cls):
        return relationship.foreign_key('operation_template', nullable=True)

    @declared_attr
    def operation_fk(cls):
        return relationship.foreign_key('operation', nullable=True)

    # endregion


class PropertyBase(ParameterMixin):
    """
    Property parameter or declaration for a property parameter.
    """

    __tablename__ = 'property'

    # region many_to_one relationships

    @declared_attr
    def node_template(cls):
        """
        Containing node template (can be ``None``).

        :type: :class:`NodeTemplate`
        """
        return relationship.many_to_one(cls, 'node_template')

    @declared_attr
    def group_template(cls):
        """
        Containing group template (can be ``None``).

        :type: :class:`GroupTemplate`
        """
        return relationship.many_to_one(cls, 'group_template')

    @declared_attr
    def policy_template(cls):
        """
        Containing policy template (can be ``None``).

        :type: :class:`PolicyTemplate`
        """
        return relationship.many_to_one(cls, 'policy_template')

    @declared_attr
    def relationship_template(cls):
        """
        Containing relationship template (can be ``None``).

        :type: :class:`RelationshipTemplate`
        """
        return relationship.many_to_one(cls, 'relationship_template')

    @declared_attr
    def capability_template(cls):
        """
        Containing capability template (can be ``None``).

        :type: :class:`CapabilityTemplate`
        """
        return relationship.many_to_one(cls, 'capability_template')

    @declared_attr
    def artifact_template(cls):
        """
        Containing artifact template (can be ``None``).

        :type: :class:`ArtifactTemplate`
        """
        return relationship.many_to_one(cls, 'artifact_template')

    @declared_attr
    def node(cls):
        """
        Containing node (can be ``None``).

        :type: :class:`Node`
        """
        return relationship.many_to_one(cls, 'node')

    @declared_attr
    def group(cls):
        """
        Containing group (can be ``None``).

        :type: :class:`Group`
        """
        return relationship.many_to_one(cls, 'group')

    @declared_attr
    def policy(cls):
        """
        Containing policy (can be ``None``).

        :type: :class:`Policy`
        """
        return relationship.many_to_one(cls, 'policy')

    @declared_attr
    def relationship(cls):
        """
        Containing relationship (can be ``None``).

        :type: :class:`Relationship`
        """
        return relationship.many_to_one(cls, 'relationship')

    @declared_attr
    def capability(cls):
        """
        Containing capability (can be ``None``).

        :type: :class:`Capability`
        """
        return relationship.many_to_one(cls, 'capability')

    @declared_attr
    def artifact(cls):
        """
        Containing artifact (can be ``None``).

        :type: :class:`Artifact`
        """
        return relationship.many_to_one(cls, 'artifact')

    # endregion

    # region foreign keys

    @declared_attr
    def node_template_fk(cls):
        return relationship.foreign_key('node_template', nullable=True)

    @declared_attr
    def group_template_fk(cls):
        return relationship.foreign_key('group_template', nullable=True)

    @declared_attr
    def policy_template_fk(cls):
        return relationship.foreign_key('policy_template', nullable=True)

    @declared_attr
    def relationship_template_fk(cls):
        return relationship.foreign_key('relationship_template', nullable=True)

    @declared_attr
    def capability_template_fk(cls):
        return relationship.foreign_key('capability_template', nullable=True)

    @declared_attr
    def artifact_template_fk(cls):
        return relationship.foreign_key('artifact_template', nullable=True)

    @declared_attr
    def node_fk(cls):
        return relationship.foreign_key('node', nullable=True)

    @declared_attr
    def group_fk(cls):
        return relationship.foreign_key('group', nullable=True)

    @declared_attr
    def policy_fk(cls):
        return relationship.foreign_key('policy', nullable=True)

    @declared_attr
    def relationship_fk(cls):
        return relationship.foreign_key('relationship', nullable=True)

    @declared_attr
    def capability_fk(cls):
        return relationship.foreign_key('capability', nullable=True)

    @declared_attr
    def artifact_fk(cls):
        return relationship.foreign_key('artifact', nullable=True)

    # endregion


class AttributeBase(ParameterMixin):
    """
    Attribute parameter or declaration for an attribute parameter.
    """

    __tablename__ = 'attribute'

    # region many_to_one relationships

    @declared_attr
    def node_template(cls):
        """
        Containing node template (can be ``None``).

        :type: :class:`NodeTemplate`
        """
        return relationship.many_to_one(cls, 'node_template')

    @declared_attr
    def node(cls):
        """
        Containing node (can be ``None``).

        :type: :class:`Node`
        """
        return relationship.many_to_one(cls, 'node')

    # endregion

    # region foreign keys

    @declared_attr
    def node_template_fk(cls):
        """For Attribute many-to-one to NodeTemplate"""
        return relationship.foreign_key('node_template', nullable=True)

    @declared_attr
    def node_fk(cls):
        """For Attribute many-to-one to Node"""
        return relationship.foreign_key('node', nullable=True)

    # endregion


class TypeBase(InstanceModelMixin):
    """
    Type and its children. Can serve as the root for a type hierarchy.
    """

    __tablename__ = 'type'

    __private_fields__ = ('parent_type_fk',)

    variant = Column(Text, nullable=False)

    description = Column(Text, doc="""
    Human-readable description.

    :type: :obj:`basestring`
    """)

    _role = Column(Text, name='role')

    # region one_to_one relationships

    @declared_attr
    def parent(cls):
        """
        Parent type (will be ``None`` for the root of a type hierarchy).

        :type: :class:`Type`
        """
        return relationship.one_to_one_self(cls, 'parent_type_fk')

    # endregion

    # region one_to_many relationships

    @declared_attr
    def children(cls):
        """
        Children.

        :type: [:class:`Type`]
        """
        return relationship.one_to_many(cls, other_fk='parent_type_fk', self=True)

    # endregion

    # region foreign keys

    @declared_attr
    def parent_type_fk(cls):
        """For Type one-to-many to Type"""
        return relationship.foreign_key('type', nullable=True)

    # endregion

    @property
    def role(self):
        def get_role(the_type):
            if the_type is None:
                return None
            elif the_type._role is None:
                return get_role(the_type.parent)
            return the_type._role

        return get_role(self)

    @role.setter
    def role(self, value):
        self._role = value

    def is_descendant(self, base_name, name):
        base = self.get_descendant(base_name)
        if base is not None:
            if base.get_descendant(name) is not None:
                return True
        return False

    def get_descendant(self, name):
        if self.name == name:
            return self
        for child in self.children:
            found = child.get_descendant(name)
            if found is not None:
                return found
        return None

    def iter_descendants(self):
        for child in self.children:
            yield child
            for descendant in child.iter_descendants():
                yield descendant

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('description', self.description),
            ('role', self.role)))

    @property
    def as_raw_all(self):
        types = []
        self._append_raw_children(types)
        return types

    def _append_raw_children(self, types):
        for child in self.children:
            raw_child = formatting.as_raw(child)
            raw_child['parent'] = self.name
            types.append(raw_child)
            child._append_raw_children(types)

    @property
    def hierarchy(self):
        """
        Type hierarchy as a list beginning with this type and ending in the root.

        :type: [:class:`Type`]
        """
        return [self] + (self.parent.hierarchy if self.parent else [])


class MetadataBase(TemplateModelMixin):
    """
    Custom values associated with the service.

    This model is used by both service template and service instance elements.

    :ivar name: name
    :vartype name: basestring
    :ivar value: value
    :vartype value: basestring
    """

    __tablename__ = 'metadata'

    value = Column(Text)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('value', self.value)))
