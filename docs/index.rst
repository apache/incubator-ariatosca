..
   Licensed to the Apache Software Foundation (ASF) under one or more
   contributor license agreements.  See the NOTICE file distributed with
   this work for additional information regarding copyright ownership.
   The ASF licenses this file to You under the Apache License, Version 2.0
   (the "License"); you may not use this file except in compliance with
   the License.  You may obtain a copy of the License at
   
       http://www.apache.org/licenses/LICENSE-2.0
   
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

User Manual for ARIA TOSCA
==========================

`ARIA TOSCA <http://ariatosca.incubator.apache.org/>`__ is an open, light, CLI-driven library of
orchestration tools that other open projects can consume to easily build
`TOSCA <https://www.oasis-open.org/committees/tosca/>`__-based orchestration solutions. ARIA is now
an incubation project at the Apache Software Foundation.  

Interfaces
----------

.. toctree::
   :maxdepth: 1
   :includehidden:

   cli
   rest

SDK
---

Core
####

.. toctree::
   :maxdepth: 1
   :includehidden:

   aria
   aria.cli
   aria.modeling
   aria.modeling.models
   aria.orchestrator
   aria.orchestrator.context
   aria.orchestrator.execution_plugin
   aria.orchestrator.execution_plugin.ctx_proxy
   aria.orchestrator.execution_plugin.ssh
   aria.orchestrator.workflows
   aria.orchestrator.workflows.api
   aria.orchestrator.workflows.builtin
   aria.orchestrator.workflows.executor
   aria.parser
   aria.parser.consumption
   aria.parser.loading
   aria.parser.modeling
   aria.parser.presentation
   aria.parser.reading
   aria.parser.validation
   aria.storage
   aria.utils

Extensions
##########

.. toctree::
   :maxdepth: 1
   :includehidden:

   aria_extension_tosca.simple_v1_0
   aria_extension_tosca.simple_v1_0.modeling
   aria_extension_tosca.simple_v1_0.presentation
   aria_extension_tosca.simple_nfv_v1_0


Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
