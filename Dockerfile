FROM python:3-alpine
MAINTAINER emw

# Metadata
ARG CROSSBAR_VERSION
ARG BUILD_DATE
ARG CROSSBAR_VCS_REF

# Application home
ENV HOME /node
ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONUNBUFFERED 1

# install dependencies and Crossbar.io
RUN    apk --update upgrade \
    && apk add libffi \
    && apk add --virtual .build-deps \
               build-base \
               libffi-dev \
               openssl-dev \
               linux-headers \
    && pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir crossbar>=${CROSSBAR_VERSION} \
    && apk del .build-deps

# test if everything installed properly
RUN crossbar version

# add our user and group
RUN    addgroup -S -g 242 crossbar \
    && adduser -S -u 242 -D -h /node -G crossbar -g "Crossbar.io Service" crossbar

# initialize a Crossbar.io node

# Crossbar config:
COPY ./.crossbar/config.json /node/.crossbar/config.json 
# Custom crossbar agents: (history and agency_rpcs)
COPY ./*.py /node/
# Web interface (debug):
COPY ./web /node/web
RUN chown -R crossbar:crossbar /node

# make /node a volume to allow external configuration
VOLUME /node

# set the Crossbar.io node directory as working directory
WORKDIR /node

# run under this user, and expose default port
USER crossbar
EXPOSE 8080 8000

# entrypoint for the Docker image is the Crossbar.io executable
ENTRYPOINT ["crossbar", "start", "--cbdir", "/node/.crossbar"]
