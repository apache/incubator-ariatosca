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


class ReadingContext(object):
    """
    Reading context.

    :ivar reader_source: for finding reader instances
    :vartype reader_source: ReaderSource
    :ivar reader: overrides ``reader_source`` with a specific class
    :vartype reader: type
    """

    def __init__(self):
        self.reader_source = DefaultReaderSource()
        self.reader = None
