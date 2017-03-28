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

import os
from datetime import datetime

from prettytable import PrettyTable

from .env import logger


def print_data(columns, items, header_text,
               column_formatters=None, col_max_width=None, defaults=None):
    if items is None:
        items = []
    elif not isinstance(items, list):
        items = [items]

    pretty_table = _generate(columns, data=items, column_formatters=column_formatters,
                             defaults=defaults)
    if col_max_width:
        pretty_table.max_width = col_max_width
    _log(header_text, pretty_table)


def _log(title, table):
    logger.info('{0}{1}{0}{2}{0}'.format(os.linesep, title, table))


def _generate(cols, data, column_formatters=None, defaults=None):
    """
    Return a new PrettyTable instance representing the list.

    Arguments:

        cols - An iterable of strings that specify what
               are the columns of the table.

               for example: ['id','name']

        data - An iterable of dictionaries or objects, each element must
               have keys or attributes corresponding to the cols items.

               for example: [{'id':'123', 'name':'Pete'}]

        column_formatters - A dictionary from a column name to a formatter - a function that
                            may manipulate the string values printed for this column.
                            (See below for a few built-in formatter examples)

                            for example: {'created_at': timestamp_formatter}

        defaults - A dictionary specifying default values for
                   key's that don't exist in the data itself.

                   for example: {'serviceId':'123'} will set the
                   serviceId value for all rows to '123'.

    """
    def get_values_per_column(column, row_data):
        if hasattr(row_data, column) or (isinstance(row_data, dict) and column in row_data):
            val = row_data[column] if isinstance(row_data, dict) else getattr(row_data, column)

            if val and isinstance(val, list):
                val = [str(element) for element in val]
                val = ','.join(val)
            elif val is None or isinstance(val, list):
                # don't print `[]` or `None` (but do print `0`, `False`, etc.)
                val = ''

            if column in column_formatters:
                # calling the user's column formatter to manipulate the value
                val = column_formatters[column](val)

            return val
        else:
            return defaults[column]

    column_formatters = column_formatters or dict()
    pretty_table = PrettyTable(list(cols))

    for datum in data:
        values_row = []
        for col in cols:
            values_row.append(get_values_per_column(col, datum))
        pretty_table.add_row(values_row)

    return pretty_table


def timestamp_formatter(value):
    try:
        datetime.strptime(value[:10], '%Y-%m-%d')
        return value.replace('T', ' ').replace('Z', ' ')
    except ValueError:
        # not a timestamp
        return value


def trim_formatter_generator(max_length):
    def trim_formatter(value):
        if len(value) >= max_length:
            value = '{0}..'.format(value[:max_length - 2])
        return value
    return trim_formatter
