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
Modeling exceptions.
"""

from ..exceptions import AriaException


class ModelingException(AriaException):
    """
    ARIA modeling exception.
    """


class ParameterException(ModelingException):
    """
    ARIA parameter exception.
    """
    pass


class ValueFormatException(ModelingException):
    """
    ARIA modeling exception: the value is in the wrong format.
    """


class CannotEvaluateFunctionException(ModelingException):
    """
    ARIA modeling exception: cannot evaluate the function at this time.
    """


class MissingRequiredParametersException(ParameterException):
    """
    ARIA modeling exception: Required parameters have been omitted.
    """


class ParametersOfWrongTypeException(ParameterException):
    """
    ARIA modeling exception: Parameters of the wrong types have been provided.
    """


class UndeclaredParametersException(ParameterException):
    """
    ARIA modeling exception: Undeclared parameters have been provided.
    """
