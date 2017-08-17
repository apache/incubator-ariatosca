# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ...utils.openclose import OpenClose
from .exceptions import ReaderException


class Reader(object):
    """
    Base class for ARIA readers.

    Readers provide agnostic raw data by consuming :class:`aria.parser.loading.Loader` instances.
    """

    def __init__(self, context, location, loader):
        self.context = context
        self.location = location
        self.loader = loader

    def load(self):
        with OpenClose(self.loader) as loader:
            data = loader.load()
            if data is None:
                raise ReaderException(u'loader did not provide data: {0}'.format(loader))
            return data

    def read(self):
        raise NotImplementedError
