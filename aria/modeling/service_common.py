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

# pylint: disable=no-self-argument, no-member, abstract-method

from sqlalchemy import (
    Column,
    Text,
)
from sqlalchemy.ext.declarative import declared_attr

from ..parser.consumption import ConsumptionContext
from ..utils import (
    collections,
    formatting,
    console,
)
from .mixins import InstanceModelMixin, TemplateModelMixin, ParameterMixin
from . import relationship


class OutputBase(ParameterMixin):

    __tablename__ = 'output'

    # region foreign keys

    @declared_attr
    def service_template_fk(cls):
        return relationship.foreign_key('service_template', nullable=True)

    @declared_attr
    def service_fk(cls):
        return relationship.foreign_key('service', nullable=True)

    # endregion

    # region many_to_one relationships

    @declared_attr
    def service_template(cls):
        return relationship.many_to_one(cls, 'service_template')

    @declared_attr
    def service(cls):
        return relationship.many_to_one(cls, 'service')

    # endregion


class InputBase(ParameterMixin):

    __tablename__ = 'input'

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

    # region many_to_one relationships

    @declared_attr
    def service_template(cls):
        return relationship.many_to_one(cls, 'service_template')

    @declared_attr
    def service(cls):
        return relationship.many_to_one(cls, 'service')

    @declared_attr
    def interface(cls):
        return relationship.many_to_one(cls, 'interface')

    @declared_attr
    def operation(cls):
        return relationship.many_to_one(cls, 'operation')

    @declared_attr
    def interface_template(cls):
        return relationship.many_to_one(cls, 'interface_template')

    @declared_attr
    def operation_template(cls):
        return relationship.many_to_one(cls, 'operation_template')

    @declared_attr
    def execution(cls):
        return relationship.many_to_one(cls, 'execution')

    # endregion


class ConfigurationBase(ParameterMixin):

    __tablename__ = 'configuration'

    # region foreign keys

    @declared_attr
    def operation_template_fk(cls):
        return relationship.foreign_key('operation_template', nullable=True)

    @declared_attr
    def operation_fk(cls):
        return relationship.foreign_key('operation', nullable=True)

    # endregion

    # region many_to_one relationships

    @declared_attr
    def operation_template(cls):
        return relationship.many_to_one(cls, 'operation_template')

    @declared_attr
    def operation(cls):
        return relationship.many_to_one(cls, 'operation')

    # endregion


class PropertyBase(ParameterMixin):

    __tablename__ = 'property'

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

    # region many_to_one relationships

    @declared_attr
    def node_template(cls):
        return relationship.many_to_one(cls, 'node_template')

    @declared_attr
    def group_template(cls):
        return relationship.many_to_one(cls, 'group_template')

    @declared_attr
    def policy_template(cls):
        return relationship.many_to_one(cls, 'policy_template')

    @declared_attr
    def relationship_template(cls):
        return relationship.many_to_one(cls, 'relationship_template')

    @declared_attr
    def capability_template(cls):
        return relationship.many_to_one(cls, 'capability_template')

    @declared_attr
    def artifact_template(cls):
        return relationship.many_to_one(cls, 'artifact_template')

    @declared_attr
    def node(cls):
        return relationship.many_to_one(cls, 'node')

    @declared_attr
    def group(cls):
        return relationship.many_to_one(cls, 'group')

    @declared_attr
    def policy(cls):
        return relationship.many_to_one(cls, 'policy')

    @declared_attr
    def relationship(cls):
        return relationship.many_to_one(cls, 'relationship')

    @declared_attr
    def capability(cls):
        return relationship.many_to_one(cls, 'capability')

    @declared_attr
    def artifact(cls):
        return relationship.many_to_one(cls, 'artifact')

    # endregion


class AttributeBase(ParameterMixin):

    __tablename__ = 'attribute'

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

    # region many_to_one relationships

    @declared_attr
    def node_template(cls):
        return relationship.many_to_one(cls, 'node_template')

    @declared_attr
    def node(cls):
        return relationship.many_to_one(cls, 'node')

    # endregion


class TypeBase(InstanceModelMixin):
    """
    Represents a type and its children.
    """

    __tablename__ = 'type'

    __private_fields__ = ['parent_type_fk']

    variant = Column(Text, nullable=False)
    description = Column(Text)
    _role = Column(Text, name='role')

    @declared_attr
    def parent(cls):
        return relationship.one_to_one_self(cls, 'parent_type_fk')

    @declared_attr
    def children(cls):
        return relationship.one_to_many(cls, other_fk='parent_type_fk', self=True)

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

    def coerce_values(self, report_issues):
        pass

    def dump(self):
        context = ConsumptionContext.get_thread_local()
        if self.name:
            console.puts(context.style.type(self.name))
        with context.style.indent:
            for child in self.children:
                child.dump()

    def _append_raw_children(self, types):
        for child in self.children:
            raw_child = formatting.as_raw(child)
            raw_child['parent'] = self.name
            types.append(raw_child)
            child._append_raw_children(types)

    @property
    def hierarchy(self):
        """
        Return the type hierarchy.
        :return:
        """
        return [self] + (self.parent.hierarchy if self.parent else [])


class MetadataBase(TemplateModelMixin):
    """
    Custom values associated with the service.

    This model is used by both service template and service instance elements.

    :ivar name: Name
    :vartype name: basestring
    :ivar value: Value
    :vartype value: basestring
    """

    __tablename__ = 'metadata'

    value = Column(Text)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('value', self.value)))

    def coerce_values(self, report_issues):
        pass

    def instantiate(self, container):
        from . import models
        return models.Metadata(name=self.name,
                               value=self.value)

    def dump(self):
        context = ConsumptionContext.get_thread_local()
        console.puts('{0}: {1}'.format(
            context.style.property(self.name),
            context.style.literal(self.value)))
