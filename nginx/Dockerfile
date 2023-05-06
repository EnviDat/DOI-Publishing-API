ARG EXTERNAL_REG
ARG INTERNAL_REG
ARG NGINX_VERSION



FROM ${EXTERNAL_REG}/nginx:${NGINX_VERSION}-alpine as run
ARG NGINX_VERSION
ARG MAINTAINER
LABEL envidat.ch.nginx-img-tag="${NGINX_VERSION}" \
      envidat.ch.maintainer="${MAINTAINER_DEVOPS}"
WORKDIR /etc/nginx
# Remove default Nginx static assets
RUN rm -rf ./conf.d/default.conf ./nginx.conf
COPY . .
EXPOSE 80
