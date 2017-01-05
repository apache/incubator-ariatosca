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
from sqlalchemy.ext import associationproxy
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Text
)


class ModelMixin(object):

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
            if tablename in (getattr(table_cls, '__name__', None),
                             getattr(table_cls, '__tablename__', None)):
                return table_cls

    @classmethod
    def foreign_key(cls, table, nullable=False):
        """Return a ForeignKey object with the relevant

        :param table: Unique id column in the parent table
        :param nullable: Should the column be allowed to remain empty
        """
        table_cls = cls._get_cls_by_tablename(table.__tablename__)
        foreign_key_str = '{tablename}.{unique_id}'.format(tablename=table_cls.__tablename__,
                                                           unique_id=table_cls.id_column_name())
        column = Column(ForeignKey(foreign_key_str, ondelete='CASCADE'),
                        nullable=nullable)
        column.__remote_table_name = table_cls.__name__
        return column

    @classmethod
    def one_to_many_relationship(cls,
                                 foreign_key_column,
                                 backreference=None):
        """Return a one-to-many SQL relationship object
        Meant to be used from inside the *child* object

        :param parent_class: Class of the parent table
        :param cls: Class of the child table
        :param foreign_key_column: The column of the foreign key (from the child table)
        :param backreference: The name to give to the reference to the child (on the parent table)
        """
        parent_table = cls._get_cls_by_tablename(
            getattr(cls, foreign_key_column).__remote_table_name)
        primaryjoin_str = '{parent_class_name}.{parent_unique_id} == ' \
                          '{child_class.__name__}.{foreign_key_column}'\
            .format(
                parent_class_name=parent_table.__name__,
                parent_unique_id=parent_table.id_column_name(),
                child_class=cls,
                foreign_key_column=foreign_key_column
            )
        return relationship(
            parent_table.__name__,
            primaryjoin=primaryjoin_str,
            foreign_keys=[getattr(cls, foreign_key_column)],
            # The following line make sure that when the *parent* is
            # deleted, all its connected children are deleted as well
            backref=backref(backreference or cls.__tablename__, cascade='all'),
        )

    @classmethod
    def relationship_to_self(cls, local_column):

        remote_side_str = '{cls.__name__}.{remote_column}'.format(
            cls=cls,
            remote_column=cls.id_column_name()
        )
        primaryjoin_str = '{remote_side_str} == {cls.__name__}.{local_column}'.format(
            remote_side_str=remote_side_str,
            cls=cls,
            local_column=local_column)
        return relationship(cls.__name__,
                            primaryjoin=primaryjoin_str,
                            remote_side=remote_side_str,
                            post_update=True)

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
        return fields - set(getattr(cls, '_private_fields', []))

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
