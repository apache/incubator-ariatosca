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


# This implementation was copied from the Fabric project directly:
# https://github.com/fabric/fabric/blob/master/fabric/context_managers.py#L486
# The purpose was to remove the rtunnel creation printouts here:
# https://github.com/fabric/fabric/blob/master/fabric/context_managers.py#L547


import contextlib
import select
import socket

import fabric.api
import fabric.state
import fabric.thread_handling


@contextlib.contextmanager
def remote(ctx, local_port, remote_port=0, local_host='localhost', remote_bind_address='127.0.0.1'):
    """Create a tunnel forwarding a locally-visible port to the remote target."""
    sockets = []
    channels = []
    thread_handlers = []

    def accept(channel, *args, **kwargs):
        # This seemingly innocent statement seems to be doing nothing
        # but the truth is far from it!
        # calling fileno() on a paramiko channel the first time, creates
        # the required plumbing to make the channel valid for select.
        # While this would generally happen implicitly inside the _forwarder
        # function when select is called, it may already be too late and may
        # cause the select loop to hang.
        # Specifically, when new data arrives to the channel, a flag is set
        # on an "event" object which is what makes the select call work.
        # problem is this will only happen if the event object is not None
        # and it will be not-None only after channel.fileno() has been called
        # for the first time. If we wait until _forwarder calls select for the
        # first time it may be after initial data has reached the channel.
        # calling it explicitly here in the paramiko transport main event loop
        # guarantees this will not happen.
        channel.fileno()

        channels.append(channel)
        sock = socket.socket()
        sockets.append(sock)

        try:
            sock.connect((local_host, local_port))
        except Exception as e:
            try:
                channel.close()
            except Exception as ex2:
                close_error = ' (While trying to close channel: {0})'.format(ex2)
            else:
                close_error = ''
            ctx.task.abort('[{0}] rtunnel: cannot connect to {1}:{2} ({3}){4}'
                           .format(fabric.api.env.host_string, local_host, local_port, e,
                                   close_error))

        thread_handler = fabric.thread_handling.ThreadHandler('fwd', _forwarder, channel, sock)
        thread_handlers.append(thread_handler)

    transport = fabric.state.connections[fabric.api.env.host_string].get_transport()
    remote_port = transport.request_port_forward(
        remote_bind_address, remote_port, handler=accept)

    try:
        yield remote_port
    finally:
        for sock, chan, thread_handler in zip(sockets, channels, thread_handlers):
            sock.close()
            chan.close()
            thread_handler.thread.join()
            thread_handler.raise_if_needed()
        transport.cancel_port_forward(remote_bind_address, remote_port)


def _forwarder(chan, sock):
    # Bidirectionally forward data between a socket and a Paramiko channel.
    while True:
        read = select.select([sock, chan], [], [])[0]
        if sock in read:
            data = sock.recv(1024)
            if len(data) == 0:
                break
            chan.send(data)
        if chan in read:
            data = chan.recv(1024)
            if len(data) == 0:
                break
            sock.send(data)
    chan.close()
    sock.close()
