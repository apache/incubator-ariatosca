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

import os
from urlparse import urljoin

from ...extension import parser
from ...utils.collections import StrictList
from ...utils.uris import as_file
from .loader import Loader
from .file import FileTextLoader
from .request import RequestTextLoader
from .exceptions import DocumentNotFoundException


class UriTextLoader(Loader):
    """
    Base class for ARIA URI loaders.

    See :class:`~aria.parser.loading.UriLocation`.

    Supports a list of search prefixes that are tried in order if the URI cannot be found.
    They will be:

    * If ``origin_location`` is provided its prefix will come first.
    * Then the prefixes in the :class:`LoadingContext` will be added.
    * Finally, the parser can supply a ``uri_loader_prefix`` function with extra prefixes.
    """

    def __init__(self, context, location, origin_location=None):
        self.context = context
        self.location = location
        self._prefixes = StrictList(value_class=basestring)
        self._loader = None

        def add_prefix(prefix):
            if prefix and (prefix not in self._prefixes):
                self._prefixes.append(prefix)

        def add_prefixes(prefixes):
            for prefix in prefixes:
                add_prefix(prefix)

        if origin_location is not None:
            add_prefix(origin_location.prefix)

        add_prefixes(context.prefixes)
        add_prefixes(parser.uri_loader_prefix())

    def open(self):
        try:
            self._open(self.location.uri)
            return
        except DocumentNotFoundException:
            # Try prefixes in order
            for prefix in self._prefixes:
                prefix_as_file = as_file(prefix)
                if prefix_as_file is not None:
                    uri = os.path.join(prefix_as_file, self.location.uri)
                else:
                    uri = urljoin(prefix, self.location.uri)
                try:
                    self._open(uri)
                    return
                except DocumentNotFoundException:
                    pass
        raise DocumentNotFoundException('document not found at URI: "%s"' % self.location)

    def close(self):
        if self._loader is not None:
            self._loader.close()

    def load(self):
        return self._loader.load() if self._loader is not None else None

    def _open(self, uri):
        the_file = as_file(uri)
        if the_file is not None:
            uri = the_file
            loader = FileTextLoader(self.context, uri)
        else:
            loader = RequestTextLoader(self.context, uri)
        loader.open() # might raise an exception
        self._loader = loader
        self.location.uri = uri
