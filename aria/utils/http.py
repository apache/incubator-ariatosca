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
HTTP utilities.
"""

import os
import tempfile

import requests


def download_file(url, destination=None, logger=None, progress_handler=None):
    """
    Download file.

    :param url: URL from which to download
    :type url: basestring
    :param destination: path where the file should be saved or ``None`` to auto-generate
    :type destination: basestring
    :returns: path where the file was saved
    :rtype: basestring
    :raises exceptions.IOError:
    :raises requests.exceptions.RequestException:
    """
    chunk_size = 1024

    if not destination:
        file_descriptor, destination = tempfile.mkstemp()
        os.close(file_descriptor)
    if logger:
        logger.info('Downloading {0} to {1}...'.format(url, destination))

    response = requests.get(url, stream=True)
    final_url = response.url
    if final_url != url and logger:
        logger.debug('Redirected to {0}'.format(final_url))

    read_bytes = 0
    total_size = int(response.headers['Content-Length']) \
        if 'Content-Length' in response.headers else None
    try:
        with open(destination, 'wb') as destination_file:
            for chunk in response.iter_content(chunk_size):
                destination_file.write(chunk)
                if total_size and progress_handler:
                    # Only showing progress bar if we have the total content length
                    read_bytes += chunk_size
                    progress_handler(read_bytes, total_size)
    finally:
        response.close()

    return destination
