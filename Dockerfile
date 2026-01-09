ARG EXTERNAL_REG
ARG PYTHON_IMG_TAG

# ------------------------------
# Base
# ------------------------------
FROM ${EXTERNAL_REG}/python:${PYTHON_IMG_TAG}-slim-bookworm as base
ARG APP_VERSION

LABEL envidat.ch.app-version="${APP_VERSION}" \
      envidat.ch.python-img-tag="${PYTHON_IMG_TAG}" \
      envidat.ch.api-port="8000"

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install \
        -y --no-install-recommends \
        locales \
        git \
        build-essential \
        python3-dev \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*
# Set locale
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8


# ------------------------------------------
# Deps (install dependencies from pdm.lock)
# ------------------------------------------
FROM base as deps
WORKDIR /opt/app

ENV HOME=/root
ENV PDM_VENV_IN_PROJECT=true

COPY pyproject.toml pdm.lock README.md ./

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip pdm

RUN pdm config python.use_venv true \
    && pdm sync --prod -v


# ------------------------------
# Build (copy full source)
# ------------------------------
FROM deps as build
COPY . .


# ------------------------------
# Runtime
# ------------------------------
FROM base as runtime

COPY --from=build /opt/app /opt/app

RUN useradd -r -u 900 -m -s /bin/false appuser

WORKDIR /opt/app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/opt/app/.venv/bin:$PATH"

USER appuser


# ------------------------------
# Prod start
# ------------------------------
ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["--workers", "1", "--log-level", "error", "--no-access-log"]