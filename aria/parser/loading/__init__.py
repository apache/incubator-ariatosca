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
Loading package.

.. autosummary::
   :nosignatures:

   aria.parser.loading.LoadingContext
   aria.parser.loading.LoaderException
   aria.parser.loading.LoaderNotFoundError
   aria.parser.loading.DocumentNotFoundException
   aria.parser.loading.LoaderSource
   aria.parser.loading.DefaultLoaderSource

Loaders
-------

.. autosummary::
   :nosignatures:

   aria.parser.loading.Loader
   aria.parser.loading.FileTextLoader
   aria.parser.loading.LiteralLoader
   aria.parser.loading.RequestLoader
   aria.parser.loading.RequestTextLoader
   aria.parser.loading.UriTextLoader

Locations
---------

.. autosummary::
   :nosignatures:

   aria.parser.loading.Location
   aria.parser.loading.UriLocation
"""

from .exceptions import LoaderException, LoaderNotFoundError, DocumentNotFoundException
from .context import LoadingContext
from .loader import Loader
from .source import LoaderSource, DefaultLoaderSource
from .location import Location, UriLocation, LiteralLocation
from .literal import LiteralLoader
from .uri import UriTextLoader
from .request import SESSION, SESSION_CACHE_PATH, RequestLoader, RequestTextLoader
from .file import FileTextLoader


__all__ = (
    'LoaderException',
    'LoaderNotFoundError',
    'DocumentNotFoundException',
    'LoadingContext',
    'Loader',
    'LoaderSource',
    'DefaultLoaderSource',
    'Location',
    'UriLocation',
    'LiteralLocation',
    'LiteralLoader',
    'UriTextLoader',
    'SESSION',
    'SESSION_CACHE_PATH',
    'RequestLoader',
    'RequestTextLoader',
    'FileTextLoader')
