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


def generate(cols, data, defaults=None):
    """
    Return a new PrettyTable instance representing the list.

    Arguments:

        cols - An iterable of strings that specify what
               are the columns of the table.

               for example: ['id','name']

        data - An iterable of dictionaries, each dictionary must
               have key's corresponding to the cols items.

               for example: [{'id':'123', 'name':'Pete']

        defaults - A dictionary specifying default values for
                   key's that don't exist in the data itself.

                   for example: {'serviceId':'123'} will set the
                   serviceId value for all rows to '123'.

    """
    def get_values_per_column(column, row_data):
        if column in row_data:
            if row_data[column] and isinstance(row_data[column], basestring):
                try:
                    datetime.strptime(row_data[column][:10], '%Y-%m-%d')
                    row_data[column] = \
                        row_data[column].replace('T', ' ').replace('Z', ' ')
                except ValueError:
                    # not a timestamp
                    pass
            elif row_data[column] and isinstance(row_data[column], list):
                row_data[column] = ','.join(row_data[column])
            elif not row_data[column]:
                # if it's empty list, don't print []
                row_data[column] = ''
            return row_data[column]
        else:
            return defaults[column]

    pretty_table = PrettyTable([col for col in cols])

    for datum in data:
        values_row = []
        for col in cols:
            values_row.append(get_values_per_column(col, datum))
        pretty_table.add_row(values_row)

    return pretty_table


def log(title, table):
    logger.info('{0}{1}{0}{2}{0}'.format(os.linesep, title, table))


def print_data(columns, items, header_text, max_width=None, defaults=None):
    if items is None:
        items = []
    elif not isinstance(items, list):
        items = [items]

    pretty_table = generate(columns, data=items, defaults=defaults)
    if max_width:
        pretty_table.max_width = max_width
    log(header_text, pretty_table)
