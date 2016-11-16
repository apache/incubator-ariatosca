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

from ruamel import yaml # @UnresolvedImport

from ...utils.collections import OrderedDict
from .reader import Reader
from .locator import Locator
from .exceptions import ReaderSyntaxError
from .locator import LocatableString, LocatableInt, LocatableFloat

# Add our types to ruamel.yaml
yaml.representer.RoundTripRepresenter.add_representer(
    LocatableString, yaml.representer.RoundTripRepresenter.represent_unicode)
yaml.representer.RoundTripRepresenter.add_representer(
    LocatableInt, yaml.representer.RoundTripRepresenter.represent_int)
yaml.representer.RoundTripRepresenter.add_representer(
    LocatableFloat, yaml.representer.RoundTripRepresenter.represent_float)

MERGE_TAG = u'tag:yaml.org,2002:merge'
MAP_TAG = u'tag:yaml.org,2002:map'


class YamlLocator(Locator):
    """
    Map for agnostic raw data read from YAML.
    """

    def add_children(self, node):
        if isinstance(node, yaml.SequenceNode):
            self.children = []
            for child_node in node.value:
                self.add_child(child_node)
        elif isinstance(node, yaml.MappingNode):
            self.children = {}
            for k, child_node in node.value:
                self.add_child(child_node, k)

    def add_child(self, node, key=None):
        locator = YamlLocator(self.location, node.start_mark.line + 1, node.start_mark.column + 1)
        if key is not None:
            # Dict
            if key.tag == MERGE_TAG:
                for merge_key, merge_node in node.value:
                    self.add_child(merge_node, merge_key)
            else:
                self.children[key.value] = locator
        else:
            # List
            self.children.append(locator)
        locator.add_children(node)


def construct_yaml_map(self, node):
    data = OrderedDict()
    yield data
    value = self.construct_mapping(node)
    data.update(value)


yaml.constructor.SafeConstructor.add_constructor(MAP_TAG, construct_yaml_map)


class YamlReader(Reader):
    """
    ARIA YAML reader.
    """

    def read(self):
        data = self.load()
        try:
            data = unicode(data)
            # see issue here:
            # https://bitbucket.org/ruamel/yaml/issues/61/roundtriploader-causes-exceptions-with
            #yaml_loader = yaml.RoundTripLoader(data)
            yaml_loader = yaml.SafeLoader(data)
            try:
                node = yaml_loader.get_single_node()
                locator = YamlLocator(self.loader.location, 0, 0)
                if node is not None:
                    locator.add_children(node)
                    raw = yaml_loader.construct_document(node)
                else:
                    raw = OrderedDict()
                #locator.dump()
                setattr(raw, '_locator', locator)
                return raw
            finally:
                yaml_loader.dispose()
        except yaml.parser.MarkedYAMLError as e:
            context = e.context or 'while parsing'
            problem = e.problem
            line = e.problem_mark.line
            column = e.problem_mark.column
            snippet = e.problem_mark.get_snippet()
            raise ReaderSyntaxError('YAML %s: %s %s' %
                                    (e.__class__.__name__, problem, context),
                                    location=self.loader.location,
                                    line=line,
                                    column=column,
                                    snippet=snippet,
                                    cause=e)
        except Exception as e:
            raise ReaderSyntaxError('YAML: %s' % e, cause=e)
