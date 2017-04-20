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

from types import FunctionType

from ...utils.formatting import safe_repr
from ...utils.type import full_type_name
from ..validation import Issue
from .null import NULL


def get_locator(*values):
    """
    Gets the first available locator.

    :rtype: :class:`aria.reading.Locator`
    """

    for v in values:
        if hasattr(v, '_locator'):
            locator = v._locator
            if locator is not None:
                return locator
    return None


def parse_types_dict_names(types_dict_names):
    """
    If the first element in the array is a function, extracts it out.
    """

    convert = None
    if isinstance(types_dict_names[0], FunctionType):
        convert = types_dict_names[0]
        types_dict_names = types_dict_names[1:]
    return types_dict_names, convert


def validate_primitive(value, cls, coerce=False):
    """
    Checks if the value is of the primitive type, optionally attempting to coerce it
    if it is not.

    Raises a :code:`ValueError` if it isn't or if coercion failed.
    """

    if (cls is not None) and (value is not None) and (value is not NULL):
        if (cls is unicode) or (cls is str): # These two types are interchangeable
            valid = isinstance(value, basestring)
        elif cls is int:
            # In Python, a bool is an int
            valid = isinstance(value, int) and not isinstance(value, bool)
        else:
            valid = isinstance(value, cls)
        if not valid:
            if coerce:
                value = cls(value)
            else:
                raise ValueError('not a "%s": %s' % (full_type_name(cls), safe_repr(value)))
    return value


def validate_no_short_form(context, presentation):
    """
    Makes sure that we can use short form definitions only if we allowed it.
    """

    if not hasattr(presentation, 'SHORT_FORM_FIELD') and not isinstance(presentation._raw, dict):
        context.validation.report('short form not allowed for field "%s"' % presentation._fullname,
                                  locator=presentation._locator,
                                  level=Issue.BETWEEN_FIELDS)


def validate_no_unknown_fields(context, presentation):
    """
    Make sure that we can use unknown fields only if we allowed it.
    """

    if not getattr(presentation, 'ALLOW_UNKNOWN_FIELDS', False) \
            and not context.validation.allow_unknown_fields \
            and isinstance(presentation._raw, dict) \
            and hasattr(presentation, 'FIELDS'):
        for k in presentation._raw:
            if k not in presentation.FIELDS:
                context.validation.report('field "%s" is not supported in "%s"'
                                          % (k, presentation._fullname),
                                          locator=presentation._get_child_locator(k),
                                          level=Issue.BETWEEN_FIELDS)


def validate_known_fields(context, presentation):
    """
    Validates all known fields.
    """

    if hasattr(presentation, '_iter_fields'):
        for _, field in presentation._iter_fields():
            field.validate(presentation, context)


def get_parent_presentation(context, presentation, *types_dict_names):
    """
    Returns the parent presentation according to the :code:`derived_from` field, or None if invalid.

    Checks that we do not derive from ourselves and that we do not cause a circular hierarchy.

    The arguments from the third onwards are used to locate a nested field under
    :code:`service_template` under the root presenter. The first of these can optionally
    be a function, in which case it will be called to convert type names. This can be used
    to support shorthand type names, aliases, etc.
    """

    type_name = presentation.derived_from

    if type_name is None:
        return None

    types_dict_names, convert = parse_types_dict_names(types_dict_names)
    types_dict = context.presentation.get('service_template', *types_dict_names) or {}

    if convert:
        type_name = convert(context, type_name, types_dict)

    # Make sure not derived from self
    if type_name == presentation._name:
        return None
    # Make sure derived from type exists
    elif type_name not in types_dict:
        return None
    else:
        # Make sure derivation hierarchy is not circular
        hierarchy = [presentation._name]
        presentation_copy = presentation
        while presentation_copy.derived_from is not None:
            derived_from = presentation_copy.derived_from
            if convert:
                derived_from = convert(context, derived_from, types_dict)

            if derived_from == presentation_copy._name or derived_from not in types_dict:
                return None
            presentation_copy = types_dict[derived_from]
            if presentation_copy._name in hierarchy:
                return None
            hierarchy.append(presentation_copy._name)

    return types_dict[type_name]


def report_issue_for_unknown_type(context, presentation, type_name, field_name, value=None):
    if value is None:
        value = getattr(presentation, field_name)
    context.validation.report('"%s" refers to an unknown %s in "%s": %s'
                              % (field_name, type_name, presentation._fullname, safe_repr(value)),
                              locator=presentation._get_child_locator(field_name),
                              level=Issue.BETWEEN_TYPES)


def report_issue_for_parent_is_self(context, presentation, field_name):
    context.validation.report('parent type of "%s" is self' % presentation._fullname,
                              locator=presentation._get_child_locator(field_name),
                              level=Issue.BETWEEN_TYPES)


def report_issue_for_unknown_parent_type(context, presentation, field_name):
    context.validation.report('unknown parent type "%s" in "%s"'
                              % (getattr(presentation, field_name), presentation._fullname),
                              locator=presentation._get_child_locator(field_name),
                              level=Issue.BETWEEN_TYPES)


def report_issue_for_circular_type_hierarchy(context, presentation, field_name):
    context.validation.report('"%s" of "%s" creates a circular type hierarchy'
                              % (getattr(presentation, field_name), presentation._fullname),
                              locator=presentation._get_child_locator(field_name),
                              level=Issue.BETWEEN_TYPES)
