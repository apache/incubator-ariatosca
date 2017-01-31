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

import csv
import re

from ..extension import parser
from ..utils.console import (puts, Colored, indent)
from ..utils.collections import OrderedDict
from ..utils.formatting import full_type_name

_DSL_SPECIFICATIONS = {}


def dsl_specification(section, spec):
    """
    Decorator for TOSCA specification.

    Used for documentation and standards compliance.
    """
    def decorator(obj):
        specification = _DSL_SPECIFICATIONS.get(spec)

        if specification is None:
            specification = {}
            _DSL_SPECIFICATIONS[spec] = specification

        if section in specification:
            raise Exception('you cannot specify the same @dsl_specification twice, consider'
                            ' adding \'-1\', \'-2\', etc.: %s, %s' % (spec, section))

        specification[section] = OrderedDict((
            ('code', full_type_name(obj)),
            ('doc', obj.__doc__)))

        try:
            setattr(obj, '_dsl_specifications', {section: section, spec: spec})
        except BaseException:
            pass

        return obj

    return decorator


def iter_specifications():
    """
    Iterates all specification assignments in the codebase.
    """
    def iter_sections(spec, sections):
        for k in sorted(sections.keys(), key=_section_key):
            details = OrderedDict()
            details['code'] = sections[k]['code']
            yield k, _fix_details(sections[k], spec)

    for spec, sections in _DSL_SPECIFICATIONS.iteritems():
        yield spec, iter_sections(spec, sections)


def dump(stream):
    """
    Dumps specification to given stream
    """
    for spec, sections in iter_specifications():
        puts(Colored.cyan(spec), stream=stream)
        with indent(2):
            for section, details in sections:
                puts(Colored.blue(section), stream=stream)
                with indent(2):
                    for k, v in details.iteritems():
                        puts('%s: %s' % (Colored.magenta(k), v), stream=stream)


def dump_as_csv(stream):
    """
    Dumps serialized as CSV specification to given stream
    """
    writer = csv.writer(stream, quoting=csv.QUOTE_ALL)
    writer.writerow(('Specification', 'Section', 'Code', 'URL'))

    for spec, sections in iter_specifications():
        for section, details in sections:
            writer.writerow((spec, section, details['code'], details['url']))
# Utils


def _section_key(value):
    try:
        parts = value.split('-', 1)
        first = (int(v) for v in parts[0].split('.'))
        second = parts[1] if len(parts) > 1 else None
        return first, second
    except ValueError:
        return value


def _fix_details(details, spec):
    code = details.get('code')
    doc = details.get('doc')
    url = parser.specification_url().get(spec)

    if (url is not None) and (doc is not None):
        # Look for a URL in ReST docstring that begins with our url
        pattern = r'<?('
        for char in url:
            pattern += r'\s*'
            pattern += re.escape(char)
        pattern += r'[^>]+)>'
        match = re.search(pattern, doc)
        if match:
            url = re.sub(r'\s+', '', match.group(1))

    return OrderedDict((
        ('code', code),
        ('url', url)))
