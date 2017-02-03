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
import tempfile

from requests import Session
from requests.exceptions import (ConnectionError, InvalidSchema)
from cachecontrol import CacheControl
from cachecontrol.caches import FileCache

from .exceptions import LoaderException, DocumentNotFoundException
from .loader import Loader

SESSION = None
SESSION_CACHE_PATH = os.path.join(tempfile.gettempdir(), 'aria_requests')


class RequestLoader(Loader):
    """
    Base class for ARIA request-based loaders.

    Extracts a document from a URI by performing a request.

    Note that the "file:" schema is not supported: :class:`FileTextLoader` should
    be used instead.
    """

    def __init__(self, context, uri, headers=None):
        if headers is None:
            headers = {}
        self.context = context
        self.uri = uri
        self.headers = headers
        self._response = None

    def load(self):
        pass

    def open(self):
        global SESSION
        if SESSION is None:
            SESSION = CacheControl(Session(), cache=FileCache(SESSION_CACHE_PATH))

        try:
            self._response = SESSION.get(self.uri, headers=self.headers)
        except InvalidSchema as e:
            raise DocumentNotFoundException('document not found: "%s"' % self.uri, cause=e)
        except ConnectionError as e:
            raise LoaderException('request connection error: "%s"' % self.uri, cause=e)
        except Exception as e:
            raise LoaderException('request error: "%s"' % self.uri, cause=e)

        status = self._response.status_code
        if status == 404:
            self._response = None
            raise DocumentNotFoundException('document not found: "%s"' % self.uri)
        elif status != 200:
            self._response = None
            raise LoaderException('request error %d: "%s"' % (status, self.uri))


class RequestTextLoader(RequestLoader):
    """
    ARIA request-based text loader.
    """

    def load(self):
        if self._response is not None:
            try:
                if self._response.encoding is None:
                    self._response.encoding = 'utf8'
                return self._response.text
            except Exception as e:
                raise LoaderException('request error: %s' % self.uri, cause=e)
        return None
