ARG EXTERNAL_REG
ARG NGINX_IMG_TAG



FROM ${EXTERNAL_REG}/debian:bookworm AS certs
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates



FROM ${EXTERNAL_REG}/nginx:${NGINX_IMG_TAG} as run
# CA-Certs
COPY --from=certs \
    /etc/ssl/certs/ca-certificates.crt \
    /etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ARG NGINX_IMG_TAG
ARG MAINTAINER_DEVOPS
LABEL envidat.ch.nginx-img-tag="${NGINX_IMG_TAG}" \
      envidat.ch.maintainer="${MAINTAINER_DEVOPS}" \
      envidat.ch.nginx-port="80"
WORKDIR /etc/nginx
# Remove default Nginx static assets
RUN rm -rf ./conf.d/default.conf ./nginx.conf
COPY . .
