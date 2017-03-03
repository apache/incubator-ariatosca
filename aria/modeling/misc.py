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

import cPickle as pickle

from sqlalchemy import (
    Column,
    Text,
    Binary
)
from sqlalchemy.ext.declarative import declared_attr

from ..storage import exceptions
from ..parser.modeling import utils as parser_utils
from ..utils import collections, formatting, console
from .bases import InstanceModelMixin, TemplateModelMixin


class ParameterBase(TemplateModelMixin):
    """
    Represents a typed value.

    This class is used by both service template and service instance elements.

    :ivar name: Name
    :ivar type_name: Type name
    :ivar value: Value
    :ivar description: Description
    """

    __tablename__ = 'parameter'

    name = Column(Text, nullable=False)
    type_name = Column(Text, nullable=False)

    # Check: value type
    _value = Column(Binary, nullable=True)
    description = Column(Text)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('type_name', self.type_name),
            ('value', self.value),
            ('description', self.description)))

    @property
    def value(self):
        if self._value is None:
            return None
        try:
            return pickle.loads(self._value)
        except BaseException:
            raise exceptions.StorageError('Bad format for parameter of type "{0}": {1}'.format(
                self.type_name, self._value))

    @value.setter
    def value(self, value):
        if value is None:
            self._value = None
        else:
            try:
                self._value = pickle.dumps(value)
            except pickle.PicklingError:
                # TODO debug log
                self._value = pickle.dumps(str(value))
 
    def instantiate(self, context, container):
        from . import models
        return models.Parameter(name=self.name,
                                type_name=self.type_name,
                                _value=self._value,
                                description=self.description)

    def coerce_values(self, context, container, report_issues):
        if self.value is not None:
            self.value = parser_utils.coerce_value(context, container, self.value,
                                                   report_issues)


class TypeBase(InstanceModelMixin):
    """
    Represents a type and its children.
    """

    __tablename__ = 'type'

    variant = Column(Text) 
    description = Column(Text)
    role = Column(Text)

    @declared_attr
    def parent(cls):
        return cls.relationship_to_self('parent_type_fk')

    @declared_attr
    def children(cls):
        return cls.one_to_many_relationship_to_self('parent_type_fk')

    # region foreign keys

    __private_fields__ = ['parent_type_fk']

    # Type one-to-many to Type
    @declared_attr
    def parent_type_fk(cls):
        return cls.foreign_key('type', nullable=True)

    # endregion

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

    def get_role(self, name):
        def _get_role(the_type):
            if the_type is None:
                return None
            elif the_type.role is None:
                return _get_role(self.parent)
            return the_type.role

        return _get_role(self.get_descendant(name))

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

    def dump(self, context):
        if self.name:
            console.puts(context.style.type(self.name))
        with context.style.indent:
            for child in self.children:
                child.dump(context)

    def _append_raw_children(self, types):
        for child in self.children:
            raw_child = formatting.as_raw(child)
            raw_child['parent'] = self.name
            types.append(raw_child)
            child._append_raw_children(types)


class MetadataBase(TemplateModelMixin):
    """
    Custom values associated with the service.

    This class is used by both service template and service instance elements.

    :ivar name: Name
    :ivar value: Value
    """

    __tablename__ = 'metadata'

    name = Column(Text, nullable=False)
    value = Column(Text)

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('value', self.value)))

    def instantiate(self, context, container):
        from . import models
        return models.Metadata(name=self.name,
                               value=self.value)
