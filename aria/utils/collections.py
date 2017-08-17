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
Additional collection classes and collection utilities.
"""

from __future__ import absolute_import  # so we can import standard 'collections'

try:
    import cPickle as pickle
except ImportError:
    import pickle

from copy import deepcopy
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict


def cls_name(cls):
    module = str(cls.__module__)
    name = str(cls.__name__)
    return name if module == '__builtin__' else '{0}.{1}'.format(module, name)


class FrozenList(list):
    """
    An immutable list.

    After initialization it will raise :class:`~exceptions.TypeError` exceptions if modification is
    attempted.

    Note that objects stored in the list may not be immutable.
    """
    def __init__(self, *args, **kwargs):
        self.locked = False
        super(FrozenList, self).__init__(*args, **kwargs)
        self.locked = True

    def __setitem__(self, index, value):
        if self.locked:
            raise TypeError('frozen list')
        return super(FrozenList, self).__setitem__(index, value)

    def __delitem__(self, index):
        if self.locked:
            raise TypeError('frozen list')
        return super(FrozenList, self).__delitem__(index)

    def __iadd__(self, values):
        if self.locked:
            raise TypeError('frozen list')
        return super(FrozenList, self).__iadd__(values)

    def __deepcopy__(self, memo):
        res = [deepcopy(v, memo) for v in self]
        return FrozenList(res)

    def append(self, value):
        if self.locked:
            raise TypeError('frozen list')
        return super(FrozenList, self).append(value)

    def extend(self, values):
        if self.locked:
            raise TypeError('frozen list')
        return super(FrozenList, self).append(values)

    def insert(self, index, value):
        if self.locked:
            raise TypeError('frozen list')
        return super(FrozenList, self).insert(index, value)

EMPTY_READ_ONLY_LIST = FrozenList()


class FrozenDict(OrderedDict):
    """
    An immutable ordered dict.

    After initialization it will raise :class:`~exceptions.TypeError` exceptions if modification is
    attempted.

    Note that objects stored in the dict may not be immutable.
    """

    def __init__(self, *args, **kwargs):
        self.locked = False
        super(FrozenDict, self).__init__(*args, **kwargs)
        self.locked = True

    def __setitem__(self, key, value, **_):
        if self.locked:
            raise TypeError('frozen dict')
        return super(FrozenDict, self).__setitem__(key, value)

    def __delitem__(self, key, **_):
        if self.locked:
            raise TypeError('frozen dict')
        return super(FrozenDict, self).__delitem__(key)

    def __deepcopy__(self, memo):
        res = [(deepcopy(k, memo), deepcopy(v, memo)) for k, v in self.iteritems()]
        return FrozenDict(res)

EMPTY_READ_ONLY_DICT = FrozenDict()


class StrictList(list):
    """
    A list that raises :class:`~exceptions.TypeError` exceptions when objects of the wrong type are
    inserted.
    """

    def __init__(self,
                 items=None,
                 value_class=None,
                 wrapper_function=None,
                 unwrapper_function=None):
        super(StrictList, self).__init__()
        if isinstance(items, StrictList):
            self.value_class = items.value_class
            self.wrapper_function = items.wrapper_function
            self.unwrapper_function = items.unwrapper_function
        self.value_class = value_class
        self.wrapper_function = wrapper_function
        self.unwrapper_function = unwrapper_function
        if items:
            for item in items:
                self.append(item)

    def _wrap(self, value):
        if (self.value_class is not None) and (not isinstance(value, self.value_class)):
            raise TypeError('value must be a "{0}": {1}'
                            .format(cls_name(self.value_class), repr(value)))
        if self.wrapper_function is not None:
            value = self.wrapper_function(value)
        return value

    def _unwrap(self, value):
        if self.unwrapper_function is not None:
            value = self.unwrapper_function(value)
        return value

    def __getitem__(self, index):
        value = super(StrictList, self).__getitem__(index)
        value = self._unwrap(value)
        return value

    def __setitem__(self, index, value):
        value = self._wrap(value)
        return super(StrictList, self).__setitem__(index, value)

    def __iadd__(self, values):
        values = [self._wrap(v) for v in values]
        return super(StrictList, self).__iadd__(values)

    def append(self, value):
        value = self._wrap(value)
        return super(StrictList, self).append(value)

    def extend(self, values):
        values = [self._wrap(v) for v in values]
        return super(StrictList, self).extend(values)

    def insert(self, index, value):
        value = self._wrap(value)
        return super(StrictList, self).insert(index, value)


class StrictDict(OrderedDict):
    """
    An ordered dict that raises :class:`~exceptions.TypeError` exceptions when keys or values of the
    wrong type are used.
    """

    def __init__(self,
                 items=None,
                 key_class=None,
                 value_class=None,
                 wrapper_function=None,
                 unwrapper_function=None):
        super(StrictDict, self).__init__()
        if isinstance(items, StrictDict):
            self.key_class = items.key_class
            self.value_class = items.value_class
            self.wrapper_function = items.wrapper_function
            self.unwrapper_function = items.unwrapper_function
        self.key_class = key_class
        self.value_class = value_class
        self.wrapper_function = wrapper_function
        self.unwrapper_function = unwrapper_function
        if items:
            for k, v in items:
                self[k] = v

    def __getitem__(self, key):
        if (self.key_class is not None) and (not isinstance(key, self.key_class)):
            raise TypeError('key must be a "{0}": {1}'
                            .format(cls_name(self.key_class), repr(key)))
        value = super(StrictDict, self).__getitem__(key)
        if self.unwrapper_function is not None:
            value = self.unwrapper_function(value)
        return value

    def __setitem__(self, key, value, **_):
        if (self.key_class is not None) and (not isinstance(key, self.key_class)):
            raise TypeError('key must be a "{0}": {1}'
                            .format(cls_name(self.key_class), repr(key)))
        if (self.value_class is not None) and (not isinstance(value, self.value_class)):
            raise TypeError('value must be a "{0}": {1}'
                            .format(cls_name(self.value_class), repr(value)))
        if self.wrapper_function is not None:
            value = self.wrapper_function(value)
        return super(StrictDict, self).__setitem__(key, value)


def merge(dict_a, dict_b, copy=True, strict=False, path=None):
    """
    Merges dicts, recursively.

    :param dict_a: target dict (will be modified)
    :param dict_b: source dict (will not be modified)
    :param copy: if True, will use :func:`deepcopy_fast` on each merged element
    :param strict: if True, will raise a ValueError if there are key conflicts, otherwise will
     override exiting values
    :param path: for internal use in strict mode
    :return: dict_a, after the merge
    """

    # TODO: a.add_yaml_merge(b),
    # see https://bitbucket.org/ruamel/yaml/src/86622a1408e0f171a12e140d53c4ffac4b6caaa3/
    #     comments.py?fileviewer=file-view-default

    path = path or []
    for key, value_b in dict_b.iteritems():
        if key in dict_a:
            value_a = dict_a[key]
            if isinstance(value_a, dict) and isinstance(value_b, dict):
                if strict:
                    path = path + [str(key)]
                merge(value_a, value_b, copy, strict, path)
            elif value_a != value_b:
                if strict:
                    raise ValueError('dict merge conflict at {0}'
                                     .format('.'.join(path + [str(key)])))
                else:
                    dict_a[key] = deepcopy_fast(value_b) if copy else value_b
        else:
            dict_a[key] = deepcopy_fast(value_b) if copy else value_b
    return dict_a


def is_removable(_container, _key, v):
    return (v is None) or ((isinstance(v, dict) or isinstance(v, list)) and (len(v) == 0))


def prune(value, is_removable_function=is_removable):
    """
    Deletes ``None`` and empty lists and dicts, recursively.
    """

    if isinstance(value, list):
        for i, v in enumerate(value):
            if is_removable_function(value, i, v):
                del value[i]
            else:
                prune(v, is_removable_function)
    elif isinstance(value, dict):
        for k, v in value.items():
            if is_removable_function(value, k, v):
                del value[k]
            else:
                prune(v, is_removable_function)

    return value


def deepcopy_fast(obj):
    """
    The builtin ``deepcopy`` is very slow due to detection of loops and other errors.

    This version is surprisingly much faster.
    """
    return pickle.loads(pickle.dumps(obj))


# TODO: Move following two methods to some place parser specific

def deepcopy_with_locators(value):
    """
    Like :func:`~copy.deepcopy`, but also copies over locators.
    """

    res = deepcopy_fast(value)
    copy_locators(res, value)
    return res


def copy_locators(target, source):
    """
    Copies over ``_locator`` for all elements, recursively.

    Assumes that target and source have exactly the same list/dict structure.
    """

    locator = getattr(source, '_locator', None)
    if locator is not None:
        try:
            setattr(target, '_locator', locator)
        except AttributeError:
            pass

    if isinstance(target, list) and isinstance(source, list):
        for i, _ in enumerate(target):
            copy_locators(target[i], source[i])
    elif isinstance(target, dict) and isinstance(source, dict):
        for k, v in target.iteritems():
            copy_locators(v, source[k])
