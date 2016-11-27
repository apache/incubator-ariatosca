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
import json

from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
# pylint: disable=unused-import
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import (
    schema,
    VARCHAR,
    ARRAY,
    Column,
    Integer,
    Text,
    DateTime,
    Boolean,
    Enum,
    String,
    PickleType,
    Float,
    TypeDecorator,
    ForeignKey,
    orm,
)

from aria.storage import exceptions

Model = declarative_base()


def foreign_key(foreign_key_column, nullable=False):
    """Return a ForeignKey object with the relevant

    :param foreign_key_column: Unique id column in the parent table
    :param nullable: Should the column be allowed to remain empty
    """
    return Column(
        ForeignKey(foreign_key_column, ondelete='CASCADE'),
        nullable=nullable
    )


def one_to_many_relationship(child_class,
                             parent_class,
                             foreign_key_column,
                             backreference=None):
    """Return a one-to-many SQL relationship object
    Meant to be used from inside the *child* object

    :param parent_class: Class of the parent table
    :param child_class: Class of the child table
    :param foreign_key_column: The column of the foreign key
    :param backreference: The name to give to the reference to the child
    """
    backreference = backreference or child_class.__tablename__
    return relationship(
        parent_class,
        primaryjoin=lambda: parent_class.id == foreign_key_column,
        # The following line make sure that when the *parent* is
        # deleted, all its connected children are deleted as well
        backref=backref(backreference, cascade='all')
    )


def relationship_to_self(self_cls, parent_key, self_key):
    return relationship(
        self_cls,
        foreign_keys=parent_key,
        remote_side=self_key
    )


class _MutableType(TypeDecorator):
    """
    Dict representation of type.
    """
    @property
    def python_type(self):
        raise NotImplementedError

    def process_literal_param(self, value, dialect):
        pass

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class _DictType(_MutableType):
    @property
    def python_type(self):
        return dict


class _ListType(_MutableType):
    @property
    def python_type(self):
        return list


class _MutableDict(Mutable, dict):
    """
    Enables tracking for dict values.
    """
    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to MutableDict."

        if not isinstance(value, _MutableDict):
            if isinstance(value, dict):
                return _MutableDict(value)

            # this call will raise ValueError
            try:
                return Mutable.coerce(key, value)
            except ValueError as e:
                raise exceptions.StorageError('SQL Storage error: {0}'.format(str(e)))
        else:
            return value

    def __setitem__(self, key, value):
        "Detect dictionary set events and emit change events."

        dict.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        "Detect dictionary del events and emit change events."

        dict.__delitem__(self, key)
        self.changed()


class _MutableList(Mutable, list):

    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to MutableDict."

        if not isinstance(value, _MutableList):
            if isinstance(value, list):
                return _MutableList(value)

            # this call will raise ValueError
            try:
                return Mutable.coerce(key, value)
            except ValueError as e:
                raise exceptions.StorageError('SQL Storage error: {0}'.format(str(e)))
        else:
            return value

    def __setitem__(self, key, value):
        list.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        list.__delitem__(self, key)


Dict = _MutableDict.as_mutable(_DictType)
List = _MutableList.as_mutable(_ListType)


class SQLModelBase(Model):
    """
    Abstract base class for all SQL models that allows [de]serialization
    """
    # SQLAlchemy syntax
    __abstract__ = True

    # This would be overridden once the models are created. Created for pylint.
    __table__ = None

    _private_fields = []

    id = Column(Integer, primary_key=True, autoincrement=True)

    def to_dict(self, suppress_error=False):
        """Return a dict representation of the model

        :param suppress_error: If set to True, sets `None` to attributes that
        it's unable to retrieve (e.g., if a relationship wasn't established
        yet, and so it's impossible to access a property through it)
        """
        if suppress_error:
            res = dict()
            for field in self.fields():
                try:
                    field_value = getattr(self, field)
                except AttributeError:
                    field_value = None
                res[field] = field_value
        else:
            # Can't simply call here `self.to_response()` because inheriting
            # class might override it, but we always need the same code here
            res = dict((f, getattr(self, f)) for f in self.fields())
        return res

    @classmethod
    def fields(cls):
        """Return the list of field names for this table

        Mostly for backwards compatibility in the code (that uses `fields`)
        """
        return set(cls.__table__.columns.keys()) - set(cls._private_fields)

    def __repr__(self):
        return '<{0} id=`{1}`>'.format(self.__class__.__name__, self.id)
