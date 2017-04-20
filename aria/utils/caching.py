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

from __future__ import absolute_import  # so we can import standard 'collections' and 'threading'

from threading import Lock
from functools import partial

from .collections import OrderedDict


class cachedmethod(object):  # pylint: disable=invalid-name
    """
    Decorator for caching method return values.

    The implementation is thread-safe.

    Supports :code:`cache_info` to be compatible with Python 3's :code:`functools.lru_cache`.
    Note that the statistics are combined for all instances of the class.

    Won't use the cache if not called when bound to an object, allowing you to override the cache.

    Adapted from `this solution
    <http://code.activestate.com/recipes/577452-a-memoize-decorator-for-instance-methods/>`__.
    """

    ENABLED = True

    def __init__(self, func):
        self.func = func
        self.hits = 0
        self.misses = 0
        self.lock = Lock()

    def cache_info(self):
        with self.lock:
            return (self.hits, self.misses, None, self.misses)

    def reset_cache_info(self):
        with self.lock:
            self.hits = 0
            self.misses = 0

    def __get__(self, instance, owner):
        if instance is None:
            # Don't use cache if not bound to an object
            # Note: This is also a way for callers to override the cache
            return self.func
        return partial(self, instance)

    def __call__(self, *args, **kwargs):
        if not self.ENABLED:
            return self.func(*args, **kwargs)

        instance = args[0]
        if not hasattr(instance, '_method_cache'):
            instance._method_cache = {}
        method_cache = instance._method_cache

        key = (self.func, args[1:], frozenset(kwargs.items()))

        try:
            with self.lock:
                return_value = method_cache[key]
                self.hits += 1
        except KeyError:
            return_value = self.func(*args, **kwargs)
            with self.lock:
                method_cache[key] = return_value
                self.misses += 1
            # Another thread may override our cache entry here, so we need to read
            # it again to make sure all threads use the same return value
            return_value = method_cache.get(key, return_value)

        return return_value


class HasCachedMethods(object):
    """
    Provides convenience methods for working with :class:`cachedmethod`.
    """

    def __init__(self, method_cache=None):
        self._method_cache = method_cache or {}

    @property
    def _method_cache_info(self):
        """
        The cache infos of all cached methods.

        :rtype: dict of str, 4-tuple
        """

        cached_info = OrderedDict()
        for k, v in self.__class__.__dict__.iteritems():
            if isinstance(v, property):
                # The property getter might be cached
                v = v.fget
            if hasattr(v, 'cache_info'):
                cached_info[k] = v.cache_info()
        return cached_info

    def _reset_method_cache(self):
        """
        Resets the caches of all cached methods.
        """

        if hasattr(self, '_method_cache'):
            self._method_cache = {}

        # Note: Another thread may already be storing entries in the cache here.
        # But it's not a big deal! It only means that our cache_info isn't
        # guaranteed to be accurate.

        for entry in self.__class__.__dict__.itervalues():
            if isinstance(entry, property):
                # The property getter might be cached
                entry = entry.fget
            if hasattr(entry, 'reset_cache_info'):
                entry.reset_cache_info()
