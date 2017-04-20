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

import json
from types import MethodType

from ruamel import yaml  # @UnresolvedImport

from .collections import FrozenList, FrozenDict, StrictList, StrictDict, OrderedDict


PLURALIZE_EXCEPTIONS = {}


# Add our types to ruamel.yaml (for round trips)
yaml.representer.RoundTripRepresenter.add_representer(
    FrozenList, yaml.representer.RoundTripRepresenter.represent_list)
yaml.representer.RoundTripRepresenter.add_representer(
    FrozenDict, yaml.representer.RoundTripRepresenter.represent_dict)
yaml.representer.RoundTripRepresenter.add_representer(
    StrictList, yaml.representer.RoundTripRepresenter.represent_list)
yaml.representer.RoundTripRepresenter.add_representer(
    StrictDict, yaml.representer.RoundTripRepresenter.represent_dict)

# Without this, ruamel.yaml will output "!!omap" types, which is
# technically correct but unnecessarily verbose for our uses
yaml.representer.RoundTripRepresenter.add_representer(
    OrderedDict, yaml.representer.RoundTripRepresenter.represent_dict)


class JsonAsRawEncoder(json.JSONEncoder):
    """
    A :class:`JSONEncoder` that will use the :code:`as_raw` property of objects
    if available.
    """
    def raw_encoder_default(self, obj):
        try:
            return iter(obj)
        except TypeError:
            if hasattr(obj, 'as_raw'):
                return as_raw(obj)
            return str(obj)
        return super(JsonAsRawEncoder, self).default(obj)

    def __init__(self, *args, **kwargs):
        kwargs['default'] = self.raw_encoder_default
        super(JsonAsRawEncoder, self).__init__(*args, **kwargs)


class YamlAsRawDumper(yaml.dumper.RoundTripDumper):  # pylint: disable=too-many-ancestors
    """
    A :class:`RoundTripDumper` that will use the :code:`as_raw` property of objects
    if available.
    """

    def represent_data(self, data):
        if hasattr(data, 'as_raw'):
            data = as_raw(data)
        return super(YamlAsRawDumper, self).represent_data(data)


def decode_list(data):
    decoded_list = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = decode_list(item)
        elif isinstance(item, dict):
            item = decode_dict(item)
        decoded_list.append(item)
    return decoded_list


def decode_dict(data):
    decoded_dict = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        elif isinstance(value, list):
            value = decode_list(value)
        elif isinstance(value, dict):
            value = decode_dict(value)
        decoded_dict[key] = value
    return decoded_dict


def safe_str(value):
    """
    Like :code:`str` coercion, but makes sure that Unicode strings are properly
    encoded, and will never return None.
    """

    try:
        return str(value)
    except UnicodeEncodeError:
        return unicode(value).encode('utf8')


def safe_repr(value):
    """
    Like :code:`repr`, but calls :code:`as_raw` and :code:`as_agnostic` first.
    """

    return repr(as_agnostic(as_raw(value)))


def string_list_as_string(strings):
    """
    Nice representation of a list of strings.
    """

    return ', '.join('"%s"' % safe_str(v) for v in strings)


def pluralize(noun):
    plural = PLURALIZE_EXCEPTIONS.get(noun)
    if plural is not None:
        return plural
    elif noun.endswith('s'):
        return '{0}es'.format(noun)
    elif noun.endswith('y'):
        return '{0}ies'.format(noun[:-1])
    else:
        return '{0}s'.format(noun)


def as_raw(value):
    """
    Converts values using their :code:`as_raw` property, if it exists, recursively.
    """

    if hasattr(value, 'as_raw'):
        value = value.as_raw
        if isinstance(value, MethodType):
            # Old-style Python classes don't support properties
            value = value()
    elif isinstance(value, list):
        value = list(value)
        for i, v in enumerate(value):
            value[i] = as_raw(v)
    elif isinstance(value, dict):
        value = dict(value)
        for k, v in value.iteritems():
            value[k] = as_raw(v)
    return value


def as_raw_list(value):
    """
    Assuming value is a list, converts its values using :code:`as_raw`.
    """

    if value is None:
        return []
    if isinstance(value, dict):
        value = value.itervalues()
    return [as_raw(v) for v in value]


def as_raw_dict(value):
    """
    Assuming value is a dict, converts its values using :code:`as_raw`.
    The keys are left as is.
    """

    if value is None:
        return OrderedDict()
    return OrderedDict((
        (k, as_raw(v)) for k, v in value.iteritems()))


def as_agnostic(value):
    """
    Converts subclasses of list and dict to standard lists and dicts, and Unicode strings
    to non-Unicode if possible, recursively.

    Useful for creating human-readable output of structures.
    """

    if isinstance(value, unicode):
        try:
            value = str(value)
        except UnicodeEncodeError:
            pass
    elif isinstance(value, list):
        value = list(value)
    elif isinstance(value, dict):
        value = dict(value)

    if isinstance(value, list):
        for i, _ in enumerate(value):
            value[i] = as_agnostic(value[i])
    elif isinstance(value, dict):
        for k, v in value.iteritems():
            value[k] = as_agnostic(v)

    return value


def json_dumps(value, indent=2):
    """
    JSON dumps that supports Unicode and the :code:`as_raw` property of objects
    if available.
    """

    return json.dumps(value, indent=indent, ensure_ascii=False, cls=JsonAsRawEncoder)


def yaml_dumps(value, indent=2):
    """
    YAML dumps that supports Unicode and the :code:`as_raw` property of objects
    if available.
    """

    return yaml.dump(value, indent=indent, allow_unicode=True, Dumper=YamlAsRawDumper)


def yaml_loads(value):
    return yaml.load(value, Loader=yaml.SafeLoader)
