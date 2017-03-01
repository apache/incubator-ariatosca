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
    def foreign_key(cls, parent_table_name, nullable=False):
        """
        Return a ForeignKey object.

        :param parent_table_name: Parent table name
        :param nullable: Should the column be allowed to remain empty
        """
        return Column(Integer,
                      ForeignKey('{table}.id'.format(table=parent_table_name),
                                 ondelete='CASCADE'),
                      nullable=nullable)

    @classmethod
    def relationship_to_self(cls,
                             column_name,
                             relationship_kwargs=None):
        relationship_kwargs = relationship_kwargs or {}

        remote_side_str = '{cls}.{remote_column}'.format(
            cls=cls.__name__,
            remote_column=cls.id_column_name()
        )

        primaryjoin_str = '{remote_side_str} == {cls}.{column}'.format(
            remote_side_str=remote_side_str,
            cls=cls.__name__,
            column=column_name
        )

        return relationship(
            cls._get_cls_by_tablename(cls.__tablename__).__name__,
            primaryjoin=primaryjoin_str,
            remote_side=remote_side_str,
            post_update=True,
            **relationship_kwargs
        )

    @classmethod
    def one_to_one_relationship(cls,
                                other_table_name,
                                backreference=None,
                                relationship_kwargs=None):
        relationship_kwargs = relationship_kwargs or {}

        return relationship(
            lambda: cls._get_cls_by_tablename(other_table_name),
            backref=backref(backreference or cls.__tablename__, uselist=False),
            **relationship_kwargs
        )

    @classmethod
    def one_to_many_relationship(cls,
                                 child_table_name,
                                 foreign_key_name=None,
                                 backreference=None,
                                 key_column_name=None,
                                 relationship_kwargs=None):
        relationship_kwargs = relationship_kwargs or {}

        foreign_keys = lambda: getattr(cls._get_cls_by_tablename(child_table_name),
                                       foreign_key_name) \
            if foreign_key_name \
            else None

        collection_class = attribute_mapped_collection(key_column_name) \
            if key_column_name \
            else list

        return relationship(
            lambda: cls._get_cls_by_tablename(child_table_name),
            backref=backref(backreference or cls.__tablename__, uselist=False),
            foreign_keys=foreign_keys,
            collection_class=collection_class,
            **relationship_kwargs
        )

    @classmethod
    def many_to_one_relationship(cls,
                                 parent_table_name,
                                 foreign_key_column=None,
                                 backreference=None,
                                 backref_kwargs=None,
                                 relationship_kwargs=None):
        """
        Return a one-to-many SQL relationship object
        Meant to be used from inside the *child* object

        :param parent_class: Class of the parent table
        :param cls: Class of the child table
        :param foreign_key_column: The column of the foreign key (from the child table)
        :param backreference: The name to give to the reference to the child (on the parent table)
        """
        relationship_kwargs = relationship_kwargs or {}

        if foreign_key_column:
            relationship_kwargs.setdefault('foreign_keys', getattr(cls, foreign_key_column))

        backref_kwargs = backref_kwargs or {}
        backref_kwargs.setdefault('lazy', 'dynamic')
        # The following line make sure that when the *parent* is deleted, all its connected children
        # are deleted as well
        backref_kwargs.setdefault('cascade', 'all')

        return relationship(
            lambda: cls._get_cls_by_tablename(parent_table_name),
            backref=backref(backreference or utils.pluralize(cls.__tablename__), **backref_kwargs),
            **relationship_kwargs
        )

    @classmethod
    def many_to_many_relationship(cls,
                                  other_table_name,
                                  table_prefix=None,
                                  key_column_name=None,
                                  relationship_kwargs=None):
        """
        Return a many-to-many SQL relationship object

        Notes:

        1. The backreference name is the current table's table name
        2. This method creates a new helper table in the DB

        :param cls: The class of the table we're connecting from
        :param other_table_name: The class of the table we're connecting to
        :param table_prefix: Custom prefix for the helper table name and the
                             backreference name
        :param key_column_name: If provided, will use a dict class with this column as the key
        """
        relationship_kwargs = relationship_kwargs or {}

        current_table_name = cls.__tablename__
        current_column_name = '{0}_id'.format(current_table_name)
        current_foreign_key = '{0}.id'.format(current_table_name)

        other_column_name = '{0}_id'.format(other_table_name)
        other_foreign_key = '{0}.id'.format(other_table_name)

        helper_table_name = '{0}_{1}'.format(current_table_name, other_table_name)

        backref_name = current_table_name
        if table_prefix:
            helper_table_name = '{0}_{1}'.format(table_prefix, helper_table_name)
            backref_name = '{0}_{1}'.format(table_prefix, backref_name)

        secondary_table = cls.get_secondary_table(
            cls.metadata,
            helper_table_name,
            current_column_name,
            other_column_name,
            current_foreign_key,
            other_foreign_key
        )

        collection_class = attribute_mapped_collection(key_column_name) \
            if key_column_name \
            else list

        return relationship(
            lambda: cls._get_cls_by_tablename(other_table_name),
            secondary=secondary_table,
            backref=backref(backref_name),
            collection_class=collection_class,
            **relationship_kwargs
        )

    @staticmethod
    def get_secondary_table(metadata,
                            helper_table_name,
                            first_column_name,
                            second_column_name,
                            first_foreign_key,
                            second_foreign_key):
        """
        Create a helper table for a many-to-many relationship

        :param helper_table_name: The name of the table
        :param first_column_name: The name of the first column in the table
        :param second_column_name: The name of the second column in the table
        :param first_foreign_key: The string representing the first foreign key,
               for example `blueprint.storage_id`, or `tenants.id`
        :param second_foreign_key: The string representing the second foreign key
        :return: A Table object
        """
        return Table(
            helper_table_name,
            metadata,
            Column(
                first_column_name,
                Integer,
                ForeignKey(first_foreign_key)
            ),
            Column(
                second_column_name,
                Integer,
                ForeignKey(second_foreign_key)
            )
        )

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
    name = Column(Text, nullable=True, index=True)

    @classmethod
    def id_column_name(cls):
        return 'id'

    @classmethod
    def name_column_name(cls):
        return 'name'
