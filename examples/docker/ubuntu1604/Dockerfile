FROM ubuntu:16.04

#COMMAND TO BUILD THE IMAGE ==> docker build --build-arg ARIA_VER=0.1.1 --build-arg GTAG_VER=0.1.1 -t aria_011:16.04 .
ARG ARIA_VER=0.1.1
ARG GTAG_VER=0.1.1

RUN apt-get update && apt-get install -y \
    python-dev \
    gcc \
    libffi-dev \
    libssl-dev \
    python-pip \
    git \
    wget

RUN pip install --upgrade pip setuptools

RUN pip install apache-ariatosca[ssh]==$ARIA_VER apache-ariatosca

WORKDIR /tmp

RUN git clone https://github.com/apache/incubator-ariatosca.git /tmp/incubator-ariatosca

WORKDIR /tmp/incubator-ariatosca

RUN git checkout tags/$GTAG_VER