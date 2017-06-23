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
Presentation package.

.. autosummary::
   :nosignatures:

   aria.parser.presentation.PresentationContext
   aria.parser.presentation.PresenterException
   aria.parser.presentation.PresenterNotFoundError
   aria.parser.presentation.Field
   aria.parser.presentation.NULL
   aria.parser.presentation.none_to_null
   aria.parser.presentation.null_to_none
   aria.parser.presentation.Value
   aria.parser.presentation.Presenter
   aria.parser.presentation.PresenterSource
   aria.parser.presentation.DefaultPresenterSource

Presentations
-------------

.. autosummary::
   :nosignatures:

   aria.parser.presentation.PresentationBase
   aria.parser.presentation.Presentation
   aria.parser.presentation.AsIsPresentation

Field decorators
----------------

.. autosummary::
   :nosignatures:

   aria.parser.presentation.has_fields
   aria.parser.presentation.short_form_field
   aria.parser.presentation.allow_unknown_fields
   aria.parser.presentation.primitive_field
   aria.parser.presentation.primitive_list_field
   aria.parser.presentation.primitive_dict_field
   aria.parser.presentation.primitive_dict_unknown_fields
   aria.parser.presentation.object_field
   aria.parser.presentation.object_list_field
   aria.parser.presentation.object_dict_field
   aria.parser.presentation.object_sequenced_list_field
   aria.parser.presentation.object_dict_unknown_fields
   aria.parser.presentation.field_getter
   aria.parser.presentation.field_setter
   aria.parser.presentation.field_validator

Field validators
----------------

.. autosummary::
   :nosignatures:

   aria.parser.presentation.type_validator
   aria.parser.presentation.list_type_validator
   aria.parser.presentation.list_length_validator
   aria.parser.presentation.derived_from_validator

Utilities
---------

.. autosummary::
   :nosignatures:

   aria.parser.presentation.get_locator
   aria.parser.presentation.parse_types_dict_names
   aria.parser.presentation.validate_primitive
   aria.parser.presentation.validate_no_short_form
   aria.parser.presentation.validate_no_unknown_fields
   aria.parser.presentation.validate_known_fields
   aria.parser.presentation.get_parent_presentation
   aria.parser.presentation.report_issue_for_unknown_type
   aria.parser.presentation.report_issue_for_parent_is_self
   aria.parser.presentation.report_issue_for_unknown_parent_type
   aria.parser.presentation.report_issue_for_circular_type_hierarchy
"""

from .exceptions import PresenterException, PresenterNotFoundError
from .context import PresentationContext
from .presenter import Presenter
from .presentation import Value, PresentationBase, Presentation, AsIsPresentation
from .source import PresenterSource, DefaultPresenterSource
from .null import NULL, none_to_null, null_to_none
from .fields import (Field, has_fields, short_form_field, allow_unknown_fields, primitive_field,
                     primitive_list_field, primitive_dict_field, primitive_dict_unknown_fields,
                     object_field, object_list_field, object_dict_field,
                     object_sequenced_list_field, object_dict_unknown_fields, field_getter,
                     field_setter, field_validator)
from .field_validators import (type_validator, list_type_validator, list_length_validator,
                               derived_from_validator)
from .utils import (get_locator, parse_types_dict_names, validate_primitive, validate_no_short_form,
                    validate_no_unknown_fields, validate_known_fields, get_parent_presentation,
                    report_issue_for_unknown_type, report_issue_for_unknown_parent_type,
                    report_issue_for_parent_is_self, report_issue_for_circular_type_hierarchy)

__all__ = (
    'PresenterException',
    'PresenterNotFoundError',
    'PresentationContext',
    'Presenter',
    'Value',
    'PresentationBase',
    'Presentation',
    'AsIsPresentation',
    'PresenterSource',
    'DefaultPresenterSource',
    'NULL',
    'none_to_null',
    'null_to_none',
    'Field',
    'has_fields',
    'short_form_field',
    'allow_unknown_fields',
    'primitive_field',
    'primitive_list_field',
    'primitive_dict_field',
    'primitive_dict_unknown_fields',
    'object_field',
    'object_list_field',
    'object_dict_field',
    'object_sequenced_list_field',
    'object_dict_unknown_fields',
    'field_getter',
    'field_setter',
    'field_validator',
    'type_validator',
    'list_type_validator',
    'list_length_validator',
    'derived_from_validator',
    'get_locator',
    'parse_types_dict_names',
    'validate_primitive',
    'validate_no_short_form',
    'validate_no_unknown_fields',
    'validate_known_fields',
    'get_parent_presentation',
    'report_issue_for_unknown_type',
    'report_issue_for_unknown_parent_type',
    'report_issue_for_parent_is_self',
    'report_issue_for_circular_type_hierarchy')
