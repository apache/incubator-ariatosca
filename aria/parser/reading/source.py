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

from ..loading import LiteralLocation, UriLocation
from .yaml import YamlReader
from .json import JsonReader
from .jinja import JinjaReader
from .exceptions import ReaderNotFoundError


EXTENSIONS = {
    '.yaml': YamlReader,
    '.json': JsonReader,
    '.jinja': JinjaReader}


class ReaderSource(object):
    """
    Base class for ARIA reader sources.

    Reader sources provide appropriate :class:`Reader` instances for locations.
    """

    @staticmethod
    def get_reader(context, location, loader):                                                      # pylint: disable=unused-argument
        raise ReaderNotFoundError(u'location: {0}'.format(location))


class DefaultReaderSource(ReaderSource):
    """
    The default ARIA reader source will generate a :class:`YamlReader` for
    locations that end in ".yaml", a :class:`JsonReader` for locations that
    end in ".json",  and a :class:`JinjaReader` for locations that end in
    ".jinja".
    """

    def __init__(self, literal_reader_class=YamlReader):
        super(DefaultReaderSource, self).__init__()
        self.literal_reader_class = literal_reader_class

    def get_reader(self, context, location, loader):
        if isinstance(location, LiteralLocation):
            return self.literal_reader_class(context, location, loader)

        elif isinstance(location, UriLocation):
            for extension, reader_class in EXTENSIONS.iteritems():
                if location.uri.endswith(extension):
                    return reader_class(context, location, loader)

        return super(DefaultReaderSource, self).get_reader(context, location, loader)
