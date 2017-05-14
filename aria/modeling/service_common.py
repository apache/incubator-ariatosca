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
from ..utils import (collections, formatting, console, caching)
from ..utils.type import (canonical_type_name, full_type_name)
from .mixins import (InstanceModelMixin, TemplateModelMixin)
from . import (
    relationship,
    functions
)


class ParameterBase(TemplateModelMixin, caching.HasCachedMethods):
    """
    Represents a typed value. The value can contain nested intrinsic functions.

    This model can be used as the ``container_holder`` argument for :func:`functions.evaluate`.

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
    description = Column(Text)
    _value = Column(PickleType)

    @property
    def value(self):
        value = self._value
        if value is not None:
            evaluation = functions.evaluate(value, self)
            if evaluation is not None:
                value = evaluation.value
        return value

    @value.setter
    def value(self, value):
        self._value = value

    @property
    @caching.cachedmethod
    def owner(self):
        """
        The sole owner of this parameter, which is another model that relates to it.

        *All* parameters should have an owner model. In case this property method fails to find
        it, it will raise a ValueError, which should signify an abnormal, orphaned parameter.
        """

        # Find first non-null relationship
        for the_relationship in self.__mapper__.relationships:
            v = getattr(self, the_relationship.key)
            if v:
                return v[0] # because we are many-to-many, the back reference will be a list

        raise ValueError('orphaned parameter: does not have an owner: {0}'.format(self.name))


    @property
    @caching.cachedmethod
    def container(self): # pylint: disable=too-many-return-statements,too-many-branches
        """
        The logical container for this parameter, which would be another model: service, node,
        group, or policy (or their templates).

        The logical container is equivalent to the ``SELF`` keyword used by intrinsic functions in
        TOSCA.

        *All* parameters should have a container model. In case this property method fails to find
        it, it will raise a ValueError, which should signify an abnormal, orphaned parameter.
        """

        from . import models

        container = self.owner

        # Extract interface from operation
        if isinstance(container, models.Operation):
            container = container.interface
        elif isinstance(container, models.OperationTemplate):
            container = container.interface_template

        # Extract from other models
        if isinstance(container, models.Interface):
            container = container.node or container.group or container.relationship
        elif isinstance(container, models.InterfaceTemplate):
            container = container.node_template or container.group_template \
                or container.relationship_template
        elif isinstance(container, models.Capability) or isinstance(container, models.Artifact):
            container = container.node
        elif isinstance(container, models.CapabilityTemplate) \
            or isinstance(container, models.ArtifactTemplate):
            container = container.node_template
        elif isinstance(container, models.Task):
            container = container.actor

        # Extract node from relationship
        if isinstance(container, models.Relationship):
            container = container.source_node
        elif isinstance(container, models.RelationshipTemplate):
            container = container.requirement_template.node_template

        if container is not None:
            return container

        raise ValueError('orphaned parameter: does not have a container: {0}'.format(self.name))

    @property
    @caching.cachedmethod
    def service(self):
        """
        The :class:`Service` containing this parameter, or None if not contained in a service.
        """

        from . import models
        container = self.container
        if isinstance(container, models.Service):
            return container
        elif hasattr(container, 'service'):
            return container.service
        return None

    @property
    @caching.cachedmethod
    def service_template(self):
        """
        The :class:`ServiceTemplate` containing this parameter, or None if not contained in a
        service template.
        """

        from . import models
        container = self.container
        if isinstance(container, models.ServiceTemplate):
            return container
        elif hasattr(container, 'service_template'):
            return container.service_template
        return None

    @property
    def as_raw(self):
        return collections.OrderedDict((
            ('name', self.name),
            ('type_name', self.type_name),
            ('value', self.value),
            ('description', self.description)))

    def instantiate(self, container):
        from . import models
        return models.Parameter(name=self.name, # pylint: disable=unexpected-keyword-arg
                                type_name=self.type_name,
                                _value=self._value,
                                description=self.description)

    def coerce_values(self, report_issues):
        value = self._value
        if value is not None:
            evaluation = functions.evaluate(value, self, report_issues)
            if (evaluation is not None) and evaluation.final:
                # A final evaluation can safely replace the existing value
                self._value = evaluation.value

    def dump(self):
        context = ConsumptionContext.get_thread_local()
        if self.type_name is not None:
            console.puts('{0}: {1} ({2})'.format(
                context.style.property(self.name),
                context.style.literal(formatting.as_raw(self.value)),
                context.style.type(self.type_name)))
        else:
            console.puts('{0}: {1}'.format(
                context.style.property(self.name),
                context.style.literal(formatting.as_raw(self.value))))
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

        type_name = canonical_type_name(value)
        if type_name is None:
            type_name = full_type_name(value)
        return cls(name=name, # pylint: disable=unexpected-keyword-arg
                   type_name=type_name,
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
