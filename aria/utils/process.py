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
Process utilities.
"""

import os


def append_to_path(*args, **kwargs):
    """
    Appends one or more paths to the system path of an environment.
    The environment will be that of the current process unless another is passed using the
    'env' keyword argument.
    :param args: paths to append
    :param kwargs: 'env' may be used to pass a custom environment to use
    """
    _append_to_path('PATH', *args, **kwargs)


def append_to_pythonpath(*args, **kwargs):
    """
    Appends one or more paths to the python path of an environment.
    The environment will be that of the current process unless another is passed using the
    'env' keyword argument.
    :param args: paths to append
    :param kwargs: 'env' may be used to pass a custom environment to use
    """
    _append_to_path('PYTHONPATH', *args, **kwargs)


def _append_to_path(path, *args, **kwargs):
    env = kwargs.get('env') or os.environ
    env[path] = '{0}{1}{2}'.format(
        os.pathsep.join(args),
        os.pathsep,
        env.get(path, '')
    )
