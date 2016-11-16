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

import os

from jinja2 import Template

from ...VERSION import version
from ..loading import LiteralLocation, LiteralLoader
from .reader import Reader
from .exceptions import ReaderSyntaxError


# TODO: we could put a lot of other useful stuff here.
CONTEXT = {
    'ARIA_VERSION': version,
    'ENV': os.environ}


class JinjaReader(Reader):
    """
    ARIA Jinja reader.

    Forwards the rendered result to a new reader in the reader source.
    """

    def read(self):
        data = self.load()
        try:
            data = str(data)
            template = Template(data)
            literal = template.render(CONTEXT)
            # TODO: might be useful to write the literal result to a file for debugging
            location = self.location
            if isinstance(location, basestring) and location.endswith('.jinja'):
                # Use reader based on the location with the ".jinja" prefix stripped off
                location = location[:-6]
                next_reader = self.context.reading.reader_source.get_reader(
                    self.context, LiteralLocation(literal, name=location), LiteralLoader(literal))
            else:
                # Use reader for literal loader
                next_reader = self.context.reading.reader_source.get_reader(
                    self.context, LiteralLocation(literal), LiteralLoader(literal))
            return next_reader.read()
        except Exception as e:
            raise ReaderSyntaxError('Jinja: %s' % e, cause=e)
