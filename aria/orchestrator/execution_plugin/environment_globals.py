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


def create_initial_globals(path):
    """ emulates a `globals()` call in a freshly loaded module

    The implementation of this function is likely to raise a couple of
    questions. If you read the implementation and nothing bothered you, feel
    free to skip the rest of this docstring.

    First, why is this function in its own module and not, say, in the same
    module of the other environment-related functions?
    Second, why is it implemented in such a way that copies the globals, then
    deletes the item that represents this function, and then changes some
    other entries?

    Well, these two questions can be answered with one (elaborate) explanation.
    If this function was in the same module with the other environment-related
    functions, then we would have had to delete more items in globals than just
    `create_initial_globals`. That is because all of the other function names
    would also be in globals, and since there is no built-in mechanism that
    return the name of the user-defined objects, this approach is quite an
    overkill.

    - But why do we rely on the copy-existing-globals-and-delete-entries
    method, when it seems to force us to put `create_initial_globals` in its
    own file?

    Well, because there is no easier method of creating globals of a newly
    loaded module.

    - How about hard coding a 'global' dict? It seems that there are very few
    entries: __doc__, __file__, __name__, __package__ (but don't forget
    __builtins__).

    That would be coupling our implementation to a specific `globals`
    implementation. What if `globals` were to change?
    """
    copied_globals = globals().copy()
    copied_globals.update({
        '__doc__': 'Dynamically executed script',
        '__file__': path,
        '__name__': '__main__',
        '__package__': None
    })
    del copied_globals[create_initial_globals.__name__]
    return copied_globals
