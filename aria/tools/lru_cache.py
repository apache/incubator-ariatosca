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
Function lru_cache implementation for python 2.7
(In Python 3 this decorator is in functools)
"""

from time import time
from functools import partial, wraps
from itertools import imap
from collections import OrderedDict


class _LRUCache(object):

    def __init__(self, input_func, max_size, timeout):
        self._input_func = input_func
        self._max_size = max_size
        self._timeout = timeout

        # This will store the cache for this function, format:
        # {caller1 : [OrderedDict1, last_refresh_time1],
        #  caller2 : [OrderedDict2, last_refresh_time2]}.
        # In case of an instance method -
        # the caller is the instance,
        # in case called from a regular function - the caller is None.
        self._caches_dict = {}

    @staticmethod
    def _prepare_key(*args, **kwargs):
        kwargs_key = "".join(
            imap(lambda x: str(x) + str(type(kwargs[x])) + str(kwargs[x]),
                 sorted(kwargs)))
        return "".join(imap(lambda x: str(type(x)) + str(x), args)) + kwargs_key

    def cache_clear(self, caller=None):
        """
        Clears the cache, optionally, only for a specific caller
        """
        # Remove the cache for the caller, only if exists:
        if caller in self._caches_dict:
            del self._caches_dict[caller]
            self._caches_dict[caller] = (OrderedDict(), time())

    def __get__(self, obj, _):
        """ Called for instance methods """
        return_func = partial(self._cache_wrapper, obj)
        return_func.cache_clear = partial(self.cache_clear, obj)
        # Return the wrapped function and wraps it to maintain the docstring
        # and the name of the original function:
        return wraps(self._input_func)(return_func)

    def __call__(self, *args, **kwargs):
        """ Called for regular functions """
        return self._cache_wrapper(None, *args, **kwargs)
    # Set the cache_clear function in the __call__ operator:
    __call__.cache_clear = cache_clear

    def _cache_wrapper(self, caller, *args, **kwargs):
        # Create a unique key including the types
        # (in order to differentiate between 1 and '1'):
        key = self._prepare_key(*args, **kwargs)

        # Check if caller exists, if not create one:
        if caller not in self._caches_dict:
            self._caches_dict[caller] = (OrderedDict(), time())
        else:
            # Validate in case the refresh time has passed:
            if self._timeout is not None and time() - self._caches_dict[caller][1] > self._timeout:
                self.cache_clear(caller)

        # Check if the key exists, if so - return it:
        cur_caller_cache_dict = self._caches_dict[caller][0]
        if key in cur_caller_cache_dict:
            return cur_caller_cache_dict[key]

        # Validate we didn't exceed the max_size:
        if len(cur_caller_cache_dict) >= self._max_size:
            # Delete the first item in the dict:
            cur_caller_cache_dict.popitem(False)

        # Call the function and store the data in the cache
        # (call it with the caller in case it's an instance function - Ternary condition):
        cur_caller_cache_dict[key] = self._input_func(caller, *args, **kwargs) \
            if caller is not None else self._input_func(*args, **kwargs)
        return cur_caller_cache_dict[key]


def lru_cache(maxsize=255, timeout=None):
    """
    lru_cache(maxsize = 255, timeout = None)
    Returns a decorator which returns an instance (a descriptor).

    Purpose:
        This decorator factory will wrap a function / instance method,
        and will supply a caching mechanism to the function.
        For every given input params it will store the result in a queue of maxsize size,
        and will return a cached ret_val if the same parameters are passed.

    Notes:
        * If an instance method is wrapped,
          each instance will have it's own cache and it's own timeout.
        * The wrapped function will have a cache_clear variable inserted into it,
          and may be called to clear it's specific cache.
        * The wrapped function will maintain the original function's docstring and name (wraps)
        * The type of the wrapped function will no longer be that of a function,
          but either an instance of _LRU_Cache_class or a functool.partial type.

    :param maxsize: The cache size limit,
                    Anything added above that will delete the first values enterred (FIFO).
                    This size is per instance, thus 1000 instances with maxsize of 255,
                    will contain at max 255K elements.
    :type maxsize: int
    :param timeout: Every n seconds the cache is deleted, regardless of usage.
                    If None - cache will never be refreshed.
    :type: timeout: int, float, None

    """
    return lambda input_func: wraps(input_func)(_LRUCache(input_func, maxsize, timeout))
