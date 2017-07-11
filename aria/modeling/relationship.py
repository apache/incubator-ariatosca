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
ARIA modeling relationship module
"""

# pylint: disable=invalid-name, redefined-outer-name

from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.ext.associationproxy import association_proxy as original_association_proxy
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Table
)

from ..utils import formatting

NO_BACK_POP = 'NO_BACK_POP'


def foreign_key(other_table, nullable=False):
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

    :param other_table: other table name
    :type other_table: basestring
    :param nullable: ``True`` to allow null values (meaning that there is no relationship)
    :type nullable: bool
    """

    return Column(Integer,
                  ForeignKey('{table}.id'.format(table=other_table), ondelete='CASCADE'),
                  nullable=nullable)


def one_to_one_self(model_class, fk):
    """
    Declare a one-to-one relationship property. The property value would be an instance of the same
    model.

    You will need an associated foreign key to our own table.

    *This utility method should only be used during class creation.*

    :param model_class: class in which this relationship will be declared
    :type model_class: type
    :param fk: foreign key name
    :type fk: basestring
    """

    remote_side = '{model_class}.{remote_column}'.format(
        model_class=model_class.__name__,
        remote_column=model_class.id_column_name()
    )

    primaryjoin = '{remote_side} == {model_class}.{column}'.format(
        remote_side=remote_side,
        model_class=model_class.__name__,
        column=fk
    )
    return _relationship(
        model_class,
        model_class.__tablename__,
        relationship_kwargs={
            'primaryjoin': primaryjoin,
            'remote_side': remote_side,
            'post_update': True
        }
    )


def one_to_one(model_class,
               other_table,
               fk=None,
               other_fk=None,
               back_populates=None):
    """
    Declare a one-to-one relationship property. The property value would be an instance of the other
    table's model.

    You have two options for the foreign key. Either this table can have an associated key to the
    other table (use the ``fk`` argument) or the other table can have an associated foreign key to
    this our table (use the ``other_fk`` argument).

    *This utility method should only be used during class creation.*

    :param model_class: class in which this relationship will be declared
    :type model_class: type
    :param other_table: other table name
    :type other_table: basestring
    :param fk: foreign key name at our table (no need specify if there's no ambiguity)
    :type fk: basestring
    :param other_fk: foreign key name at the other table (no need specify if there's no ambiguity)
    :type other_fk: basestring
    :param back_populates: override name of matching many-to-many property at other table; set to
     ``False`` to disable
    :type back_populates: basestring or bool
    """
    backref_kwargs = None
    if back_populates is not NO_BACK_POP:
        if back_populates is None:
            back_populates = model_class.__tablename__
        backref_kwargs = {'name': back_populates, 'uselist': False}
        back_populates = None

    return _relationship(model_class,
                         other_table,
                         fk=fk,
                         back_populates=back_populates,
                         backref_kwargs=backref_kwargs,
                         other_fk=other_fk)


def one_to_many(model_class,
                other_table=None,
                other_fk=None,
                dict_key=None,
                back_populates=None,
                rel_kwargs=None,
                self=False):
    """
    Declare a one-to-many relationship property. The property value would be a list or dict of
    instances of the child table's model.

    The child table will need an associated foreign key to our table.

    The declaration will automatically create a matching many-to-one property at the child model,
    named after our table name. Use the ``child_property`` argument to override this name.

    *This utility method should only be used during class creation.*

    :param model_class: class in which this relationship will be declared
    :type model_class: type
    :param other_table: other table name
    :type other_table: basestring
    :param other_fk: foreign key name at the other table (no need specify if there's no ambiguity)
    :type other_fk: basestring
    :param dict_key: if set the value will be a dict with this key as the dict key; otherwise will
     be a list
    :type dict_key: basestring
    :param back_populates: override name of matching many-to-one property at other table; set to
     ``False`` to disable
    :type back_populates: basestring or bool
    :param rel_kwargs: additional relationship kwargs to be used by SQLAlchemy
    :type rel_kwargs: dict
    :param self: used for relationships between a table and itself. if set, other_table will
     become the same as the source table.
    :type self: bool
    """
    relationship_kwargs = rel_kwargs or {}
    if self:
        assert other_fk
        other_table_name = model_class.__tablename__
        back_populates = False
        relationship_kwargs['remote_side'] = '{model}.{column}'.format(model=model_class.__name__,
                                                                       column=other_fk)

    else:
        assert other_table
        other_table_name = other_table
        if back_populates is None:
            back_populates = model_class.__tablename__
        relationship_kwargs.setdefault('cascade', 'all')

    return _relationship(
        model_class,
        other_table_name,
        back_populates=back_populates,
        other_fk=other_fk,
        dict_key=dict_key,
        relationship_kwargs=relationship_kwargs)


def many_to_one(model_class,
                parent_table,
                fk=None,
                parent_fk=None,
                back_populates=None):
    """
    Declare a many-to-one relationship property. The property value would be an instance of the
    parent table's model.

    You will need an associated foreign key to the parent table.

    The declaration will automatically create a matching one-to-many property at the child model,
    named after the plural form of our table name. Use the ``parent_property`` argument to override
    this name. Note: the automatic property will always be a SQLAlchemy query object; if you need a
    Python collection then use :func:`one_to_many` at that model.

    *This utility method should only be used during class creation.*

    :param model_class: class in which this relationship will be declared
    :type model_class: type
    :param parent_table: parent table name
    :type parent_table: basestring
    :param fk: foreign key name at our table (no need specify if there's no ambiguity)
    :type fk: basestring
    :param back_populates: override name of matching one-to-many property at parent table; set to
     ``False`` to disable
    :type back_populates: basestring or bool
    """
    if back_populates is None:
        back_populates = formatting.pluralize(model_class.__tablename__)

    return _relationship(model_class,
                         parent_table,
                         back_populates=back_populates,
                         fk=fk,
                         other_fk=parent_fk)


def many_to_many(model_class,
                 other_table=None,
                 prefix=None,
                 dict_key=None,
                 other_property=None,
                 self=False):
    """
    Declare a many-to-many relationship property. The property value would be a list or dict of
    instances of the other table's model.

    You do not need associated foreign keys for this relationship. Instead, an extra table will be
    created for you.

    The declaration will automatically create a matching many-to-many property at the other model,
    named after the plural form of our table name. Use the ``other_property`` argument to override
    this name. Note: the automatic property will always be a SQLAlchemy query object; if you need a
    Python collection then use :func:`many_to_many` again at that model.

    *This utility method should only be used during class creation.*

    :param model_class: class in which this relationship will be declared
    :type model_class: type
    :param other_table: parent table name
    :type other_table: basestring
    :param prefix: optional prefix for extra table name as well as for ``other_property``
    :type prefix: basestring
    :param dict_key: if set the value will be a dict with this key as the dict key; otherwise will
     be a list
    :type dict_key: basestring
    :param other_property: override name of matching many-to-many property at other table; set to
     ``False`` to disable
    :type other_property: basestring or bool
    :param self: used for relationships between a table and itself. if set, other_table will
     become the same as the source table.
    :type self: bool
    """

    this_table = model_class.__tablename__
    this_column_name = '{0}_id'.format(this_table)
    this_foreign_key = '{0}.id'.format(this_table)

    if self:
        other_table = this_table

    other_column_name = '{0}_{1}'.format(other_table, 'self_ref_id' if self else 'id')
    other_foreign_key = '{0}.{1}'.format(other_table, 'id')

    secondary_table_name = '{0}_{1}'.format(this_table, other_table)

    if prefix is not None:
        secondary_table_name = '{0}_{1}'.format(prefix, secondary_table_name)
        if other_property is None:
            other_property = '{0}_{1}'.format(prefix, formatting.pluralize(this_table))

    secondary_table = _get_secondary_table(
        model_class.metadata,
        secondary_table_name,
        this_column_name,
        other_column_name,
        this_foreign_key,
        other_foreign_key
    )

    kwargs = {'relationship_kwargs': {'secondary': secondary_table}}

    if self:
        kwargs['back_populates'] = NO_BACK_POP
        kwargs['relationship_kwargs']['primaryjoin'] = \
                    getattr(model_class, 'id') == getattr(secondary_table.c, this_column_name)
        kwargs['relationship_kwargs']['secondaryjoin'] = \
            getattr(model_class, 'id') == getattr(secondary_table.c, other_column_name)
    else:
        kwargs['backref_kwargs'] = \
            {'name': other_property, 'uselist': True} if other_property else None
        kwargs['dict_key'] = dict_key

    return _relationship(model_class, other_table, **kwargs)


def association_proxy(*args, **kwargs):
    if 'type' in kwargs:
        type_ = kwargs.get('type')
        del kwargs['type']
    else:
        type_ = ':obj:`basestring`'
    proxy = original_association_proxy(*args, **kwargs)
    proxy.__doc__ = """
    Internal. For use in SQLAlchemy queries.

    :type: {0}
    """.format(type_)
    return proxy


def _relationship(model_class,
                  other_table_name,
                  back_populates=None,
                  backref_kwargs=None,
                  relationship_kwargs=None,
                  fk=None,
                  other_fk=None,
                  dict_key=None):
    relationship_kwargs = relationship_kwargs or {}

    if fk:
        relationship_kwargs.setdefault(
            'foreign_keys',
            lambda: getattr(_get_class_for_table(model_class, model_class.__tablename__), fk)
        )

    elif other_fk:
        relationship_kwargs.setdefault(
            'foreign_keys',
            lambda: getattr(_get_class_for_table(model_class, other_table_name), other_fk)
        )

    if dict_key:
        relationship_kwargs.setdefault('collection_class',
                                       attribute_mapped_collection(dict_key))

    if backref_kwargs:
        assert back_populates is None
        return relationship(
            lambda: _get_class_for_table(model_class, other_table_name),
            backref=backref(**backref_kwargs),
            **relationship_kwargs
        )
    else:
        if back_populates is not NO_BACK_POP:
            relationship_kwargs['back_populates'] = back_populates
        return relationship(lambda: _get_class_for_table(model_class, other_table_name),
                            **relationship_kwargs)


def _get_class_for_table(model_class, tablename):
    if tablename in (model_class.__name__, model_class.__tablename__):
        return model_class

    for table_cls in model_class._decl_class_registry.itervalues():
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
        Column(first_column, Integer, ForeignKey(first_foreign_key)),
        Column(second_column, Integer, ForeignKey(second_foreign_key))
    )
