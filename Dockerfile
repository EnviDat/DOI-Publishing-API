ARG EXTERNAL_REG
ARG PYTHON_IMG_TAG



FROM ${EXTERNAL_REG}/python:${PYTHON_IMG_TAG}-slim-bullseye as base
ARG APP_VERSION
ARG PYTHON_IMG_TAG
ARG MAINTAINER_APP
ARG MAINTAINER_DEVOPS
LABEL envidat.ch.app-version="${APP_VERSION}" \
      envidat.ch.python-img-tag="${PYTHON_IMG_TAG}" \
      envidat.ch.maintainer-app="${MAINTAINER_APP}" \
      envidat.ch.maintainer-devops="${MAINTAINER_DEVOPS}" \
      envidat.ch.api-port="8000"
RUN set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
        -y --no-install-recommends locales \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*
# Set locale
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8



FROM base as extract-deps
WORKDIR /opt/python
COPY pyproject.toml pdm.lock README.md /opt/python/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir pdm==2.5.6
RUN pdm export --prod > requirements.txt \
    && pdm export --dev --no-default > requirements-dev.txt



FROM base as build
RUN set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
        -y --no-install-recommends \
            build-essential \
            gcc \
    && rm -rf /var/lib/apt/lists/*
COPY --from=extract-deps \
    /opt/python/requirements.txt /opt/python/
RUN pip install --user --no-warn-script-location \
    --no-cache-dir -r /opt/python/requirements.txt



FROM base as runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/home/appuser/.local/bin:$PATH"
RUN set -ex \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
        -y --no-install-recommends \
            nano \
            curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build \
    /root/.local \
    /home/appuser/.local
WORKDIR /opt
COPY . /opt/
# Add appuser user, permissions
RUN useradd -r -u 900 -m -c "appuser account" -d /home/appuser -s /bin/false appuser \
    && chown -R appuser:appuser /opt /home/appuser
USER appuser



FROM runtime as debug
COPY --from=extract-deps \
    /opt/python/requirements-dev.txt /opt/python/
RUN pip install --user --no-warn-script-location \
    --no-cache-dir -r /opt/python/requirements-dev.txt
ENTRYPOINT ["python", "-m", "debugpy", "--listen", \
            "0.0.0.0:5678", "-m"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
    "--reload", "--log-level", "error", "--no-access-log"]


FROM runtime as prod
# Pre-compile packages to .pyc (init perf gains)
RUN python -c "import compileall; compileall.compile_path(maxlevels=10, quiet=1)"
ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["--workers", "1", "--log-level", "error", "--no-access-log"]
