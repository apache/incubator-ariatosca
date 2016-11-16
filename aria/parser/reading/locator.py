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

from ...utils.console import puts, Colored, indent

# We are inheriting the primitive types in order to add the ability to set
# an attribute (_locator) on them.


class LocatableString(unicode):
    pass


class LocatableInt(int):
    pass


class LocatableFloat(float):
    pass


def wrap(value):
    if isinstance(value, basestring):
        return True, LocatableString(value)
    elif isinstance(value, int) and \
            not isinstance(value, bool):  # Note: bool counts as int in Python!
        return True, LocatableInt(value)
    elif isinstance(value, float):
        return True, LocatableFloat(value)
    return False, value


class Locator(object):
    """
    Stores location information (line and column numbers) for agnostic raw data.
    """
    def __init__(self, location, line, column, children=None):
        self.location = location
        self.line = line
        self.column = column
        self.children = children

    def get_child(self, *names):
        if (not names) or (not isinstance(self.children, dict)):
            return self
        name = names[0]
        if name not in self.children:
            return self
        child = self.children[name]
        return child.get_child(names[1:])

    def link(self, raw, path=None):
        if hasattr(raw, '_locator'):
            # This can happen when we use anchors
            return

        try:
            setattr(raw, '_locator', self)
        except AttributeError:
            return

        if isinstance(raw, list):
            for i, raw_element in enumerate(raw):
                wrapped, raw_element = wrap(raw_element)
                if wrapped:
                    raw[i] = raw_element
                child_path = '%s.%d' % (path, i) if path else str(i)
                try:
                    self.children[i].link(raw_element, child_path)
                except KeyError:
                    raise ValueError('location map does not match agnostic raw data: %s' %
                                     child_path)
        elif isinstance(raw, dict):
            for k, raw_element in raw.iteritems():
                wrapped, raw_element = wrap(raw_element)
                if wrapped:
                    raw[k] = raw_element
                child_path = '%s.%s' % (path, k) if path else k
                try:
                    self.children[k].link(raw_element, child_path)
                except KeyError:
                    raise ValueError('location map does not match agnostic raw data: %s' %
                                     child_path)

    def merge(self, locator):
        if isinstance(self.children, dict) and isinstance(locator.children, dict):
            for k, loc in locator.children.iteritems():
                if k in self.children:
                    self.children[k].merge(loc)
                else:
                    self.children[k] = loc

    def dump(self, key=None):
        if key:
            puts('%s "%s":%d:%d' %
                 (Colored.red(key), Colored.blue(self.location), self.line, self.column))
        else:
            puts('"%s":%d:%d' % (Colored.blue(self.location), self.line, self.column))
        if isinstance(self.children, list):
            with indent(2):
                for loc in self.children:
                    loc.dump()
        elif isinstance(self.children, dict):
            with indent(2):
                for k, loc in self.children.iteritems():
                    loc.dump(k)

    def __str__(self):
        # Should be in same format as Issue.locator_as_str
        return '"%s":%d:%d' % (self.location, self.line, self.column)
