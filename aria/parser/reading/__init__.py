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

"""
Reading package.

.. autosummary::
   :nosignatures:

   aria.parser.reading.ReadingContext
   ReaderException
   ReaderNotFoundError
   ReaderSyntaxError
   JinjaReader
   JsonReader
   Locator
   RawReader
   Reader
   ReaderSource
   DefaultReaderSource
   YamlReader
"""

from .raw import RawReader
from .reader import Reader
from .yaml import YamlReader
from .locator import Locator
from .json import JsonReader
from .jinja import JinjaReader
from .context import ReadingContext
from .source import ReaderSource, DefaultReaderSource
from .exceptions import (ReaderException,
                         ReaderNotFoundError,
                         ReaderSyntaxError)

__all__ = (
    'ReaderException',
    'ReaderNotFoundError',
    'ReaderSyntaxError',
    'Reader',
    'ReaderSource',
    'DefaultReaderSource',
    'ReadingContext',
    'RawReader',
    'Locator',
    'YamlReader',
    'JsonReader',
    'JinjaReader')
