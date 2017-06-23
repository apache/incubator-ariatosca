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
SQLAlchemy implementation of the storage model API ("MAPI").
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
    collection_instrumentation
)

_predicates = {'ge': '__ge__',
               'gt': '__gt__',
               'lt': '__lt__',
               'le': '__le__',
               'eq': '__eq__',
               'ne': '__ne__'}


class SQLAlchemyModelAPI(api.ModelAPI):
    """
    SQLAlchemy implementation of the storage model API ("MAPI").
    """

    def __init__(self,
                 engine,
                 session,
                 **kwargs):
        super(SQLAlchemyModelAPI, self).__init__(**kwargs)
        self._engine = engine
        self._session = session

    def get(self, entry_id, include=None, **kwargs):
        """
        Returns a single result based on the model class and element ID
        """
        query = self._get_query(include, {'id': entry_id})
        result = query.first()

        if not result:
            raise exceptions.NotFoundError(
                'Requested `{0}` with ID `{1}` was not found'
                .format(self.model_cls.__name__, entry_id)
            )
        return self._instrument(result)

    def get_by_name(self, entry_name, include=None, **kwargs):
        assert hasattr(self.model_cls, 'name')
        result = self.list(include=include, filters={'name': entry_name})
        if not result:
            raise exceptions.NotFoundError(
                'Requested {0} with name `{1}` was not found'
                .format(self.model_cls.__name__, entry_name)
            )
        elif len(result) > 1:
            raise exceptions.StorageError(
                'Requested {0} with name `{1}` returned more than 1 value'
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
            dict(total=total, size=size, offset=offset),
            [self._instrument(result) for result in results]
        )

    def iter(self,
             include=None,
             filters=None,
             sort=None,
             **kwargs):
        """
        Returns a (possibly empty) list of ``model_class`` results.
        """
        for result in self._get_query(include, filters, sort):
            yield self._instrument(result)

    def put(self, entry, **kwargs):
        """
        Creatse a ``model_class`` instance from a serializable ``model`` object.

        :param entry: dict with relevant kwargs, or an instance of a class that has a ``to_dict``
         method, and whose attributes match the columns of ``model_class`` (might also be just an
         instance of ``model_class``)
        :return: an instance of ``model_class``
        """
        self._session.add(entry)
        self._safe_commit()
        return entry

    def delete(self, entry, **kwargs):
        """
        Deletes a single result based on the model class and element ID.
        """
        self._load_relationships(entry)
        self._session.delete(entry)
        self._safe_commit()
        return entry

    def update(self, entry, **kwargs):
        """
        Adds ``instance`` to the database session, and attempts to commit.

        :return: updated instance
        """
        return self.put(entry)

    def refresh(self, entry):
        """
        Reloads the instance with fresh information from the database.

        :param entry: instance to be re-loaded from the database
        :return: refreshed instance
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
        Drops the table.
        """
        self.model_cls.__table__.drop(self._engine)

    def _safe_commit(self):
        """
        Try to commit changes in the session. Roll back if exception raised SQLAlchemy errors and
        rolls back if they're caught.
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
        """
        Create the initial query from the model class and included columns.

        :param include: (possibly empty) list of columns to include in the query
        :return: SQLAlchemy AppenderQuery object
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
        """
        Gets a list of all the tables on which we need to join.

        :param columns: set of all attributes involved in the query
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
        """
        Adds sorting clauses to the query.

        :param query: base SQL query
        :param sort: optional dictionary where keys are column names to sort by, and values are
         the order (asc/desc)
        :return: SQLAlchemy AppenderQuery object
        """
        if sort:
            for column, order in sort.items():
                if order == 'desc':
                    column = column.desc()
                query = query.order_by(column)
        return query

    def _filter_query(self, query, filters):
        """
        Adds filter clauses to the query.

        :param query: base SQL query
        :param filters: optional dictionary where keys are column names to filter by, and values
         are values applicable for those columns (or lists of such values)
        :return: SQLAlchemy AppenderQuery object
        """
        return self._add_value_filter(query, filters)

    @staticmethod
    def _add_value_filter(query, filters):
        for column, value in filters.items():
            if isinstance(value, dict):
                for predicate, operand in value.items():
                    query = query.filter(getattr(column, predicate)(operand))
            elif isinstance(value, (list, tuple)):
                query = query.filter(column.in_(value))
            else:
                query = query.filter(column == value)

        return query

    def _get_query(self,
                   include=None,
                   filters=None,
                   sort=None):
        """
        Gets a SQL query object based on the params passed.

        :param model_class: SQL database table class
        :param include: optional list of columns to include in the query
        :param filters: optional dictionary where keys are column names to filter by, and values
         are values applicable for those columns (or lists of such values)
        :param sort: optional dictionary where keys are column names to sort by, and values are the
         order (asc/desc)
        :return: sorted and filtered query with only the relevant columns
        """
        include, filters, sort, joins = self._get_joins_and_converted_columns(
            include, filters, sort
        )
        filters = self._convert_operands(filters)

        query = self._get_base_query(include, joins)
        query = self._filter_query(query, filters)
        query = self._sort_query(query, sort)
        return query

    @staticmethod
    def _convert_operands(filters):
        for column, conditions in filters.items():
            if isinstance(conditions, dict):
                for predicate, operand in conditions.items():
                    if predicate not in _predicates:
                        raise exceptions.StorageError(
                            "{0} is not a valid predicate for filtering. Valid predicates are {1}"
                            .format(predicate, ', '.join(_predicates.keys())))
                    del filters[column][predicate]
                    filters[column][_predicates[predicate]] = operand


        return filters

    def _get_joins_and_converted_columns(self,
                                         include,
                                         filters,
                                         sort):
        """
        Gets a list of tables on which we need to join and the converted ``include``, ``filters``
        and ```sort`` arguments (converted to actual SQLAlchemy column/label objects instead of
        column names).
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
        """
        Gooes over the optional parameters (include, filters, sort), and replace column names with
        actual SQLAlechmy column objects.
        """
        include = [self._get_column(c) for c in include]
        filters = dict((self._get_column(c), filters[c]) for c in filters)
        sort = OrderedDict((self._get_column(c), sort[c]) for c in sort)

        return include, filters, sort

    def _get_column(self, column_name):
        """
        Returns the column on which an action (filtering, sorting, etc.) would need to be performed.
        Can be either an attribute of the class, or an association proxy linked to a relationship
        in the class.
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
        """
        Paginates the query by size and offset.

        :param query: current SQLAlchemy query object
        :param pagination: optional dict with size and offset keys
        :return: tuple with four elements:
         * results: ``size`` items starting from ``offset``
         * the total count of items
         * ``size`` [default: 0]
         * ``offset`` [default: 0]
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
        """
        Helper method used to overcome a problem where the relationships that rely on joins aren't
        being loaded automatically.
        """
        for rel in instance.__mapper__.relationships:
            getattr(instance, rel.key)

    def _instrument(self, model):
        if self._instrumentation:
            return collection_instrumentation.instrument(self._instrumentation, model, self)
        else:
            return model


def init_storage(base_dir, filename='db.sqlite'):
    """
    Built-in ModelStorage initiator.

    Creates a SQLAlchemy engine and a session to be passed to the MAPI.

    ``initiator_kwargs`` must be passed to the ModelStorage which must hold the ``base_dir`` for the
    location of the database file, and an option filename. This would create an SQLite database.

    :param base_dir: directory of the database
    :param filename: database file name.
    :return:
    """
    uri = 'sqlite:///{platform_char}{path}'.format(
        # Handles the windows behavior where there is not root, but drivers.
        # Thus behaving as relative path.
        platform_char='' if 'Windows' in platform.system() else '/',

        path=os.path.join(base_dir, filename))

    engine = create_engine(uri, connect_args=dict(timeout=15))

    session_factory = orm.sessionmaker(bind=engine)
    session = orm.scoped_session(session_factory=session_factory)

    return dict(engine=engine, session=session)


class ListResult(list):
    """
    Contains results about the requested items.
    """
    def __init__(self, metadata, *args, **qwargs):
        super(ListResult, self).__init__(*args, **qwargs)
        self.metadata = metadata
        self.items = self
