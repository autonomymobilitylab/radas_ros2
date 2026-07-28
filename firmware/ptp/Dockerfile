FROM ubuntu:24.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    linuxptp \
    gettext-base \ 
    && rm -rf /var/lib/apt/lists/*
