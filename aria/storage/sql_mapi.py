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
SQLAlchemy based MAPI
"""
import os
import platform

from sqlalchemy import (
    create_engine,
    orm,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import StaleDataError

from aria.utils.collections import OrderedDict
from . import (
    api,
    exceptions,
)


class SQLAlchemyModelAPI(api.ModelAPI):
    """
    SQL based MAPI.
    """

    def __init__(self,
                 engine,
                 session,
                 **kwargs):
        super(SQLAlchemyModelAPI, self).__init__(**kwargs)
        self._engine = engine
        self._session = session

    def get(self, entry_id, include=None, **kwargs):
        """Return a single result based on the model class and element ID
        """
        query = self._get_query(include, {'id': entry_id})
        result = query.first()

        if not result:
            raise exceptions.StorageError(
                'Requested `{0}` with ID `{1}` was not found'
                .format(self.model_cls.__name__, entry_id)
            )
        return result

    def get_by_name(self, entry_name, include=None, **kwargs):
        assert hasattr(self.model_cls, 'name')
        result = self.list(include=include, filters={'name': entry_name})
        if not result:
            raise exceptions.StorageError(
                'Requested {0} with NAME `{1}` was not found'
                .format(self.model_cls.__name__, entry_name)
            )
        elif len(result) > 1:
            raise exceptions.StorageError(
                'Requested {0} with NAME `{1}` returned more than 1 value'
                .format(self.model_cls.__name__, entry_name)
            )
        else:
            return result[0]

    def list(self,
             include=None,
             filters=None,
             pagination=None,
             sort=None,
             **kwargs):
        query = self._get_query(include, filters, sort)

        results, total, size, offset = self._paginate(query, pagination)

        return ListResult(
            items=results,
            metadata=dict(total=total,
                          size=size,
                          offset=offset)
        )

    def iter(self,
             include=None,
             filters=None,
             sort=None,
             **kwargs):
        """Return a (possibly empty) list of `model_class` results
        """
        return iter(self._get_query(include, filters, sort))

    def put(self, entry, **kwargs):
        """Create a `model_class` instance from a serializable `model` object

        :param entry: A dict with relevant kwargs, or an instance of a class
        that has a `to_dict` method, and whose attributes match the columns
        of `model_class` (might also my just an instance of `model_class`)
        :return: An instance of `model_class`
        """
        self._session.add(entry)
        self._safe_commit()
        return entry

    def delete(self, entry, **kwargs):
        """Delete a single result based on the model class and element ID
        """
        self._load_relationships(entry)
        self._session.delete(entry)
        self._safe_commit()
        return entry

    def update(self, entry, **kwargs):
        """Add `instance` to the DB session, and attempt to commit

        :return: The updated instance
        """
        return self.put(entry)

    def refresh(self, entry):
        """Reload the instance with fresh information from the DB

        :param entry: Instance to be re-loaded from the DB
        :return: The refreshed instance
        """
        self._session.refresh(entry)
        self._load_relationships(entry)
        return entry

    def _destroy_connection(self):
        pass

    def _establish_connection(self):
        pass

    def create(self, checkfirst=True, create_all=True, **kwargs):
        self.model_cls.__table__.create(self._engine, checkfirst=checkfirst)

        if create_all:
            # In order to create any models created dynamically (e.g. many-to-many helper tables are
            # created at runtime).
            self.model_cls.metadata.create_all(bind=self._engine, checkfirst=checkfirst)

    def drop(self):
        """
        Drop the table from the storage.
        :return:
        """
        self.model_cls.__table__.drop(self._engine)

    def _safe_commit(self):
        """Try to commit changes in the session. Roll back if exception raised
        Excepts SQLAlchemy errors and rollbacks if they're caught
        """
        try:
            self._session.commit()
        except StaleDataError as e:
            self._session.rollback()
            raise exceptions.StorageError('Version conflict: {0}'.format(str(e)))
        except (SQLAlchemyError, ValueError) as e:
            self._session.rollback()
            raise exceptions.StorageError('SQL Storage error: {0}'.format(str(e)))

    def _get_base_query(self, include, joins):
        """Create the initial query from the model class and included columns

        :param include: A (possibly empty) list of columns to include in
        the query
        :return: An SQLAlchemy AppenderQuery object
        """
        # If only some columns are included, query through the session object
        if include:
            # Make sure that attributes come before association proxies
            include.sort(key=lambda x: x.is_clause_element)
            query = self._session.query(*include)
        else:
            # If all columns should be returned, query directly from the model
            query = self._session.query(self.model_cls)

        query = query.join(*joins)
        return query

    @staticmethod
    def _get_joins(model_class, columns):
        """Get a list of all the tables on which we need to join

        :param columns: A set of all attributes involved in the query
        """

        # Using a list instead of a set because order is important
        joins = OrderedDict()
        for column_name in columns:
            column = getattr(model_class, column_name)
            while not column.is_attribute:
                join_attr = column.local_attr
                # This is a hack, to deal with the fact that SQLA doesn't
                # fully support doing something like: `if join_attr in joins`,
                # because some SQLA elements have their own comparators
                join_attr_name = str(join_attr)
                if join_attr_name not in joins:
                    joins[join_attr_name] = join_attr
                column = column.remote_attr

        return joins.values()

    @staticmethod
    def _sort_query(query, sort=None):
        """Add sorting clauses to the query

        :param query: Base SQL query
        :param sort: An optional dictionary where keys are column names to
        sort by, and values are the order (asc/desc)
        :return: An SQLAlchemy AppenderQuery object
        """
        if sort:
            for column, order in sort.items():
                if order == 'desc':
                    column = column.desc()
                query = query.order_by(column)
        return query

    def _filter_query(self, query, filters):
        """Add filter clauses to the query

        :param query: Base SQL query
        :param filters: An optional dictionary where keys are column names to
        filter by, and values are values applicable for those columns (or lists
        of such values)
        :return: An SQLAlchemy AppenderQuery object
        """
        return self._add_value_filter(query, filters)

    @staticmethod
    def _add_value_filter(query, filters):
        for column, value in filters.items():
            if isinstance(value, (list, tuple)):
                query = query.filter(column.in_(value))
            else:
                query = query.filter(column == value)

        return query

    def _get_query(self,
                   include=None,
                   filters=None,
                   sort=None):
        """Get an SQL query object based on the params passed

        :param model_class: SQL DB table class
        :param include: An optional list of columns to include in the query
        :param filters: An optional dictionary where keys are column names to
        filter by, and values are values applicable for those columns (or lists
        of such values)
        :param sort: An optional dictionary where keys are column names to
        sort by, and values are the order (asc/desc)
        :return: A sorted and filtered query with only the relevant
        columns
        """
        include, filters, sort, joins = self._get_joins_and_converted_columns(
            include, filters, sort
        )

        query = self._get_base_query(include, joins)
        query = self._filter_query(query, filters)
        query = self._sort_query(query, sort)
        return query

    def _get_joins_and_converted_columns(self,
                                         include,
                                         filters,
                                         sort):
        """Get a list of tables on which we need to join and the converted
        `include`, `filters` and `sort` arguments (converted to actual SQLA
        column/label objects instead of column names)
        """
        include = include or []
        filters = filters or dict()
        sort = sort or OrderedDict()

        all_columns = set(include) | set(filters.keys()) | set(sort.keys())
        joins = self._get_joins(self.model_cls, all_columns)

        include, filters, sort = self._get_columns_from_field_names(
            include, filters, sort
        )
        return include, filters, sort, joins

    def _get_columns_from_field_names(self,
                                      include,
                                      filters,
                                      sort):
        """Go over the optional parameters (include, filters, sort), and
        replace column names with actual SQLA column objects
        """
        include = [self._get_column(c) for c in include]
        filters = dict((self._get_column(c), filters[c]) for c in filters)
        sort = OrderedDict((self._get_column(c), sort[c]) for c in sort)

        return include, filters, sort

    def _get_column(self, column_name):
        """Return the column on which an action (filtering, sorting, etc.)
        would need to be performed. Can be either an attribute of the class,
        or an association proxy linked to a relationship the class has
        """
        column = getattr(self.model_cls, column_name)
        if column.is_attribute:
            return column
        else:
            # We need to get to the underlying attribute, so we move on to the
            # next remote_attr until we reach one
            while not column.remote_attr.is_attribute:
                column = column.remote_attr
            # Put a label on the remote attribute with the name of the column
            return column.remote_attr.label(column_name)

    @staticmethod
    def _paginate(query, pagination):
        """Paginate the query by size and offset

        :param query: Current SQLAlchemy query object
        :param pagination: An optional dict with size and offset keys
        :return: A tuple with four elements:
        - res ults: `size` items starting from `offset`
        - the total count of items
        - `size` [default: 0]
        - `offset` [default: 0]
        """
        if pagination:
            size = pagination.get('size', 0)
            offset = pagination.get('offset', 0)
            total = query.order_by(None).count()  # Fastest way to count
            results = query.limit(size).offset(offset).all()
            return results, total, size, offset
        else:
            results = query.all()
            return results, len(results), 0, 0

    @staticmethod
    def _load_relationships(instance):
        """A helper method used to overcome a problem where the relationships
        that rely on joins aren't being loaded automatically
        """
        for rel in instance.__mapper__.relationships:
            getattr(instance, rel.key)


def init_storage(base_dir, filename='db.sqlite'):
    """
    A builtin ModelStorage initiator.
    Creates a sqlalchemy engine and a session to be passed to the mapi.

    Initiator_kwargs must be passed to the ModelStorage which must hold the base_dir for the
    location of the db file, and an option filename. This would create an sqlite db.
    :param base_dir: the dir of the db
    :param filename: the db file name.
    :return:
    """
    uri = 'sqlite:///{platform_char}{path}'.format(
        # Handles the windows behavior where there is not root, but drivers.
        # Thus behaving as relative path.
        platform_char='' if 'Windows' in platform.system() else '/',

        path=os.path.join(base_dir, filename))

    engine = create_engine(uri)
    session_factory = orm.sessionmaker(bind=engine)
    session = orm.scoped_session(session_factory=session_factory)

    return dict(engine=engine, session=session)


class ListResult(object):
    """
    a ListResult contains results about the requested items.
    """
    def __init__(self, items, metadata):
        self.items = items
        self.metadata = metadata

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def __getitem__(self, item):
        return self.items[item]
