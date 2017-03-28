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
    PickleType
)
from sqlalchemy.ext.declarative import declared_attr

from ..parser.consumption import ConsumptionContext
from ..utils import collections, formatting, console
from .mixins import InstanceModelMixin, TemplateModelMixin
from . import (
    relationship,
    utils
)


class ParameterBase(TemplateModelMixin):
    """
    Represents a typed value.

    This model is used by both service template and service instance elements.

    :ivar name: Name
    :vartype name: basestring
    :ivar type_name: Type name
    :vartype type_name: basestring
    :ivar value: Value
    :ivar description: Description
    :vartype description: basestring
    """

    __tablename__ = 'parameter'

    name = Column(Text)
    type_name = Column(Text)
    value = Column(PickleType)
    description = Column(Text)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('type_name', self.type_name),
            ('value', self.value),
            ('description', self.description)))

    def instantiate(self, container):
        from . import models
        return models.Parameter(name=self.name,
                                type_name=self.type_name,
                                value=self.value,
                                description=self.description)

    def coerce_values(self, container, report_issues):
        if self.value is not None:
            self.value = utils.coerce_value(container, self.value,
                                            report_issues)

    def dump(self):
        context = ConsumptionContext.get_thread_local()
        if self.type_name is not None:
            console.puts('{0}: {1} ({2})'.format(
                context.style.property(self.name),
                context.style.literal(self.value),
                context.style.type(self.type_name)))
        else:
            console.puts('{0}: {1}'.format(
                context.style.property(self.name),
                context.style.literal(self.value)))
        if self.description:
            console.puts(context.style.meta(self.description))

    def unwrap(self):
        return self.name, self.value

    @classmethod
    def wrap(cls, name, value, description=None):
        """
        Wraps an arbitrary value as a parameter. The type will be guessed via introspection.

        :param name: Parameter name
        :type name: basestring
        :param value: Parameter value
        :param description: Description (optional)
        :type description: basestring
        """
        return cls(name=name,
                   type_name=formatting.full_type_name(value)
                   if value is not None else None,
                   value=value,
                   description=description)


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
        return relationship.one_to_many_self(cls, 'parent_type_fk')

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

    def coerce_values(self, container, report_issues):
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

    def coerce_values(self, container, report_issues):
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
