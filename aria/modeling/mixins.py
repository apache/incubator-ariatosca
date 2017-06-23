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
ARIA modeling mix-ins module
"""

from sqlalchemy.ext import associationproxy
from sqlalchemy import (
    Column,
    Integer,
    Text,
    PickleType
)

from ..parser.consumption import ConsumptionContext
from ..utils import console, collections, caching, formatting
from ..utils.type import canonical_type_name, full_type_name
from . import utils, functions


class ModelMixin(object):

    @utils.classproperty
    def __modelname__(cls):                                                                         # pylint: disable=no-self-argument
        return getattr(cls, '__mapiname__', cls.__tablename__)

    @classmethod
    def id_column_name(cls):
        raise NotImplementedError

    @classmethod
    def name_column_name(cls):
        raise NotImplementedError

    def to_dict(self, fields=None, suppress_error=False):
        """
        Create a dict representation of the model.

        :param suppress_error: if set to ``True``, sets ``None`` to attributes that it's unable to
         retrieve (e.g., if a relationship wasn't established yet, and so it's impossible to access
         a property through it)
        """

        res = dict()
        fields = fields or self.fields()
        for field in fields:
            try:
                field_value = getattr(self, field)
            except AttributeError:
                if suppress_error:
                    field_value = None
                else:
                    raise
            if isinstance(field_value, list):
                field_value = list(field_value)
            elif isinstance(field_value, dict):
                field_value = dict(field_value)
            elif isinstance(field_value, ModelMixin):
                field_value = field_value.to_dict()
            res[field] = field_value

        return res

    @classmethod
    def fields(cls):
        """
        List of field names for this table.

        Mostly for backwards compatibility in the code (that uses ``fields``).
        """

        fields = set(cls._iter_association_proxies())
        fields.update(cls.__table__.columns.keys())
        return fields - set(getattr(cls, '__private_fields__', ()))

    @classmethod
    def _iter_association_proxies(cls):
        for col, value in vars(cls).items():
            if isinstance(value, associationproxy.AssociationProxy):
                yield col

    def __repr__(self):
        return '<{cls} id=`{id}`>'.format(
            cls=self.__class__.__name__,
            id=getattr(self, self.name_column_name()))


class ModelIDMixin(object):
    id = Column(Integer, primary_key=True, autoincrement=True, doc="""
    Unique ID.
    
    :type: :obj:`int`
    """)

    name = Column(Text, index=True, doc="""
    Model name.
    
    :type: :obj:`basestring`
    """)

    @classmethod
    def id_column_name(cls):
        return 'id'

    @classmethod
    def name_column_name(cls):
        return 'name'


class InstanceModelMixin(ModelMixin):
    """
    Mix-in for service instance models.

    All models support validation, diagnostic dumping, and representation as raw data (which can be
    translated into JSON or YAML) via :meth:`as_raw`.
    """

    @property
    def as_raw(self):
        raise NotImplementedError

    def validate(self):
        pass

    def coerce_values(self, report_issues):
        pass

    def dump(self):
        pass


class TemplateModelMixin(InstanceModelMixin):
    """
    Mix-in for service template models.

    All model models can be instantiated into service instance models.
    """

    def instantiate(self, container):
        raise NotImplementedError


class ParameterMixin(TemplateModelMixin, caching.HasCachedMethods):                                 #pylint: disable=abstract-method
    """
    Mix-in for typed values. The value can contain nested intrinsic functions.

    This model can be used as the ``container_holder`` argument for
    :func:`~aria.modeling.functions.evaluate`.
    """

    __tablename__ = 'parameter'

    type_name = Column(Text, doc="""
    Type name.
    
    :type: :obj:`basestring`
    """)

    description = Column(Text, doc="""
    Human-readable description.
    
    :type: :obj:`basestring`
    """)

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

        *All* parameters should have an owner model.

        :raises ~exceptions.ValueError: if failed to find an owner, which signifies an abnormal,
         orphaned parameter
        """

        # Find first non-null relationship
        for the_relationship in self.__mapper__.relationships:
            v = getattr(self, the_relationship.key)
            if v:
                return v

        raise ValueError('orphaned {class_name}: does not have an owner: {name}'.format(
            class_name=type(self).__name__, name=self.name))

    @property
    @caching.cachedmethod
    def container(self): # pylint: disable=too-many-return-statements,too-many-branches
        """
        The logical container for this parameter, which would be another model: service, node,
        group, or policy (or their templates).

        The logical container is equivalent to the ``SELF`` keyword used by intrinsic functions in
        TOSCA.

        *All* parameters should have a container model.

        :raises ~exceptions.ValueError: if failed to find a container model, which signifies an
         abnormal, orphaned parameter
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
        The :class:`~aria.modeling.models.Service` model containing this parameter, or ``None`` if
        not contained in a service.

        :raises ~exceptions.ValueError: if failed to find a container model, which signifies an
         abnormal, orphaned parameter
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
        The :class:`~aria.modeling.models.ServiceTemplate` model containing this parameter, or
        ``None`` if not contained in a service template.

        :raises ~exceptions.ValueError: if failed to find a container model, which signifies an
         abnormal, orphaned parameter
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
        return self.__class__(name=self.name,  # pylint: disable=unexpected-keyword-arg
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

    @property
    def unwrapped(self):
        return self.name, self.value

    @classmethod
    def wrap(cls, name, value, description=None):
        """
        Wraps an arbitrary value as a parameter. The type will be guessed via introspection.

        For primitive types, we will prefer their TOSCA aliases. See the `TOSCA Simple Profile v1.0
        cos01 specification <http://docs.oasis-open.org/tosca/TOSCA-Simple-Profile-YAML/v1.0/cos01
        /TOSCA-Simple-Profile-YAML-v1.0-cos01.html#_Toc373867862>`__

        :param name: parameter name
        :type name: basestring
        :param value: parameter value
        :param description: human-readable description (optional)
        :type description: basestring
        """

        type_name = canonical_type_name(value)
        if type_name is None:
            type_name = full_type_name(value)
        return cls(name=name,  # pylint: disable=unexpected-keyword-arg
                   type_name=type_name,
                   value=value,
                   description=description)

    def as_other_parameter_model(self, other_model_cls):
        name, value = self.unwrapped
        return other_model_cls.wrap(name, value)

    def as_argument(self):
        from . import models
        return self.as_other_parameter_model(models.Argument)
