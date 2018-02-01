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

@operation
def proxy_connect(**kwargs):

    service_names = get_service_names()

    duration = ctx.node.properties['wait_config']['wait_time']

    installed = False

    service_exists = ctx.node.properties['service_name'] in service_names

    if service_exists:
        installed = is_installed(
            service_names[ctx.node.properties['service_name']])

    wait_for_service =  ctx.node.properties['wait_config']['wait_for_service']

    wait_expr = ctx.node.properties['wait_config'].get('wait_expression',
                                                       None)

    if not service_exists or not installed:
        if wait_for_service:
            if duration > ctx.operation.retry_number:
                return ctx.operation.retry(
                    message = 'Waiting for service', retry_after=1)
            else:
                if not service_exists:
                    raise NonRecoverableError(
                        "service {} not found".format(
                            ctx.node.properties['service_name']))
                else:
                    raise NonRecoverableError(
                        "service {} not installed".format(
                            ctx.node.properties['service_name']))
        else:
            if not service_exists:
                raise NonRecoverableError(
                    "service {} not found".format(
                        ctx.node.properties['service_name']))
            else:
                raise NonRecoverableError(
                    "service {} not installed".format(
                        ctx.node.properties['service_name']))

    # Service exists, so see if outputs exist yet
    elif( ctx.node.properties['outputs']):
        outputs = service_names[ctx.node.properties['service_name']].outputs
        if not output_equivalence( ctx.node.properties['outputs'], outputs):
            return fail_or_wait(wait_for_service,
                                duration,
                                'Waiting for service outputs',
                                "service {} outputs {} not found".format(
                                    ctx.node.properties['service_name'],
                                    ctx.node.properties['outputs']))

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
            if('service_outputs' in ctx.instance.runtime_properties and
               ctx.instance.runtime_properties['service_outputs']):
                 service_outputs = list(
                    ctx.instance.runtime_properties['service_outputs'])
            for k,v in outputs.iteritems():
                service_outputs.append( dict(name = k,value = v.value))
            ctx.instance.runtime_properties['service_outputs'] = service_outputs

            ctx.instance.runtime_properties['last_update'] = str(datetime.utcnow())
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


# Tests whether the list of configured outputs (a simple string list) is equivalent
# to the list returned from Aria (possible duplicate keys)
def output_equivalence( config_list, service_list ):
    sset = set()
    for k,v in service_list.iteritems():
        sset.add( k )
    if not len(sset) == len(config_list):
        return False
    for entry in sset:
        if not entry in config_list:
            return False
    return True

# Looks at the execution history to determine of service is installed
@aria.pass_model_storage
def is_installed( service, model_storage ):
    executions = model_storage.execution.list(
        filters=dict(service=service)).items
    for e in reversed(executions):
        if e.workflow_name == "uninstall":
            return False
        if e.workflow_name == "install" and e.status == "succeeded":
            return True
    return False

# Evaluates wait_expr in the context of supplied outputs
def eval_waitexpr( expr, outputs):
    locals = {}
    for k,v in outputs.iteritems():
        locals[k] = v.value
    return eval(expr,locals)

def fail_or_wait( wait_flag, duration, wait_msg, fail_msg ):
    if wait_flag:
        if duration > ctx.operation.retry_number:
            return ctx.operation.retry(
                      message = wait_msg, retry_after=1)
        else:
            raise NonRecoverableError( fail_msg)
    else:
        raise NonRecoverableError( fail_msg)
