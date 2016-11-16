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

from aria.utils.collections import OrderedDict

#
# NodeType, NodeTemplate
#


def get_inherited_artifact_definitions(context, presentation, for_presentation=None):

    if hasattr(presentation, '_get_type'):
        # In NodeTemplate
        parent = presentation._get_type(context)
    else:
        # In NodeType
        parent = presentation._get_parent(context)

    # Get artifact definitions from parent
    artifacts = get_inherited_artifact_definitions(context, parent, for_presentation=presentation) \
        if parent is not None else OrderedDict()

    # Add/override our artifact definitions
    our_artifacts = presentation.artifacts
    if our_artifacts:
        for artifact_name, artifact in our_artifacts.iteritems():
            artifacts[artifact_name] = artifact._clone(for_presentation)

    return artifacts
