## Dockerfile
## https://docker.github.io/engine/reference/builder/

FROM python:3.10-slim as production

RUN set -eux; \
  apt update \
  && DEBIAN_FRONTEND=noninteractive apt install --no-install-recommends -yq \
  wait-for-it \
  libpq-dev \
  && rm -rf /var/lib/apt/lists/*

COPY . /app/

RUN set -eux; \
  python3 -m pip install --upgrade pip \
  && cd /app/ \
  && python3 -m pip install -r requirements.txt

COPY entrypoint.sh /usr/bin/entrypoint.sh

WORKDIR /app

ENTRYPOINT [ "/usr/bin/entrypoint.sh" ]
CMD [  ]

