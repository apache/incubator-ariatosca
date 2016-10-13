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

import os
import subprocess
from signal import SIGKILL
from time import sleep

from aria.logger import LoggerMixin
from aria.exceptions import ExecutorException, ProcessException


class Process(LoggerMixin):
    def __init__(
            self,
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=None,
            env=None,
            **kwargs):
        """
        Process class - subprocess wrapper
        :param args:
        :param stdout:
        :param stderr:
        :param cwd:
        :param env:
        """
        super(Process, self).__init__(**kwargs)
        self.args = args
        self.cwd = cwd
        self.env = env
        self.process = None
        self._stdout = stdout
        self._stderr = stderr

    def __repr__(self):
        return '{cls.__name__}(args=self.args, cwd=self.cwd)'.format(
            cls=self.__class__, self=self)

    def __getattr__(self, item):
        return getattr(self.process, item)

    @property
    def name(self):
        return self.args[0]

    @property
    def pid(self):
        if self.is_running():
            return self.process.pid

    @property
    def stdout(self):
        assert self.process, 'Need to run before calling thie method'
        return self.process.stdout

    @property
    def stderr(self):
        assert self.process, 'Need to run before calling thie method'
        return self.process.stderr

    @property
    def return_code(self):
        if self.process is None:
            return None
        if self.is_running():
            raise ExecutorException(
                'Can not get return code while process is still running')
        if self.process.returncode is None:
            self.wait()
        return self.process.returncode

    def terminate(self):
        if self.process is not None and self.process.poll() is None:
            self.logger.debug('terminating process {0:d} ({1})'.format(self.process.pid, self.name))
            self.process.terminate()
            sleep(1)
        kill_attempts = 0
        while self.process is not None and self.process.poll() is None and kill_attempts < 10:
            self.logger.debug('trying to kill process {0:d}'.format(self.process.pid))
            self.process.kill()
            sleep(1)
            kill_attempts += 1

    def killpg(self):
        if self.is_running():
            os.killpg(os.getpgid(self.pid), SIGKILL)

    def is_running(self):
        return self.process.poll() is None if self.process else False

    def wait(self):
        """
        Block till child process finishes
        """
        assert self.process, 'Need to run before calling thie method'
        self.process.wait()

    def run(self, nice=None, universal_newlines=True):
        """
        Run the child process. This call does not block.
        :param int nice: nice on the child process run
        :param bool universal_newlines:
        """
        self.logger.debug('Running child process: {0}'.format(' '.join(self.args)))
        self.process = subprocess.Popen(
            self.args,
            cwd=self.cwd,
            env=self.env,
            stdout=self._stdout,
            stderr=self._stderr,
            close_fds=os.name != 'nt',
            preexec_fn=lambda: os.nice(nice) if nice else None,
            universal_newlines=universal_newlines)

    def run_in_shell(self, nice=None, universal_newlines=True):
        command = ' '.join(self.args)
        self.logger.debug('Running child process in shell: {0}'.format(command))
        self.process = subprocess.Popen(
            command,
            shell=True,
            cwd=self.cwd,
            env=self.env,
            stdout=self._stdout,
            stderr=self._stderr,
            close_fds=os.name != 'nt',
            preexec_fn=lambda: os.nice(nice) if nice else None,
            universal_newlines=universal_newlines)

    def raise_failure(self):
        if self.is_running():
            self.wait()
        if self.return_code == 0:
            return
        raise ProcessException(
            command=self.args,
            stderr=self.stderr.read(),
            stdout=self.stdout.read(),
            return_code=self.return_code)
