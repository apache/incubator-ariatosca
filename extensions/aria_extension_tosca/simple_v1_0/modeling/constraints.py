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

import re

from aria.modeling.contraints import NodeTemplateConstraint
from aria.modeling.utils import NodeTemplateContainerHolder
from aria.modeling.functions import evaluate
from aria.parser import implements_specification


@implements_specification('3.5.2-2', 'tosca-simple-1.0')
class EvaluatingNodeTemplateConstraint(NodeTemplateConstraint):
    """
    A version of :class:`NodeTemplateConstraint` with boilerplate initialization for TOSCA
    constraints.
    """

    def __init__(self, property_name, capability_name, constraint, as_list=False):
        self.property_name = property_name
        self.capability_name = capability_name
        self.constraint = constraint
        self.as_list = as_list

    def matches(self, source_node_template, target_node_template):
        # TOSCA node template constraints can refer to either capability properties or node
        # template properties
        if self.capability_name is not None:
            # Capability property
            capability = target_node_template.capability_templates.get(self.capability_name)
            value = capability.properties.get(self.property_name) \
                if capability is not None else None # Parameter
        else:
            # Node template property
            value = target_node_template.properties.get(self.property_name) # Parameter

        value = value.value if value is not None else None

        container_holder = NodeTemplateContainerHolder(source_node_template)

        if self.as_list:
            constraints = []
            for constraint in self.constraint:
                evaluation = evaluate(constraint, container_holder)
                if evaluation is not None:
                    constraints.append(evaluation.value)
                else:
                    constraints.append(constraint)
            constraint = constraints
        else:
            evaluation = evaluate(self.constraint, container_holder)
            if evaluation is not None:
                constraint = evaluation.value
            else:
                constraint = self.constraint

        return self.matches_evaluated(value, constraint)

    def matches_evaluated(self, value, constraint):
        raise NotImplementedError


class Equal(EvaluatingNodeTemplateConstraint):
    def matches_evaluated(self, value, constraint):
        return value == constraint


class GreaterThan(EvaluatingNodeTemplateConstraint):
    def matches_evaluated(self, value, constraint):
        return value > constraint


class GreaterOrEqual(EvaluatingNodeTemplateConstraint):
    def matches_evaluated(self, value, constraint):
        return value >= constraint


class LessThan(EvaluatingNodeTemplateConstraint):
    def matches_evaluated(self, value, constraint):
        return value < constraint


class LessOrEqual(EvaluatingNodeTemplateConstraint):
    def matches_evaluated(self, value, constraint):
        return value <= constraint


class InRange(EvaluatingNodeTemplateConstraint):
    def __init__(self, property_name, capability_name, constraint):
        super(InRange, self).__init__(property_name, capability_name, constraint, as_list=True)

    def matches_evaluated(self, value, constraints):
        lower, upper = constraints
        if value < lower:
            return False
        if (upper != 'UNBOUNDED') and (value > upper):
            return False
        return True


class ValidValues(EvaluatingNodeTemplateConstraint):
    def __init__(self, property_name, capability_name, constraint):
        super(ValidValues, self).__init__(property_name, capability_name, constraint, as_list=True)

    def matches_evaluated(self, value, constraints):
        return value in constraints


class Length(EvaluatingNodeTemplateConstraint):
    def matches_evaluated(self, value, constraint):
        return len(value) == constraint


class MinLength(EvaluatingNodeTemplateConstraint):
    def matches_evaluated(self, value, constraint):
        return len(value) >= constraint


class MaxLength(EvaluatingNodeTemplateConstraint):
    def matches_evaluated(self, value, constraint):
        return len(value) <= constraint


class Pattern(EvaluatingNodeTemplateConstraint):
    def matches_evaluated(self, value, constraint):
        # From TOSCA 1.0 3.5.2.1:
        #
        # "Note: Future drafts of this specification will detail the use of regular expressions and
        # reference an appropriate standardized grammar."
        #
        # So we will just use Python's.
        return re.match(constraint, unicode(value)) is not None
