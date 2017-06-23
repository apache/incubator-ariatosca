# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Archive utilities.
"""

import os
import tarfile
import zipfile
import tempfile
from contextlib import closing


def is_archive(source):
    return tarfile.is_tarfile(source) or zipfile.is_zipfile(source)


def extract_archive(source):
    if tarfile.is_tarfile(source):
        return untar(source)
    elif zipfile.is_zipfile(source):
        return unzip(source)
    raise ValueError(
        'Unsupported archive type provided or archive is not valid: {0}.'.format(source))


def tar(source, destination):
    with closing(tarfile.open(destination, 'w:gz')) as tar_archive:
        tar_archive.add(source, arcname=os.path.basename(source))


def untar(archive, destination=None):
    if not destination:
        destination = tempfile.mkdtemp()
    with closing(tarfile.open(name=archive)) as tar_archive:
        tar_archive.extractall(path=destination, members=tar_archive.getmembers())
    return destination


def zip(source, destination):
    with closing(zipfile.ZipFile(destination, 'w')) as zip_file:
        for root, _, files in os.walk(source):
            for filename in files:
                file_path = os.path.join(root, filename)
                source_dir = os.path.dirname(source)
                zip_file.write(
                    file_path, os.path.relpath(file_path, source_dir))
    return destination


def unzip(archive, destination=None):
    if not destination:
        destination = tempfile.mkdtemp()
    with closing(zipfile.ZipFile(archive, 'r')) as zip_file:
        zip_file.extractall(destination)
    return destination
