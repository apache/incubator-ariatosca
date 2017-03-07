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
ARIA's storage.structures module
Path: aria.storage.structures

models module holds ARIA's models.

classes:
    * ModelMixin - abstract model implementation.
    * ModelIDMixin - abstract model implementation with IDs.
"""

from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.ext import associationproxy
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Text,
    Table,
)

from . import utils
from ..utils import formatting


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

    @classmethod
    def foreign_key(cls, parent_table, nullable=False):
        """
        Return a ForeignKey object.

        :param parent_table: Parent table name
        :param nullable: Should the column be allowed to remain empty
        """
        return Column(Integer,
                      ForeignKey('{table}.id'.format(table=parent_table),
                                 ondelete='CASCADE'),
                      nullable=nullable)

    @classmethod
    def relationship_to_self(cls,
                             column_name,
                             relationship_kwargs=None):
        relationship_kwargs = relationship_kwargs or {}

        remote_side = '{cls}.{remote_column}'.format(
            cls=cls.__name__,
            remote_column=cls.id_column_name()
        )

        primaryjoin = '{remote_side} == {cls}.{column}'.format(
            remote_side=remote_side,
            cls=cls.__name__,
            column=column_name
        )

        return relationship(
            cls._get_cls_by_tablename(cls.__tablename__).__name__,
            primaryjoin=primaryjoin,
            remote_side=remote_side,
            post_update=True,
            **relationship_kwargs
        )

    @classmethod
    def one_to_many_relationship_to_self(cls,
                                         key,
                                         dict_key=None,
                                         relationship_kwargs=None):
        relationship_kwargs = relationship_kwargs or {}

        relationship_kwargs.setdefault('remote_side', '{cls}.{remote_column}'.format(
            cls=cls.__name__,
            remote_column=key
        ))

        return cls._create_relationship(cls.__tablename__, None, relationship_kwargs,
                                        backreference='', dict_key=dict_key)

    @classmethod
    def one_to_one_relationship(cls,
                                other_table,
                                key=None,
                                foreign_key=None,
                                backreference=None,
                                backref_kwargs=None,
                                relationship_kwargs=None):
        backref_kwargs = backref_kwargs or {}
        backref_kwargs.setdefault('uselist', False)

        return cls._create_relationship(other_table, backref_kwargs, relationship_kwargs,
                                        backreference, key=key, foreign_key=foreign_key)

    @classmethod
    def one_to_many_relationship(cls,
                                 child_table,
                                 key=None,
                                 foreign_key=None,
                                 dict_key=None,
                                 backreference=None,
                                 backref_kwargs=None,
                                 relationship_kwargs=None):
        backref_kwargs = backref_kwargs or {}
        backref_kwargs.setdefault('uselist', False)

        return cls._create_relationship(child_table, backref_kwargs, relationship_kwargs,
                                        backreference, key=key, foreign_key=foreign_key,
                                        dict_key=dict_key)

    @classmethod
    def many_to_one_relationship(cls,
                                 parent_table,
                                 key=None,
                                 foreign_key=None,
                                 backreference=None,
                                 backref_kwargs=None,
                                 relationship_kwargs=None):
        """
        Return a one-to-many SQL relationship object
        Meant to be used from inside the *child* object

        :param parent_table: Name of the parent table
        :param foreign_key: The column of the foreign key (from the child table)
        :param backreference: The name to give to the reference to the child (on the parent table)
        """

        if backreference is None:
            backreference = formatting.pluralize(cls.__tablename__)

        backref_kwargs = backref_kwargs or {}
        backref_kwargs.setdefault('uselist', True)
        backref_kwargs.setdefault('lazy', 'dynamic')
        # The following line make sure that when the *parent* is deleted, all its connected children
        # are deleted as well
        backref_kwargs.setdefault('cascade', 'all')

        return cls._create_relationship(parent_table, backref_kwargs, relationship_kwargs,
                                        backreference, key=key, foreign_key=foreign_key)

    @classmethod
    def many_to_many_relationship(cls,
                                  other_table,
                                  table_prefix=None,
                                  key=None,
                                  dict_key=None,
                                  backreference=None,
                                  backref_kwargs=None,
                                  relationship_kwargs=None):
        """
        Return a many-to-many SQL relationship object

        Notes:

        1. The backreference name is the current table's table name
        2. This method creates a new helper table in the DB

        :param cls: The class of the table we're connecting from
        :param other_table: The class of the table we're connecting to
        :param table_prefix: Custom prefix for the helper table name and the backreference name
        :param dict_key: If provided, will use a dict class with this column as the key
        """

        this_table = cls.__tablename__
        this_column_name = '{0}_id'.format(this_table)
        this_foreign_key = '{0}.id'.format(this_table)

        other_column_name = '{0}_id'.format(other_table)
        other_foreign_key = '{0}.id'.format(other_table)

        helper_table = '{0}_{1}'.format(this_table, other_table)

        if backreference is None:
            backreference = formatting.pluralize(this_table)
            if table_prefix:
                helper_table = '{0}_{1}'.format(table_prefix, helper_table)
                backreference = '{0}_{1}'.format(table_prefix, backreference)

        backref_kwargs = backref_kwargs or {}
        backref_kwargs.setdefault('uselist', True)

        relationship_kwargs = relationship_kwargs or {}
        relationship_kwargs.setdefault('secondary', cls._get_secondary_table(
            cls.metadata,
            helper_table,
            this_column_name,
            other_column_name,
            this_foreign_key,
            other_foreign_key
        ))

        return cls._create_relationship(other_table, backref_kwargs, relationship_kwargs,
                                        backreference, key=key, dict_key=dict_key)

    def to_dict(self, fields=None, suppress_error=False):
        """
        Return a dict representation of the model

        :param suppress_error: If set to True, sets `None` to attributes that
                               it's unable to retrieve (e.g., if a relationship wasn't established
                               yet, and so it's impossible to access a property through it)
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
    def _create_relationship(cls, table, backref_kwargs, relationship_kwargs, backreference,
                             key=None, foreign_key=None, dict_key=None):
        relationship_kwargs = relationship_kwargs or {}

        if key:
            relationship_kwargs.setdefault('foreign_keys',
                                           lambda: getattr(
                                               cls._get_cls_by_tablename(cls.__tablename__),
                                               key))

        elif foreign_key:
            relationship_kwargs.setdefault('foreign_keys',
                                           lambda: getattr(
                                               cls._get_cls_by_tablename(table),
                                               foreign_key))

        if dict_key:
            relationship_kwargs.setdefault('collection_class',
                                           attribute_mapped_collection(dict_key))

        if backreference == '':
            return relationship(
                lambda: cls._get_cls_by_tablename(table),
                **relationship_kwargs
            )
        else:
            if backreference is None:
                backreference = cls.__tablename__
            backref_kwargs = backref_kwargs or {}
            return relationship(
                lambda: cls._get_cls_by_tablename(table),
                backref=backref(backreference, **backref_kwargs),
                **relationship_kwargs
            )

    @staticmethod
    def _get_secondary_table(metadata,
                             helper_table,
                             first_column,
                             second_column,
                             first_foreign_key,
                             second_foreign_key):
        """
        Create a helper table for a many-to-many relationship

        :param helper_table: The name of the table
        :param first_column_name: The name of the first column in the table
        :param second_column_name: The name of the second column in the table
        :param first_foreign_key: The string representing the first foreign key,
               for example `blueprint.storage_id`, or `tenants.id`
        :param second_foreign_key: The string representing the second foreign key
        :return: A Table object
        """

        return Table(
            helper_table,
            metadata,
            Column(
                first_column,
                Integer,
                ForeignKey(first_foreign_key)
            ),
            Column(
                second_column,
                Integer,
                ForeignKey(second_foreign_key)
            )
        )

    @classmethod
    def _association_proxies(cls):
        for col, value in vars(cls).items():
            if isinstance(value, associationproxy.AssociationProxy):
                yield col

    @classmethod
    def fields(cls):
        """
        Return the list of field names for this table

        Mostly for backwards compatibility in the code (that uses `fields`)
        """

        fields = set(cls._association_proxies())
        fields.update(cls.__table__.columns.keys())
        return fields - set(getattr(cls, '__private_fields__', []))

    @classmethod
    def _get_cls_by_tablename(cls, tablename):
        """
        Return class reference mapped to table.

        :param tablename: String with name of table.
        :return: Class reference or None.
        """

        if tablename in (cls.__name__, cls.__tablename__):
            return cls

        for table_cls in cls._decl_class_registry.values():
            if tablename == getattr(table_cls, '__tablename__', None):
                return table_cls

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

    def validate(self, context):
        pass

    def coerce_values(self, context, container, report_issues):
        pass

    def dump(self, context):
        pass


class TemplateModelMixin(InstanceModelMixin):
    """
    Mixin for :class:`ServiceTemplate` models.

    All model models can be instantiated into :class:`ServiceInstance` models.
    """

    def instantiate(self, context, container):
        raise NotImplementedError
