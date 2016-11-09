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

from .source import DefaultReaderSource
from ..utils import LockedList


class ReadingContext(object):
    """
    Properties:

    * :code:`reader_source`: For finding reader instances
    * :code:`reader`: Overrides :code:`reader_source` with a specific class
    """

    def __init__(self):
        self.reader_source = DefaultReaderSource()
        self.reader = None

        self._locations = LockedList() # for keeping track of locations already read
