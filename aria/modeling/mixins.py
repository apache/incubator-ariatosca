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
classes:
    * ModelMixin - abstract model implementation.
    * ModelIDMixin - abstract model implementation with IDs.
"""

from sqlalchemy.ext import associationproxy
from sqlalchemy import (
    Column,
    Integer,
    Text,
)

from .utils import classproperty


class ModelMixin(object):

    @classproperty
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
        Return a dict representation of the model

        :param suppress_error: If set to True, sets `None` to attributes that it's unable to
                               retrieve (e.g., if a relationship wasn't established yet, and so it's
                               impossible to access a property through it)
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
        Return the list of field names for this table

        Mostly for backwards compatibility in the code (that uses `fields`)
        """

        fields = set(cls._iter_association_proxies())
        fields.update(cls.__table__.columns.keys())
        return fields - set(getattr(cls, '__private_fields__', []))

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
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, index=True)

    @classmethod
    def id_column_name(cls):
        return 'id'

    @classmethod
    def name_column_name(cls):
        return 'name'


class InstanceModelMixin(ModelMixin):
    """
    Mixin for :class:`ServiceInstance` models.

    All models support validation, diagnostic dumping, and representation as
    raw data (which can be translated into JSON or YAML) via :code:`as_raw`.
    """

    @property
    def as_raw(self):
        raise NotImplementedError

    def validate(self):
        pass

    def coerce_values(self, container, report_issues):
        pass

    def dump(self):
        pass


class TemplateModelMixin(InstanceModelMixin):
    """
    Mixin for :class:`ServiceTemplate` models.

    All model models can be instantiated into :class:`ServiceInstance` models.
    """

    def instantiate(self, container):
        raise NotImplementedError
