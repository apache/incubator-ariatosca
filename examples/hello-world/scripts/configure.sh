#!/bin/bash

set -e

TEMP_DIR="/tmp"
PYTHON_FILE_SERVER_ROOT=${TEMP_DIR}/python-simple-http-webserver
if [ -d ${PYTHON_FILE_SERVER_ROOT} ]; then
	echo "Removing file server root folder ${PYTHON_FILE_SERVER_ROOT}"
	rm -rf ${PYTHON_FILE_SERVER_ROOT}
fi
ctx logger info "Creating HTTP server root directory at ${PYTHON_FILE_SERVER_ROOT}"

mkdir -p ${PYTHON_FILE_SERVER_ROOT}

cd ${PYTHON_FILE_SERVER_ROOT}

index_path="index.html"
image_path="images/aria-logo.png"

ctx logger info "Downloading blueprint resources..."
ctx download-resource-and-render ${PYTHON_FILE_SERVER_ROOT}/index.html ${index_path}
ctx download-resource ${PYTHON_FILE_SERVER_ROOT}/aria-logo.png ${image_path}

