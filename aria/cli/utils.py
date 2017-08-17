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
Miscellaneous CLI utilities.
"""

import os
import sys
from StringIO import StringIO

from backports.shutil_get_terminal_size import get_terminal_size

from .env import logger
from .exceptions import AriaCliError
from ..utils import http


def storage_sort_param(sort_by, descending):
    return {sort_by: 'desc' if descending else 'asc'}


def get_parameter_templates_as_string(parameter_templates):
    params_string = StringIO()

    for param_name, param_template in parameter_templates.iteritems():
        params_string.write('\t{0}:{1}'.format(param_name, os.linesep))
        param_dict = param_template.to_dict()
        del param_dict['id']  # not interested in printing the id
        for k, v in param_dict.iteritems():
            params_string.write('\t\t{0}: {1}{2}'.format(k, v, os.linesep))

    params_string.write(os.linesep)
    return params_string.getvalue()


def check_overriding_storage_exceptions(e, model_class, name):
    """
    Checks whether the storage exception is a known type where we'd like to override the exception
    message; If so, it raises a new error. Otherwise it simply returns.
    """
    assert isinstance(e, BaseException)
    if 'UNIQUE constraint failed' in e.message:
        new_message = \
            'Could not store {model_class} `{name}`{linesep}' \
            'There already a exists a {model_class} with the same name' \
                .format(model_class=model_class, name=name, linesep=os.linesep)
        trace = sys.exc_info()[2]
        raise type(e), type(e)(new_message), trace                                                  # pylint: disable=raising-non-exception


def download_file(url):
    progress_bar = generate_progress_handler(url, 'Downloading')
    try:
        destination = http.download_file(url, logger=logger, progress_handler=progress_bar)
    except Exception as e:
        raise AriaCliError(
            'Failed to download {0}. ({1})'.format(url, str(e)))
    return destination


def generate_progress_handler(file_path, action='', max_bar_length=80):
    """
    Returns a function that prints a progress bar in the terminal.

    :param file_path: the name of the file being transferred
    :param action: uploading/downloading
    :param max_bar_length: maximum allowed length of the bar
    :return: configured ``print_progress`` function
    """
    # We want to limit the maximum line length to 80, but allow for a smaller terminal size. We also
    # include the action string, and some extra chars
    terminal_width = get_terminal_size().columns

    # This takes care of the case where there is no terminal (e.g. unittest)
    terminal_width = terminal_width or max_bar_length
    bar_length = min(max_bar_length, terminal_width) - len(action) - 12

    # Shorten the file name if it's too long
    file_name = os.path.basename(file_path)
    if len(file_name) > (bar_length / 4) + 3:
        file_name = file_name[:bar_length / 4] + '...'

    bar_length -= len(file_name)

    def print_progress(read_bytes, total_bytes):
        """
        Print upload/download progress on a single line.

        Call this function in a loop to create a progress bar in the terminal.

        :param read_bytes: number of bytes already processed
        :param total_bytes: total number of bytes in the file
        """

        filled_length = min(bar_length, int(round(bar_length * read_bytes / float(total_bytes))))
        percents = min(100.00, round(100.00 * (read_bytes / float(total_bytes)), 2))
        bar = '#' * filled_length + '-' * (bar_length - filled_length)                              # pylint: disable=blacklisted-name

        # The \r caret makes sure the cursor moves back to the beginning of the line
        sys.stdout.write('\r{0} {1} |{2}| {3}%'.format(action, file_name, bar, percents))
        if read_bytes >= total_bytes:
            sys.stdout.write(os.linesep)

    return print_progress
