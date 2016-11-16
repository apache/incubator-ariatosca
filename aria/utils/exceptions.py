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

from clint.textui import indent
from .console import (puts, Colored)


def print_exception(e, full=True, cause=False, traceback=None):
    """
    Prints the exception with nice colors and such.
    """
    def format_heading(e):
        return '%s%s: %s' % (Colored.red('Caused by ') if cause else '', Colored.red(
            e.__class__.__name__, bold=True), Colored.red(e))

    puts(format_heading(e))
    if full:
        if cause:
            if traceback:
                print_traceback(traceback)
        else:
            print_traceback()
    if hasattr(e, 'cause') and e.cause:
        traceback = e.cause_traceback if hasattr(e, 'cause_traceback') else None
        print_exception(e.cause, full=full, cause=True, traceback=traceback)

def print_traceback(traceback=None):
    """
    Prints the traceback with nice colors and such.
    """

    if traceback is None:
        _, _, traceback = sys.exc_info()
    while traceback is not None:
        frame = traceback.tb_frame
        lineno = traceback.tb_lineno
        code = frame.f_code
        filename = code.co_filename
        name = code.co_name
        with indent(2):
            puts('File "%s", line %s, in %s' % (Colored.blue(filename),
                                                Colored.cyan(lineno),
                                                Colored.cyan(name)))
            linecache.checkcache(filename)
            line = linecache.getline(filename, lineno, frame.f_globals)
            if line:
                with indent(2):
                    puts(Colored.black(line.strip()))
        traceback = traceback.tb_next
