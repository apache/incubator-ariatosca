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

import codecs

from .loader import Loader
from .exceptions import LoaderException, DocumentNotFoundException


class FileTextLoader(Loader):
    """
    ARIA file text loader.

    Extracts a text document from a file. The default encoding is UTF-8, but other supported
    encoding can be specified instead.
    """

    def __init__(self, context, path, encoding='utf-8'):
        self.context = context
        self.path = path
        self.encoding = encoding
        self._file = None

    def open(self):
        try:
            self._file = codecs.open(self.path, mode='r', encoding=self.encoding, buffering=1)
        except IOError as e:
            if e.errno == 2:
                raise DocumentNotFoundException('file not found: "%s"' % self.path, cause=e)
            else:
                raise LoaderException('file I/O error: "%s"' % self.path, cause=e)
        except Exception as e:
            raise LoaderException('file error: "%s"' % self.path, cause=e)

    def close(self):
        if self._file is not None:
            try:
                self._file.close()
            except IOError as e:
                raise LoaderException('file I/O error: "%s"' % self.path, cause=e)
            except Exception as e:
                raise LoaderException('file error: "%s"' % self.path, cause=e)

    def load(self):
        if self._file is not None:
            try:
                return self._file.read()
            except IOError as e:
                raise LoaderException('file I/O error: "%s"' % self.path, cause=e)
            except Exception as e:
                raise LoaderException('file error %s' % self.path, cause=e)
        return None
