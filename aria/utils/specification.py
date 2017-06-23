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

"""
Utilities for cross-referencing code with specification documents.
"""

from .collections import OrderedDict


DSL_SPECIFICATIONS = {}


def implements_specification(section, spec):
    """
    Decorator for specification implementations.

    Used for documentation and standards compliance.
    """

    from .type import full_type_name

    def decorator(obj):
        specification = DSL_SPECIFICATIONS.get(spec)

        if specification is None:
            specification = {}
            DSL_SPECIFICATIONS[spec] = specification

        if section in specification:
            raise Exception('you cannot specify the same @implements_specification twice, consider'
                            ' adding \'-1\', \'-2\', etc.: {0}, {1}'.format(spec, section))

        specification[section] = OrderedDict((
            ('code', full_type_name(obj)),
            ('doc', obj.__doc__)))

        try:
            setattr(obj, '_dsl_specifications', {section: section, spec: spec})
        except BaseException:
            pass

        return obj

    return decorator
