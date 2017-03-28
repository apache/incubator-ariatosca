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

import sys
import linecache
import StringIO
import traceback as tb

import jsonpickle

from .console import (puts, indent, Colored)


ENTRY_FORMAT = 'File "{filename}", line {lineno}, in {name}'


def print_exception(e, full=True, cause=False, traceback=None):
    """
    Prints the exception with nice colors and such.
    """
    def format_heading(e):
        return '{0}{1}: {2}'.format(
            Colored.red('Caused by ') if cause else '',
            Colored.red(e.__class__.__name__, bold=True),
            Colored.red(e))

    puts(format_heading(e))
    if full:
        if cause:
            if traceback:
                print_traceback(traceback, True)
        else:
            print_traceback()
    if hasattr(e, 'cause') and e.cause:
        traceback = e.cause_traceback if hasattr(e, 'cause_traceback') else None
        print_exception(e.cause, full=full, cause=True, traceback=traceback)


def print_traceback(traceback=None, print_last_stack=False):
    """
    Prints the traceback with nice colors and such.
    """

    if traceback is None:
        _, _, traceback = sys.exc_info()
    while traceback is not None:
        frame = traceback.tb_frame
        code = frame.f_code
        filename = code.co_filename
        lineno = traceback.tb_lineno
        name = code.co_name
        with indent(2):
            puts(ENTRY_FORMAT.format(filename=Colored.blue(filename),
                                     lineno=Colored.cyan(lineno),
                                     name=Colored.cyan(name)))
            linecache.checkcache(filename)
            line = linecache.getline(filename, lineno, frame.f_globals)
            if line:
                with indent(2):
                    puts(line.strip())
        traceback = traceback.tb_next
        if print_last_stack and (traceback is None):
            # Print stack of *last* traceback
            _print_stack(frame)


def _print_stack(frame):
    entries = tb.extract_stack(frame)
    if not entries:
        return
    puts(Colored.red('Call stack:'))
    with indent(2):
        for filename, lineno, name, line in entries:
            puts(ENTRY_FORMAT.format(filename=Colored.blue(filename),
                                     lineno=Colored.cyan(lineno),
                                     name=Colored.cyan(name)))
            with indent(2):
                puts(line)


def get_exception_as_string(exc_type, exc_val, traceback):
    s_traceback = StringIO.StringIO()
    tb.print_exception(
        etype=exc_type,
        value=exc_val,
        tb=traceback,
        file=s_traceback)
    return s_traceback.getvalue()


class _WrappedException(Exception):

    def __init__(self, exception_type, exception_str):
        super(_WrappedException, self).__init__(exception_type, exception_str)
        self.exception_type = exception_type
        self.exception_str = exception_str


def wrap_if_needed(exception):
    try:
        jsonpickle.loads(jsonpickle.dumps(exception))
        return exception
    except BaseException:
        return _WrappedException(type(exception).__name__, str(exception))
