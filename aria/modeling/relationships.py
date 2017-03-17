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

# pylint: disable=invalid-name, redefined-outer-name

from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Table
)

from ..utils import formatting


def fk(other_table,
       nullable=False):
    """
    Declare a foreign key property, which will also create a foreign key column in the table with
    the name of the property. By convention the property name should end in "_fk".

    You are required to explicitly create foreign keys in order to allow for one-to-one,
    one-to-many, and many-to-one relationships (but not for many-to-many relationships). If you do
    not do so, SQLAlchemy will fail to create the relationship property and raise an exception with
    a clear error message.

    You should normally not have to access this property directly, but instead use the associated
    relationship properties.

    *This utility method should only be used during class creation.*

    :param other_table: Other table name
    :type other_table: basestring
    :param nullable: True to allow null values (meaning that there is no relationship)
    :type nullable: bool
    """

    return Column(Integer,
                  ForeignKey('{table}.id'.format(table=other_table), ondelete='CASCADE'),
                  nullable=nullable)


def one_to_one_self(model_class,
                    fk,
                    relationship_kwargs=None):
    """
    Declare a one-to-one relationship property. The property value would be an instance of the same
    model.

    You will need an associated foreign key to our own table.

    *This utility method should only be used during class creation.*

    :param model_class: The class in which this relationship will be declared
    :type model_class: type
    :param fk: Foreign key name
    :type fk: basestring
    :param relationship_kwargs: Extra kwargs for SQLAlchemy `relationship`
    :type relationship_kwargs: {}
    """

    relationship_kwargs = relationship_kwargs or {}

    remote_side = '{model_class}.{remote_column}'.format(
        model_class=model_class.__name__,
        remote_column=model_class.id_column_name()
    )

    primaryjoin = '{remote_side} == {model_class}.{column}'.format(
        remote_side=remote_side,
        model_class=model_class.__name__,
        column=fk
    )

    return relationship(
        _get_class_for_table(model_class, model_class.__tablename__).__name__,
        primaryjoin=primaryjoin,
        remote_side=remote_side,
        post_update=True,
        **relationship_kwargs
    )


def one_to_many_self(model_class,
                     fk,
                     dict_key=None,
                     relationship_kwargs=None):
    """
    Declare a one-to-many relationship property. The property value would be a list or dict of
    instances of the same model.

    You will need an associated foreign key to our own table.

    *This utility method should only be used during class creation.*

    :param model_class: The class in which this relationship will be declared
    :type model_class: type
    :param fk: Foreign key name
    :type fk: basestring
    :param dict_key: If set the value will be a dict with this key as the dict key; otherwise will
                     be a list
    :type dict_key: basestring
    :param relationship_kwargs: Extra kwargs for SQLAlchemy `relationship`
    :type relationship_kwargs: {}
    """

    relationship_kwargs = relationship_kwargs or {}

    relationship_kwargs.setdefault('remote_side', '{model_class}.{remote_column}'.format(
        model_class=model_class.__name__,
        remote_column=fk
    ))

    return _relationship(model_class, model_class.__tablename__, None, relationship_kwargs,
                         other_property=False, dict_key=dict_key)


def one_to_one(model_class,
               other_table,
               fk=None,
               other_fk=None,
               other_property=None,
               relationship_kwargs=None,
               backref_kwargs=None):
    """
    Declare a one-to-one relationship property. The property value would be an instance of the other
    table's model.

    You have two options for the foreign key. Either this table can have an associated key to the
    other table (use the `fk` argument) or the other table can have an associated foreign key to
    this our table (use the `other_fk` argument).

    *This utility method should only be used during class creation.*

    :param model_class: The class in which this relationship will be declared
    :type model_class: type
    :param other_table: Other table name
    :type other_table: basestring
    :param fk: Foreign key name at our table (no need specify if there's no ambiguity)
    :type fk: basestring
    :param other_fk: Foreign key name at the other table (no need specify if there's no ambiguity)
    :type other_fk: basestring
    :param relationship_kwargs: Extra kwargs for SQLAlchemy `relationship`
    :type relationship_kwargs: {}
    :param backref_kwargs: Extra kwargs for SQLAlchemy `backref`
    :type backref_kwargs: {}
    """

    backref_kwargs = backref_kwargs or {}
    backref_kwargs.setdefault('uselist', False)

    return _relationship(model_class, other_table, backref_kwargs, relationship_kwargs,
                         other_property, fk=fk, other_fk=other_fk)


def one_to_many(model_class,
                child_table,
                child_fk=None,
                dict_key=None,
                child_property=None,
                relationship_kwargs=None,
                backref_kwargs=None):
    """
    Declare a one-to-many relationship property. The property value would be a list or dict of
    instances of the child table's model.

    The child table will need an associated foreign key to our table.

    The declaration will automatically create a matching many-to-one property at the child model,
    named after our table name. Use the `child_property` argument to override this name.

    *This utility method should only be used during class creation.*

    :param model_class: The class in which this relationship will be declared
    :type model_class: type
    :param child_table: Child table name
    :type child_table: basestring
    :param child_fk: Foreign key name at the child table (no need specify if there's no ambiguity)
    :type child_fk: basestring
    :param dict_key: If set the value will be a dict with this key as the dict key; otherwise will
                     be a list
    :type dict_key: basestring
    :param child_property: Override name of matching many-to-one property at child table; set to
                           false to disable
    :type child_property: basestring|bool
    :param relationship_kwargs: Extra kwargs for SQLAlchemy `relationship`
    :type relationship_kwargs: {}
    :param backref_kwargs: Extra kwargs for SQLAlchemy `backref`
    :type backref_kwargs: {}
    """

    backref_kwargs = backref_kwargs or {}
    backref_kwargs.setdefault('uselist', False)

    return _relationship(model_class, child_table, backref_kwargs, relationship_kwargs,
                         child_property, other_fk=child_fk, dict_key=dict_key)


def many_to_one(model_class,
                parent_table,
                fk=None,
                parent_fk=None,
                parent_property=None,
                relationship_kwargs=None,
                backref_kwargs=None):
    """
    Declare a many-to-one relationship property. The property value would be an instance of the
    parent table's model.

    You will need an associated foreign key to the parent table.

    The declaration will automatically create a matching one-to-many property at the child model,
    named after the plural form of our table name. Use the `parent_property` argument to override
    this name. Note: the automatic property will always be a SQLAlchemy query object; if you need a
    Python collection then use :meth:`one_to_many` at that model.

    *This utility method should only be used during class creation.*

    :param model_class: The class in which this relationship will be declared
    :type model_class: type
    :param parent_table: Parent table name
    :type parent_table: basestring
    :param fk: Foreign key name at our table (no need specify if there's no ambiguity)
    :type fk: basestring
    :param parent_property: Override name of matching one-to-many property at parent table; set to
                            false to disable
    :type parent_property: basestring|bool
    :param relationship_kwargs: Extra kwargs for SQLAlchemy `relationship`
    :type relationship_kwargs: {}
    :param backref_kwargs: Extra kwargs for SQLAlchemy `backref`
    :type backref_kwargs: {}
    """

    if parent_property is None:
        parent_property = formatting.pluralize(model_class.__tablename__)

    backref_kwargs = backref_kwargs or {}
    backref_kwargs.setdefault('uselist', True)
    backref_kwargs.setdefault('lazy', 'dynamic')
    backref_kwargs.setdefault('cascade', 'all') # delete children when parent is deleted

    return _relationship(model_class, parent_table, backref_kwargs, relationship_kwargs,
                         parent_property, fk=fk, other_fk=parent_fk)


def many_to_many(model_class,
                 other_table,
                 prefix=None,
                 dict_key=None,
                 other_property=None,
                 relationship_kwargs=None,
                 backref_kwargs=None):
    """
    Declare a many-to-many relationship property. The property value would be a list or dict of
    instances of the other table's model.

    You do not need associated foreign keys for this relationship. Instead, an extra table will be
    created for you.

    The declaration will automatically create a matching many-to-many property at the other model,
    named after the plural form of our table name. Use the `other_property` argument to override
    this name. Note: the automatic property will always be a SQLAlchemy query object; if you need a
    Python collection then use :meth:`many_to_many` again at that model.

    *This utility method should only be used during class creation.*

    :param model_class: The class in which this relationship will be declared
    :type model_class: type
    :param parent_table: Parent table name
    :type parent_table: basestring
    :param prefix: Optional prefix for extra table name as well as for `other_property`
    :type prefix: basestring
    :param dict_key: If set the value will be a dict with this key as the dict key; otherwise will
                     be a list
    :type dict_key: basestring
    :param other_property: Override name of matching many-to-many property at other table; set to
                           false to disable
    :type other_property: basestring|bool
    :param relationship_kwargs: Extra kwargs for SQLAlchemy `relationship`
    :type relationship_kwargs: {}
    :param backref_kwargs: Extra kwargs for SQLAlchemy `backref`
    :type backref_kwargs: {}
    """

    this_table = model_class.__tablename__
    this_column_name = '{0}_id'.format(this_table)
    this_foreign_key = '{0}.id'.format(this_table)

    other_column_name = '{0}_id'.format(other_table)
    other_foreign_key = '{0}.id'.format(other_table)

    secondary_table = '{0}_{1}'.format(this_table, other_table)

    if other_property is None:
        other_property = formatting.pluralize(this_table)
        if prefix is not None:
            secondary_table = '{0}_{1}'.format(prefix, secondary_table)
            other_property = '{0}_{1}'.format(prefix, other_property)

    backref_kwargs = backref_kwargs or {}
    backref_kwargs.setdefault('uselist', True)

    relationship_kwargs = relationship_kwargs or {}
    relationship_kwargs.setdefault('secondary', _get_secondary_table(
        model_class.metadata,
        secondary_table,
        this_column_name,
        other_column_name,
        this_foreign_key,
        other_foreign_key
    ))

    return _relationship(model_class, other_table, backref_kwargs, relationship_kwargs,
                         other_property, dict_key=dict_key)


def _relationship(model_class, other_table, backref_kwargs, relationship_kwargs, other_property,
                  fk=None, other_fk=None, dict_key=None):
    relationship_kwargs = relationship_kwargs or {}

    if fk:
        relationship_kwargs.setdefault('foreign_keys',
                                       lambda: getattr(
                                           _get_class_for_table(
                                               model_class,
                                               model_class.__tablename__),
                                           fk))

    elif other_fk:
        relationship_kwargs.setdefault('foreign_keys',
                                       lambda: getattr(
                                           _get_class_for_table(
                                               model_class,
                                               other_table),
                                           other_fk))

    if dict_key:
        relationship_kwargs.setdefault('collection_class',
                                       attribute_mapped_collection(dict_key))

    if other_property is False:
        # No backref
        return relationship(
            lambda: _get_class_for_table(model_class, other_table),
            **relationship_kwargs
        )
    else:
        if other_property is None:
            other_property = model_class.__tablename__
        backref_kwargs = backref_kwargs or {}
        return relationship(
            lambda: _get_class_for_table(model_class, other_table),
            backref=backref(other_property, **backref_kwargs),
            **relationship_kwargs
        )


def _get_class_for_table(model_class, tablename):
    if tablename in (model_class.__name__, model_class.__tablename__):
        return model_class

    for table_cls in model_class._decl_class_registry.values():
        if tablename == getattr(table_cls, '__tablename__', None):
            return table_cls

    raise ValueError('unknown table: {0}'.format(tablename))


def _get_secondary_table(metadata,
                         name,
                         first_column,
                         second_column,
                         first_foreign_key,
                         second_foreign_key):
    return Table(
        name,
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
