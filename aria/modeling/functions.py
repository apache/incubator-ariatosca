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

from ..parser.consumption import ConsumptionContext
from ..parser.exceptions import InvalidValueError
from ..utils.collections import OrderedDict
from . import exceptions


class Function(object):
    """
    Base class for intrinsic functions. Serves as a placeholder for a value that should eventually
    be derived by "evaluating" (calling) the function.

    Note that this base class is provided as a convenience and you do not have to inherit it: any
    object with an ``__evaluate__`` method would be treated similarly.
    """

    @property
    def as_raw(self):
        raise NotImplementedError

    def __evaluate__(self, container_holder):
        """
        Evaluates the function if possible. If impossible, raises
        :class:`CannotEvaluateFunctionException` (do not just return None).

        :rtype: Evaluation (or any object with ``value`` and ``final`` properties)
        """

        raise NotImplementedError

    def __deepcopy__(self, memo):
        # Circumvent cloning in order to maintain our state
        return self


class Evaluation(object):
    """
    An evaluated :class:`Function` return value.
    """

    def __init__(self, value, final=False):
        self.value = value
        self.final = final


def evaluate(value, container_holder, report_issues=False): # pylint: disable=too-many-branches
    """
    Recursively attempts to call ``__evaluate__``. If an evaluation occurred will return an
    :class:`Evaluation`, otherwise it will be None. If any evaluation is non-final, then the entire
    evaluation will also be non-final.

    The ``container_holder`` argument should have three properties: ``container`` should return
    the model that contains the value, ``service`` should return the containing
    :class:`aria.modeling.models.Service` model or None, and ``service_template`` should return the
    containing :class:`aria.modeling.models.ServiceTemplate` model or None.
    """

    evaluated = False
    final = True

    if hasattr(value, '__evaluate__'):
        try:
            evaluation = value.__evaluate__(container_holder)

            # Verify evaluation structure
            if (evaluation is None) \
                or (not hasattr(evaluation, 'value')) \
                or (not hasattr(evaluation, 'final')):
                raise InvalidValueError('bad __evaluate__ implementation')

            evaluated = True
            value = evaluation.value
            final = evaluation.final

            # The evaluated value might itself be evaluable
            evaluation = evaluate(value, container_holder, report_issues)
            if evaluation is not None:
                value = evaluation.value
                if not evaluation.final:
                    final = False
        except exceptions.CannotEvaluateFunctionException:
            pass
        except InvalidValueError as e:
            if report_issues:
                context = ConsumptionContext.get_thread_local()
                context.validation.report(e.issue)

    elif isinstance(value, list):
        evaluated_list = []
        for v in value:
            evaluation = evaluate(v, container_holder, report_issues)
            if evaluation is not None:
                evaluated_list.append(evaluation.value)
                evaluated = True
                if not evaluation.final:
                    final = False
            else:
                evaluated_list.append(v)
        if evaluated:
            value = evaluated_list

    elif isinstance(value, dict):
        evaluated_dict = OrderedDict()
        for k, v in value.iteritems():
            evaluation = evaluate(v, container_holder, report_issues)
            if evaluation is not None:
                evaluated_dict[k] = evaluation.value
                evaluated = True
                if not evaluation.final:
                    final = False
            else:
                evaluated_dict[k] = v
        if evaluated:
            value = evaluated_dict

    return Evaluation(value, final) if evaluated else None
