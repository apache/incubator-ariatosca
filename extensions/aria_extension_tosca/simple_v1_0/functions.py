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

from cStringIO import StringIO

from aria.utils.collections import FrozenList
from aria.utils.formatting import as_raw, safe_repr
from aria.parser import dsl_specification
from aria.parser.exceptions import InvalidValueError
from aria.parser.validation import Issue
from aria.modeling.exceptions import CannotEvaluateFunctionException
from aria.modeling.functions import Function

#
# Intrinsic
#

@dsl_specification('4.3.1', 'tosca-simple-1.0')
class Concat(Function):
    """
    The :code:`concat` function is used to concatenate two or more string values within a TOSCA
    service template.
    """

    def __init__(self, context, presentation, argument):
        self.locator = presentation._locator

        if not isinstance(argument, list):
            raise InvalidValueError(
                'function "concat" argument must be a list of string expressions: %s'
                % safe_repr(argument),
                locator=self.locator)

        string_expressions = []
        for index, an_argument in enumerate(argument):
            string_expressions.append(parse_string_expression(context, presentation, 'concat',
                                                              index, None, an_argument))
        self.string_expressions = FrozenList(string_expressions)

    @property
    def as_raw(self):
        string_expressions = []
        for string_expression in self.string_expressions:
            if hasattr(string_expression, 'as_raw'):
                string_expression = as_raw(string_expression)
            string_expressions.append(string_expression)
        return {'concat': string_expressions}

    def _evaluate(self, context, container):
        value = StringIO()
        for e in self.string_expressions:
            if hasattr(e, '_evaluate'):
                e = e._evaluate(context, container)
            value.write(str(e))
        return value.getvalue()

@dsl_specification('4.3.2', 'tosca-simple-1.0')
class Token(Function):
    """
    The :code:`token` function is used within a TOSCA service template on a string to parse out
    (tokenize) substrings separated by one or more token characters within a larger string.
    """

    def __init__(self, context, presentation, argument):
        self.locator = presentation._locator

        if (not isinstance(argument, list)) or (len(argument) != 3):
            raise InvalidValueError('function "token" argument must be a list of 3 parameters: %s'
                                    % safe_repr(argument),
                                    locator=self.locator)

        self.string_with_tokens = parse_string_expression(context, presentation, 'token', 0,
                                                          'the string to tokenize', argument[0])
        self.string_of_token_chars = parse_string_expression(context, presentation, 'token', 1,
                                                             'the token separator characters',
                                                             argument[1])
        self.substring_index = parse_int(context, presentation, 'token', 2,
                                         'the 0-based index of the token to return', argument[2])

    @property
    def as_raw(self):
        string_with_tokens = self.string_with_tokens
        if hasattr(string_with_tokens, 'as_raw'):
            string_with_tokens = as_raw(string_with_tokens)
        string_of_token_chars = self.string_with_tokens
        if hasattr(string_of_token_chars, 'as_raw'):
            string_of_token_chars = as_raw(string_of_token_chars)
        return {'token': [string_with_tokens, string_of_token_chars, self.substring_index]}

    def _evaluate(self, context, container):
        string_with_tokens = self.string_with_tokens
        if hasattr(string_with_tokens, '_evaluate'):
            string_with_tokens = string_with_tokens._evaluate(context, container) # pylint: disable=no-member

#
# Property
#

@dsl_specification('4.4.1', 'tosca-simple-1.0')
class GetInput(Function):
    """
    The :code:`get_input` function is used to retrieve the values of properties declared within the
    inputs section of a TOSCA Service Template.
    """

    def __init__(self, context, presentation, argument):
        self.locator = presentation._locator

        self.input_property_name = parse_string_expression(context, presentation, 'get_input',
                                                           None, 'the input property name',
                                                           argument)

        if isinstance(self.input_property_name, basestring):
            the_input = context.presentation.get_from_dict('service_template', 'topology_template',
                                                           'inputs', self.input_property_name)
            if the_input is None:
                raise InvalidValueError(
                    'function "get_input" argument is not a valid input name: %s'
                    % safe_repr(argument),
                    locator=self.locator)

    @property
    def as_raw(self):
        return {'get_input': as_raw(self.input_property_name)}

    def _evaluate(self, context, container): # pylint: disable=unused-argument
        if not context.modeling.instance:
            raise CannotEvaluateFunctionException()
        the_input = context.modeling.instance.inputs.get(
            self.input_property_name,
            context.modeling.template.inputs.get(self.input_property_name))
        return as_raw(the_input.value) if the_input is not None else None

@dsl_specification('4.4.2', 'tosca-simple-1.0')
class GetProperty(Function):
    """
    The :code:`get_property` function is used to retrieve property values between modelable entities
    defined in the same service template.
    """

    def __init__(self, context, presentation, argument):
        self.locator = presentation._locator

        if (not isinstance(argument, list)) or (len(argument) < 2):
            raise InvalidValueError(
                'function "get_property" argument must be a list of at least 2 string expressions: '
                '%s'
                % safe_repr(argument),
                locator=self.locator)

        self.modelable_entity_name = parse_modelable_entity_name(context, presentation,
                                                                 'get_property', 0, argument[0])
        # The first of these will be tried as a req-or-cap name:
        self.nested_property_name_or_index = argument[1:]

    @property
    def as_raw(self):
        return {'get_property': [self.modelable_entity_name] + self.nested_property_name_or_index}

    def _evaluate(self, context, container):
        modelable_entities = get_modelable_entities(context, container, self.locator,
                                                    self.modelable_entity_name)
        req_or_cap_name = self.nested_property_name_or_index[0]

        for modelable_entity in modelable_entities:
            properties = None
            
            if hasattr(modelable_entity, 'requirement_templates') \
                and modelable_entity.requirement_templates \
                and (req_or_cap_name in [v.name for v in modelable_entity.requirement_templates]):
                for requirement_template in modelable_entity.requirement_templates:
                    if requirement_template.name == req_or_cap_name:
                        # First argument refers to a requirement
                        # TODO: should follow to matched capability in other node...
                        raise CannotEvaluateFunctionException()
                        break
                nested_property_name_or_index = self.nested_property_name_or_index[1:]
            elif hasattr(modelable_entity, 'capability_templates') \
                and modelable_entity.capability_templates \
                and (req_or_cap_name in modelable_entity.capability_templates):
                # First argument refers to a capability
                properties = modelable_entity.capability_templates[req_or_cap_name].properties
                nested_property_name_or_index = self.nested_property_name_or_index[1:]
            else:
                properties = modelable_entity.properties
                nested_property_name_or_index = self.nested_property_name_or_index

            if properties:
                found = True
                value = properties
                for name in nested_property_name_or_index:
                    if (isinstance(value, dict) and (name in value)) \
                        or (isinstance(value, list) and name < len(list)):
                        value = value[name]
                        if hasattr(value, '_evaluate'):
                            value = value._evaluate(context, modelable_entity)
                    else:
                        found = False
                        break
                if found:
                    return as_raw(value)

        raise InvalidValueError(
            'function "get_property" could not find "%s" in modelable entity "%s"' \
            % ('.'.join(self.nested_property_name_or_index), self.modelable_entity_name),
            locator=self.locator)

#
# Attribute
#

@dsl_specification('4.5.1', 'tosca-simple-1.0')
class GetAttribute(Function):
    """
    The :code:`get_attribute` function is used to retrieve the values of named attributes declared
    by the referenced node or relationship template name.
    """

    def __init__(self, context, presentation, argument):
        self.locator = presentation._locator

        if (not isinstance(argument, list)) or (len(argument) < 2):
            raise InvalidValueError(
                'function "get_attribute" argument must be a list of at least 2 string expressions:'
                ' %s'
                % safe_repr(argument),
                locator=self.locator)

        self.modelable_entity_name = parse_modelable_entity_name(context, presentation,
                                                                 'get_attribute', 0, argument[0])
        # The first of these will be tried as a req-or-cap name:
        self.nested_property_name_or_index = argument[1:]

    @property
    def as_raw(self):
        return {'get_attribute': [self.modelable_entity_name] + self.nested_property_name_or_index}

    def _evaluate(self, context, container): # pylint: disable=no-self-use,unused-argument
        raise CannotEvaluateFunctionException()

#
# Operation
#

@dsl_specification('4.6.1', 'tosca-simple-1.0')
class GetOperationOutput(Function):
    """
    The :code:`get_operation_output` function is used to retrieve the values of variables exposed /
    exported from an interface operation.
    """

    def __init__(self, context, presentation, argument):
        self.locator = presentation._locator

        if (not isinstance(argument, list)) or (len(argument) != 4):
            raise InvalidValueError(
                'function "get_operation_output" argument must be a list of 4 parameters: %s'
                % safe_repr(argument),
                locator=self.locator)

        self.modelable_entity_name = parse_string_expression(context, presentation,
                                                             'get_operation_output', 0,
                                                             'modelable entity name', argument[0])
        self.interface_name = parse_string_expression(context, presentation, 'get_operation_output',
                                                      1, 'the interface name', argument[1])
        self.operation_name = parse_string_expression(context, presentation, 'get_operation_output',
                                                      2, 'the operation name', argument[2])
        self.output_variable_name = parse_string_expression(context, presentation,
                                                            'get_operation_output', 3,
                                                            'the output name', argument[3])

    @property
    def as_raw(self):
        interface_name = self.interface_name
        if hasattr(interface_name, 'as_raw'):
            interface_name = as_raw(interface_name)
        operation_name = self.operation_name
        if hasattr(operation_name, 'as_raw'):
            operation_name = as_raw(operation_name)
        output_variable_name = self.output_variable_name
        if hasattr(output_variable_name, 'as_raw'):
            output_variable_name = as_raw(output_variable_name)
        return {'get_operation_output': [self.modelable_entity_name, interface_name, operation_name,
                                         output_variable_name]}

#
# Navigation
#

@dsl_specification('4.7.1', 'tosca-simple-1.0')
class GetNodesOfType(Function):
    """
    The :code:`get_nodes_of_type` function can be used to retrieve a list of all known instances of
    nodes of the declared Node Type.
    """

    def __init__(self, context, presentation, argument):
        self.locator = presentation._locator

        self.node_type_name = parse_string_expression(context, presentation, 'get_nodes_of_type',
                                                      None, 'the node type name', argument)

        if isinstance(self.node_type_name, basestring):
            node_types = context.presentation.get('service_template', 'node_types')
            if (node_types is None) or (self.node_type_name not in node_types):
                raise InvalidValueError(
                    'function "get_nodes_of_type" argument is not a valid node type name: %s'
                    % safe_repr(argument),
                    locator=self.locator)

    @property
    def as_raw(self):
        node_type_name = self.node_type_name
        if hasattr(node_type_name, 'as_raw'):
            node_type_name = as_raw(node_type_name)
        return {'get_nodes_of_type': node_type_name}

    def _evaluate(self, context, container):
        pass

#
# Artifact
#

@dsl_specification('4.8.1', 'tosca-simple-1.0')
class GetArtifact(Function):
    """
    The :code:`get_artifact` function is used to retrieve artifact location between modelable
    entities defined in the same service template.
    """

    def __init__(self, context, presentation, argument):
        self.locator = presentation._locator

        if (not isinstance(argument, list)) or (len(argument) < 2) or (len(argument) > 4):
            raise InvalidValueError(
                'function "get_artifact" argument must be a list of 2 to 4 parameters: %s'
                % safe_repr(argument),
                locator=self.locator)

        self.modelable_entity_name = parse_string_expression(context, presentation, 'get_artifact',
                                                             0, 'modelable entity name',
                                                             argument[0])
        self.artifact_name = parse_string_expression(context, presentation, 'get_artifact', 1,
                                                     'the artifact name', argument[1])
        self.location = parse_string_expression(context, presentation, 'get_artifact', 2,
                                                'the location or "LOCAL_FILE"', argument[2])
        self.remove = parse_bool(context, presentation, 'get_artifact', 3, 'the removal flag',
                                 argument[3])

    @property
    def as_raw(self):
        artifact_name = self.artifact_name
        if hasattr(artifact_name, 'as_raw'):
            artifact_name = as_raw(artifact_name)
        location = self.location
        if hasattr(location, 'as_raw'):
            location = as_raw(location)
        return {'get_artifacts': [self.modelable_entity_name, artifact_name, location, self.remove]}

#
# Utils
#

def get_function(context, presentation, value):
    functions = context.presentation.presenter.functions
    if isinstance(value, dict) and (len(value) == 1):
        key = value.keys()[0]
        if key in functions:
            try:
                return True, functions[key](context, presentation, value[key])
            except InvalidValueError as e:
                context.validation.report(issue=e.issue)
                return True, None
    return False, None

def parse_string_expression(context, presentation, name, index, explanation, value): # pylint: disable=unused-argument
    is_function, func = get_function(context, presentation, value)
    if is_function:
        return func
    else:
        value = str(value)
    return value

def parse_int(context, presentation, name, index, explanation, value): # pylint: disable=unused-argument
    if not isinstance(value, int):
        try:
            value = int(value)
        except ValueError:
            raise invalid_value(name, index, 'an integer', explanation, value,
                                presentation._locator)
    return value

def parse_bool(context, presentation, name, index, explanation, value): # pylint: disable=unused-argument
    if not isinstance(value, bool):
        raise invalid_value(name, index, 'a boolean', explanation, value, presentation._locator)
    return value

def parse_modelable_entity_name(context, presentation, name, index, value):
    value = parse_string_expression(context, presentation, name, index, 'the modelable entity name',
                                    value)
    if value == 'SELF':
        the_self, _ = parse_self(presentation)
        if the_self is None:
            raise invalid_modelable_entity_name(name, index, value, presentation._locator,
                                                'a node template or a relationship template')
    elif value == 'HOST':
        _, self_variant = parse_self(presentation)
        if self_variant != 'node_template':
            raise invalid_modelable_entity_name(name, index, value, presentation._locator,
                                                'a node template')
    elif (value == 'SOURCE') or (value == 'TARGET'):
        _, self_variant = parse_self(presentation)
        if self_variant != 'relationship_template':
            raise invalid_modelable_entity_name(name, index, value, presentation._locator,
                                                'a relationship template')
    elif isinstance(value, basestring):
        node_templates = \
            context.presentation.get('service_template', 'topology_template', 'node_templates') \
            or {}
        relationship_templates = \
            context.presentation.get('service_template', 'topology_template',
                                     'relationship_templates') \
            or {}
        if (value not in node_templates) and (value not in relationship_templates):
            raise InvalidValueError(
                'function "%s" parameter %d is not a valid modelable entity name: %s'
                % (name, index + 1, safe_repr(value)),
                locator=presentation._locator, level=Issue.BETWEEN_TYPES)
    return value

def parse_self(presentation):
    from .templates import NodeTemplate, RelationshipTemplate
    from .types import NodeType, RelationshipType

    if presentation is None:
        return None, None
    elif isinstance(presentation, NodeTemplate) or isinstance(presentation, NodeType):
        return presentation, 'node_template'
    elif isinstance(presentation, RelationshipTemplate) \
        or isinstance(presentation, RelationshipType):
        return presentation, 'relationship_template'
    else:
        return parse_self(presentation._container)

@dsl_specification('4.1', 'tosca-simple-1.0')
def get_modelable_entities(context, container, locator, modelable_entity_name):
    """
    The following keywords MAY be used in some TOSCA function in place of a TOSCA Node or
    Relationship Template name.
    """

    if modelable_entity_name == 'SELF':
        return get_self(context, container)
    elif modelable_entity_name == 'HOST':
        return get_host(context, container)
    elif modelable_entity_name == 'SOURCE':
        return get_source(context, container)
    elif modelable_entity_name == 'TARGET':
        return get_target(context, container)
    elif isinstance(modelable_entity_name, basestring):
        node_templates = \
            context.presentation.get('service_template', 'topology_template', 'node_templates') \
            or {}
        if modelable_entity_name in node_templates:
            return [node_templates[modelable_entity_name]]
        relationship_templates = \
            context.presentation.get('service_template', 'topology_template',
                                     'relationship_templates') \
            or {}
        if modelable_entity_name in relationship_templates:
            return [relationship_templates[modelable_entity_name]]

    raise InvalidValueError('function "get_property" could not find modelable entity "%s"'
                            % modelable_entity_name,
                            locator=locator)

def get_self(context, container): # pylint: disable=unused-argument
    """
    A TOSCA orchestrator will interpret this keyword as the Node or Relationship Template instance
    that contains the function at the time the function is evaluated.
    """

    return [container]

def get_host(context, container): # pylint: disable=unused-argument
    """
    A TOSCA orchestrator will interpret this keyword to refer to the all nodes that "host" the node
    using this reference (i.e., as identified by its HostedOn relationship).

    Specifically, TOSCA orchestrators that encounter this keyword when evaluating the get_attribute
    or :code:`get_property` functions SHALL search each node along the "HostedOn" relationship chain
    starting at the immediate node that hosts the node where the function was evaluated (and then
    that node's host node, and so forth) until a match is found or the "HostedOn" relationship chain
    ends.
    """

    return []

def get_source(context, container): # pylint: disable=unused-argument
    """
    A TOSCA orchestrator will interpret this keyword as the Node Template instance that is at the
    source end of the relationship that contains the referencing function.
    """

    return []

def get_target(context, container): # pylint: disable=unused-argument
    """
    A TOSCA orchestrator will interpret this keyword as the Node Template instance that is at the
    target end of the relationship that contains the referencing function.
    """

def invalid_modelable_entity_name(name, index, value, locator, contexts):
    return InvalidValueError('function "%s" parameter %d can be "%s" only in %s'
                             % (name, index + 1, value, contexts),
                             locator=locator, level=Issue.FIELD)

def invalid_value(name, index, the_type, explanation, value, locator):
    return InvalidValueError(
        'function "%s" %s is not %s%s: %s'
        % (name, ('parameter %d' % (index + 1)) if index is not None else 'argument',
           the_type, (', %s' % explanation) if explanation is not None else '', safe_repr(value)),
        locator=locator, level=Issue.FIELD)
