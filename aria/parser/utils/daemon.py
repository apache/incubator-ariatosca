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

from __future__ import absolute_import  # so we can import standard 'daemon'

try:
    import os
    import signal
    from time import sleep
    from .console import puts, Colored
    from daemon import DaemonContext
    from daemon.pidfile import TimeoutPIDLockFile
    from daemon.runner import is_pidfile_stale

    def start_daemon(pidfile_path, log_path, acquire_timeout=5):
        pidfile = TimeoutPIDLockFile(pidfile_path, acquire_timeout=acquire_timeout)
        if is_pidfile_stale(pidfile):
            pidfile.break_lock()
        if pidfile.is_locked():
            pid = pidfile.read_pid()
            if pid is not None:
                puts(Colored.red('Already running at pid: %d' % pid))
            else:
                puts(Colored.red('Already running'))
            return None
        logfile = open(log_path, 'w+t')
        puts(Colored.blue('Starting'))
        return DaemonContext(pidfile=pidfile, stdout=logfile, stderr=logfile)

    def stop_daemon(pidfile_path, acquire_timeout=5):
        pidfile = TimeoutPIDLockFile(pidfile_path, acquire_timeout=acquire_timeout)
        pid = pidfile.read_pid()
        if pid is not None:
            puts(Colored.blue('Stopping pid: %d' % pid))
            os.kill(pid, signal.SIGTERM)
            while pidfile.is_locked():
                puts(Colored.cyan('Waiting...'))
                sleep(0.1)
            puts(Colored.blue('Stopped'))
        else:
            puts(Colored.red('Not running'))

    def status_daemon(pidfile_path, acquire_timeout=5):
        pid = TimeoutPIDLockFile(pidfile_path, acquire_timeout=acquire_timeout).read_pid()
        if pid is not None:
            puts(Colored.blue('Running at pid: %d' % pid))
        else:
            puts(Colored.blue('Not running'))

except ImportError:
    def start_daemon(*args, **kwargs):
        puts(Colored.red('Cannot start daemon in this environment'))

    def stop_daemon(*args, **kwargs):
        puts(Colored.red('Not running'))

    def status_daemon(*args, **kwargs):
        puts(Colored.blue('Not running'))
