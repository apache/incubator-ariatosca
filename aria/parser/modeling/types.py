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

from ...utils.collections import StrictList, StrictDict, OrderedDict
from ...utils.formatting import as_raw
from ...utils.console import puts


class Type(object):
    """
    Represents a type and its children.
    """

    def __init__(self, name):
        if not isinstance(name, basestring):
            raise ValueError('must set name (string)')

        self.name = name
        self.description = None
        self.children = StrictList(value_class=Type)

    def get_parent(self, name):
        for child in self.children:
            if child.name == name:
                return self
            parent = child.get_parent(name)
            if parent is not None:
                return parent
        return None

    def get_descendant(self, name):
        if self.name == name:
            return self
        for child in self.children:
            found = child.get_descendant(name)
            if found is not None:
                return found
        return None

    def is_descendant(self, base_name, name):
        base = self.get_descendant(base_name)
        if base is not None:
            if base.get_descendant(name) is not None:
                return True
        return False

    def iter_descendants(self):
        for child in self.children:
            yield child
            for descendant in child.iter_descendants():
                yield descendant

    @property
    def as_raw(self):
        return OrderedDict((
            ('name', self.name),
            ('description', self.description)))

    def dump(self, context):
        if self.name:
            puts(context.style.type(self.name))
        with context.style.indent:
            for child in self.children:
                child.dump(context)

    def append_raw_children(self, types):
        for child in self.children:
            raw_child = as_raw(child)
            raw_child['parent'] = self.name
            types.append(raw_child)
            child.append_raw_children(types)


class RelationshipType(Type):
    def __init__(self, name):
        super(RelationshipType, self).__init__(name)

        self.properties = StrictDict(key_class=basestring)
        self.source_interfaces = StrictDict(key_class=basestring)
        self.target_interfaces = StrictDict(key_class=basestring)


class PolicyType(Type):
    def __init__(self, name):
        super(PolicyType, self).__init__(name)

        self.implementation = None
        self.properties = StrictDict(key_class=basestring)


class PolicyTriggerType(Type):
    def __init__(self, name):
        super(PolicyTriggerType, self).__init__(name)

        self.implementation = None
        self.properties = StrictDict(key_class=basestring)


class TypeHierarchy(Type):
    """
    Represents a single-parent derivation :class:`Type` hierarchy.
    """

    def __init__(self):
        super(TypeHierarchy, self).__init__(name='')
        self.name = None  # TODO Calling the super __init__ with name='' and then setting it to None
        # is an ugly workaround. We need to improve this. here is the reason for the current state:
        # In this module there is a class named `Type`. Its `__init__` gets has a `name` argument
        # that raises an exception of `name` is not an instance of `basestring`. Here are some
        # classes that inherit from `Type`: RelationshipType, PolicyType, PolicyTriggerType.
        # But `TypeHierarchy` also inherits from `Type`. And its `__init__` does not call its super
        # `__init__`, which causes pylint to yell. As you can clearly see, it also sets `name` to
        # None. But calling super __init__ with name=None raises an exception. We tried modifying
        # the Type class hierarchies, but it was not that simple. Also calling with name='' without
        # setting `name` to None later on raises parsing validation issues.
        self.children = StrictList(value_class=Type)

    @property
    def as_raw(self):
        types = []
        self.append_raw_children(types)
        return types
