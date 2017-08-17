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


def convert_name_to_full_type_name(context, name, types_dict):                                      # pylint: disable=unused-argument
    """
    Converts a type name to its full type name, or else returns it unchanged.

    Works by checking for ``shorthand_name`` and ``type_qualified_name`` in the types'
    ``_extensions`` field. See also
    :class:`aria_extension_tosca.v1_0.presentation.extensible.ExtensiblePresentation`.

    Can be used as the conversion function argument in ``type_validator`` and
    ``derived_from_validator``.
    """

    if (name is not None) and types_dict and (name not in types_dict):
        for full_name, the_type in types_dict.iteritems():
            if hasattr(the_type, '_extensions') and the_type._extensions \
                and ((the_type._extensions.get('shorthand_name') == name) \
                     or (the_type._extensions.get('type_qualified_name') == name)):
                return full_name
    return name


def get_type_by_name(context, name, *types_dict_names):
    """
    Gets a type either by its full name or its shorthand name or type-qualified name.

    Works by checking for ``shorthand_name`` and ``type_qualified_name`` in the types'
    ``_extensions`` field. See also
    :class:`~aria_extension_tosca.v1_0.presentation.extensible.ExtensiblePresentation`.

    The arguments from the third onwards are used to locate a nested field under
    ``service_template`` under the root presenter.
    """

    if name is not None:
        types_dict = context.presentation.get('service_template', *types_dict_names)
        if types_dict:
            the_type = types_dict.get(name)
            if the_type is not None:
                # Full name
                return the_type
            for the_type in types_dict.itervalues():
                if hasattr(the_type, '_extensions') and the_type._extensions \
                    and ((the_type._extensions.get('shorthand_name') == name) \
                         or (the_type._extensions.get('type_qualified_name') == name)):
                    # Shorthand name
                    return the_type
    return None
