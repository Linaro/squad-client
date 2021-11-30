FROM docker.io/library/python:3.9-alpine

ENV BUILD_DEPS="\
    build-base \
    yaml-dev \
"

ENV RUNTIME_DEPS="\
    bash \
    yaml \
"

WORKDIR /squad_client
COPY . ./

RUN set -e ;\
    apk update ;\
    apk add --no-cache --virtual .build-deps ${BUILD_DEPS} ;\
    apk add --no-cache ${RUNTIME_DEPS} ;\
    SQUAD_CLIENT_RELEASE=1 pip install --no-cache-dir . ;\
    # List packages and python modules installed
    apk info -vv | sort ;\
    pip freeze ;\
    # Cleanup
    apk del --no-cache --purge .build-deps ;\
    rm -rf /var/cache/apk/* /tmp/* /squad_client

WORKDIR /reports
