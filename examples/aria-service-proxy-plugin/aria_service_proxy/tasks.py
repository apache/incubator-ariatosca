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

from cloudify.decorators import operation
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError
from datetime import datetime
from aria.cli.core import aria

WAIT_CONFIG_KEY = 'wait_config'
WAIT_TIME_KEY = 'wait_time'
WAIT_FOR_SERVICE_KEY = 'wait_for_service'
WAIT_EXPR_KEY = 'wait_expression'
SERVICE_NAME_KEY = 'service_name'
SERVICE_OUTPUTS_KEY = 'service_outputs'
OUTPUT_KEY = 'outputs'
LAST_UPDATE_KEY = 'last_update'

WORKFLOW_INSTALL = 'install'
WORKFLOW_UNINSTALL = 'uninstall'
WF_SUCCESS_STATUS = 'succeeded'

RETRY_DELAY_SECS = 1

# Only operation exposed.  Waits for proxied service to be ready
# if necessary, then copies selected outputs to node attributes.
#
@operation
def proxy_connect(**kwargs):

    #
    # Collect node configuration
    #

    service_names = get_service_names()

    duration = ctx.node.properties[WAIT_CONFIG_KEY][WAIT_TIME_KEY]

    installed = False

    service_exists = ctx.node.properties[SERVICE_NAME_KEY] in service_names

    if service_exists:
        installed = is_installed(
            service_names[ctx.node.properties[SERVICE_NAME_KEY]])

    wait_for_service = ctx.node.properties[WAIT_CONFIG_KEY][WAIT_FOR_SERVICE_KEY]

    wait_expr = ctx.node.properties[WAIT_CONFIG_KEY].get(WAIT_EXPR_KEY,
                                                       None)

    # If the service doesn't exist, or exists but hasn't been installed,
    # and wait_for_service = true, retry for configured duration.
    #
    if not service_exists or not installed:
        if wait_for_service:
            if duration > ctx.operation.retry_number:
                return ctx.operation.retry(
                    message = 'Waiting for service',
                    retry_after=RETRY_DELAY_SECS)
            else:
                if not service_exists:
                    raise NonRecoverableError(
                        "service {} not found".format(
                            ctx.node.properties[SERVICE_NAME_KEY]))
                else:
                    raise NonRecoverableError(
                        "service {} not installed".format(
                            ctx.node.properties[SERVICE_NAME_KEY]))
        else:
            if not service_exists:
                raise NonRecoverableError(
                    "service {} not found".format(
                        ctx.node.properties[SERVICE_NAME_KEY]))
            else:
                raise NonRecoverableError(
                    "service {} not installed".format(
                        ctx.node.properties[SERVICE_NAME_KEY]))

    # Service ready.  If outputs are configured in proxy, grab them
    elif( ctx.node.properties[OUTPUT_KEY]):
        outputs = service_names[ctx.node.properties[SERVICE_NAME_KEY]].outputs

        # If the outputs are not ready yet, retry
        if not output_equivalence( ctx.node.properties[OUTPUT_KEY], outputs):
            return fail_or_wait(wait_for_service,
                                duration,
                                'Waiting for service outputs',
                                "service {} outputs {} not found".format(
                                    ctx.node.properties[SERVICE_NAME_KEY],
                                    ctx.node.properties[OUTPUT_KEY]))

        # Outputs are ready.  Copy them from target outputs into the
        # this node instance attributes
        else:
            # Success
            # place outputs in attributes
            # final wicket: expression
            if wait_expr:
                if not eval_waitexpr(wait_expr, outputs):
                    return(fail_or_wait(wait_for_service, duration,
                                        "waiting for expr",
                                        "Expr {} evaluates false".format(
                                        wait_expr)))

            service_outputs = []
            if(SERVICE_OUTPUTS_KEY in ctx.instance.runtime_properties and
               ctx.instance.runtime_properties[SERVICE_OUTPUTS_KEY]):
                 service_outputs = list(
                    ctx.instance.runtime_properties[SERVICE_OUTPUTS_KEY])
            for key,val in outputs.iteritems():
                service_outputs.append( dict(name = key,value = val.value))
            ctx.instance.runtime_properties[SERVICE_OUTPUTS_KEY] = service_outputs

            ctx.instance.runtime_properties[LAST_UPDATE_KEY] = str(datetime.utcnow())

    # Service exists, but outputs not configured, so we're done
    else:
        ctx.logger.info("service exists, but no outputs specified = success")


# returns service names
@aria.pass_model_storage
def get_service_names(model_storage):
    """
    Lists all services
    """
    services_list = model_storage.service.list()
    outdict = {}
    for service in services_list:
        outdict[str(service.name)] = service
    return outdict


# Tests whether the list of configured outputs (a simple string list)
# is equivalent # to the list returned from Aria (possible duplicate keys)
def output_equivalence(config_list, service_list):
    sset = set()
    for key, val in service_list.iteritems():
        sset.add(key)
    if not len(sset) == len(config_list):
        return False
    for entry in sset:
        if entry not in config_list:
            return False
    return True


# Looks at the execution history to determine of service is installed
@aria.pass_model_storage
def is_installed(service, model_storage):
    executions = model_storage.execution.list(
        filters=dict(service=service)).items
    for execution in reversed(executions):
        if execution.workflow_name == WORKFLOW_UNINSTALL:
            return False
        if (execution.workflow_name == WORKFLOW_INSTALL and
            execution.status == WF_SUCCESS_STATUS):
            return True
    return False


# Evaluates wait_expr in the context of supplied outputs
def eval_waitexpr(expr, outputs):
    locals = {}
    for key, val in outputs.iteritems():
        locals[key] = val.value
    return eval(expr, locals)

# Convenience function that either fails immediately (if wait_flag
# is false), or tests and retries or fails based on the wait condition
def fail_or_wait( wait_flag, duration, wait_msg, fail_msg ):
    if wait_flag:
        if duration > ctx.operation.retry_number:
            return ctx.operation.retry(
                      message = wait_msg, retry_after=RETRY_DELAY_SECS)
        else:
            raise NonRecoverableError( fail_msg)
    else:
        raise NonRecoverableError( fail_msg)
