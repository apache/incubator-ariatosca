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

import sqlalchemy.orm
import sqlalchemy.pool

import aria


def operation_context_to_dict(context):
    context_cls = context.__class__
    context_dict = {
        'name': context.name,
        'deployment_id': context._deployment_id,
        'task_id': context._task_id,
        'actor_id': context._actor_id,
    }
    if context.model:
        model = context.model
        context_dict['model_storage'] = {
            'api_cls': model.api,
            'api_kwargs': _serialize_sql_mapi_kwargs(model)
        }
    else:
        context_dict['model_storage'] = None
    if context.resource:
        resource = context.resource
        context_dict['resource_storage'] = {
            'api_cls': resource.api,
            'api_kwargs': _serialize_file_rapi_kwargs(resource)
        }
    else:
        context_dict['resource_storage'] = None
    return {
        'context_cls': context_cls,
        'context': context_dict
    }


def operation_context_from_dict(context_dict):
    context_cls = context_dict['context_cls']
    context = context_dict['context']

    model_storage = context['model_storage']
    if model_storage:
        api_cls = model_storage['api_cls']
        api_kwargs = _deserialize_sql_mapi_kwargs(model_storage.get('api_kwargs', {}))
        context['model_storage'] = aria.application_model_storage(api=api_cls,
                                                                  api_kwargs=api_kwargs)

    resource_storage = context['resource_storage']
    if resource_storage:
        api_cls = resource_storage['api_cls']
        api_kwargs = _deserialize_file_rapi_kwargs(resource_storage.get('api_kwargs', {}))
        context['resource_storage'] = aria.application_resource_storage(api=api_cls,
                                                                        api_kwargs=api_kwargs)

    return context_cls(**context)


def _serialize_sql_mapi_kwargs(model):
    return {
        'engine_url': str(model._api_kwargs['engine'].url)
    }


def _deserialize_sql_mapi_kwargs(api_kwargs):
    engine_url = api_kwargs.get('engine_url')
    if not engine_url:
        return {}
    engine = sqlalchemy.create_engine(engine_url)
    session_factory = sqlalchemy.orm.sessionmaker(bind=engine)
    session = sqlalchemy.orm.scoped_session(session_factory=session_factory)
    return {'session': session, 'engine': engine}


def _serialize_file_rapi_kwargs(resource):
    return {'directory': resource._api_kwargs['directory']}


def _deserialize_file_rapi_kwargs(api_kwargs):
    return api_kwargs
