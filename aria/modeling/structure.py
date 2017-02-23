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
Aria's storage.structures module
Path: aria.storage.structures

models module holds aria's models.

classes:
    * Field - represents a single field.
    * IterField - represents an iterable field.
    * PointerField - represents a single pointer field.
    * IterPointerField - represents an iterable pointers field.
    * Model - abstract model implementation.
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


class Function(object):
    """
    An intrinsic function.

    Serves as a placeholder for a value that should eventually be derived
    by calling the function.
    """

    @property
    def as_raw(self):
        raise NotImplementedError

    def _evaluate(self, context, container):
        raise NotImplementedError

    def __deepcopy__(self, memo):
        # Circumvent cloning in order to maintain our state
        return self


class ElementBase(object):
    """
    Base class for :class:`ServiceInstance` elements.

    All elements support validation, diagnostic dumping, and representation as
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


class ModelElementBase(ElementBase):
    """
    Base class for :class:`ServiceModel` elements.

    All model elements can be instantiated into :class:`ServiceInstance` elements.
    """

    def instantiate(self, context, container):
        raise NotImplementedError


class ModelMixin(ModelElementBase):

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
    def _get_cls_by_tablename(cls, tablename):
        """Return class reference mapped to table.

         :param tablename: String with name of table.
         :return: Class reference or None.
         """
        if tablename in (cls.__name__, cls.__tablename__):
            return cls

        for table_cls in cls._decl_class_registry.values():
            if tablename == getattr(table_cls, '__tablename__', None):
                return table_cls

    @classmethod
    def foreign_key(cls, parent_table_name, nullable=False):
        """Return a ForeignKey object.

        :param parent_table_name: Parent table name
        :param nullable: Should the column be allowed to remain empty
        """
        return Column(Integer,
                      ForeignKey('{table}.id'.format(table=parent_table_name),
                                 ondelete='CASCADE'),
                      nullable=nullable)

    @classmethod
    def relationship_to_self(cls, local_column, relationship_kwargs=None):
        relationship_kwargs = relationship_kwargs or {}

        remote_side_str = '{cls.__name__}.{remote_column}'.format(
            cls=cls,
            remote_column=cls.id_column_name()
        )

        primaryjoin_str = '{remote_side_str} == {cls.__name__}.{local_column}'.format(
            remote_side_str=remote_side_str,
            cls=cls,
            local_column=local_column)

        return relationship(cls._get_cls_by_tablename(cls.__tablename__).__name__,
                            primaryjoin=primaryjoin_str,
                            remote_side=remote_side_str,
                            post_update=True,
                            **relationship_kwargs)

    @classmethod
    def one_to_one_relationship(cls, other_table_name, backreference=None,
                                relationship_kwargs=None):
        relationship_kwargs = relationship_kwargs or {}

        return relationship(lambda: cls._get_cls_by_tablename(other_table_name),
                            backref=backref(backreference or cls.__tablename__, uselist=False),
                            **relationship_kwargs)

    @classmethod
    def one_to_many_relationship(cls, child_table_name, backreference=None, key_column_name=None,
                                 relationship_kwargs=None):
        relationship_kwargs = relationship_kwargs or {}

        collection_class = attribute_mapped_collection(key_column_name) \
            if key_column_name \
            else list

        return relationship(lambda: cls._get_cls_by_tablename(child_table_name),
                            backref=backref(backreference or cls.__tablename__, uselist=False),
                            collection_class=collection_class,
                            **relationship_kwargs)

    @classmethod
    def many_to_one_relationship(cls,
                                 parent_table_name,
                                 foreign_key_column=None,
                                 backreference=None,
                                 backref_kwargs=None,
                                 relationship_kwargs=None,
                                 **kwargs):
        """Return a one-to-many SQL relationship object
        Meant to be used from inside the *child* object

        :param parent_class: Class of the parent table
        :param cls: Class of the child table
        :param foreign_key_column: The column of the foreign key (from the child table)
        :param backreference: The name to give to the reference to the child (on the parent table)
        """
        relationship_kwargs = kwargs
        if foreign_key_column:
            relationship_kwargs.setdefault('foreign_keys', getattr(cls, foreign_key_column))

        backref_kwargs = backref_kwargs or {}
        backref_kwargs.setdefault('lazy', 'dynamic')
        # The following line make sure that when the *parent* is deleted, all its connected children
        # are deleted as well
        backref_kwargs.setdefault('cascade', 'all')

        return relationship(lambda: cls._get_cls_by_tablename(parent_table_name),
                            backref=backref(backreference or utils.pluralize(cls.__tablename__),
                                            **backref_kwargs or {}),
                            **relationship_kwargs)

    @classmethod
    def many_to_many_relationship(cls, other_table_name, table_prefix, key_column_name=None,
                                  relationship_kwargs=None):
        """Return a many-to-many SQL relationship object

        Notes:
        1. The backreference name is the current table's table name
        2. This method creates a new helper table in the DB

        :param cls: The class of the table we're connecting from
        :param other_table_name: The class of the table we're connecting to
        :param table_prefix: Custom prefix for the helper table name and the
                             backreference name
        :param key_column_name: If provided, will use a dict class with this column as the key 
        """
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
            **(relationship_kwargs or {})
        )

    @staticmethod
    def get_secondary_table(metadata,
                            helper_table_name,
                            first_column_name,
                            second_column_name,
                            first_foreign_key,
                            second_foreign_key):
        """Create a helper table for a many-to-many relationship

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
        """Return a dict representation of the model

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
        """Return the list of field names for this table

        Mostly for backwards compatibility in the code (that uses `fields`)
        """
        fields = set(cls._association_proxies())
        fields.update(cls.__table__.columns.keys())
        return fields - set(getattr(cls, '__private_fields__', []))

    def __repr__(self):
        return '<{__class__.__name__} id=`{id}`>'.format(
            __class__=self.__class__,
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
