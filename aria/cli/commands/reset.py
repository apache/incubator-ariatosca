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
CLI ``reset`` command.
"""

from .. import helptexts
from ..core import aria
from ..env import env
from ..exceptions import AriaCliError


@aria.command(name='reset',
              short_help="Reset ARIA working directory")
@aria.options.force(help=helptexts.FORCE_RESET)
@aria.options.reset_config
@aria.pass_logger
@aria.options.verbose()
def reset(force, reset_config, logger):
    """
    Reset ARIA working directory

    Deletes installed plugins, service templates, services, executions, and logs. The user
    configuration will remain intact unless the `--reset_config` flag has been set as well, in
    which case the entire ARIA working directory shall be removed.
    """
    if not force:
        raise AriaCliError("To reset the ARIA's working directory, you must also provide the force"
                           " flag ('-f'/'--force').")

    env.reset(reset_config=reset_config)
    logger.info("ARIA's working directory has been reset")
