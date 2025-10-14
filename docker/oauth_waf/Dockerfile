#
# NOTE: THIS DOCKERFILE IS GENERATED VIA "update.sh"
#
# PLEASE DO NOT EDIT IT DIRECTLY.
#

ARG MODSECURITY_VERSION

FROM  owasp/modsecurity:nginx-alpine

ENV DEBIAN_FRONTEND=noninteractive

# -- All configuration files are generated from Ansible and Mapped as part of the docker up.
COPY docker/oauth_waf/nginx.conf /etc/nginx/nginx.conf
COPY docker/oauth_waf/modsecurity/ /etc/modsecurity.d/
COPY docker/oauth_waf/modsecurity/include.conf /etc/modsecurity.d/include.conf

COPY docker/oauth_waf/nginx/nginx.conf /etc/nginx/nginx.conf
COPY docker/oauth_waf/nginx/guacamole.octoengine.com.conf /etc/nginx/conf.d/guacamole.octoengine.com.conf

RUN rm -rf /docker-entrypoint.d/90-copy-modsecurity-config.sh \
    && rm -rf /docker-entrypoint.d/* 

