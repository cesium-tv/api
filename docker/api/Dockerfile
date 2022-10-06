FROM python:3-slim-buster AS python

ARG BULMA_VERSION=0.9.4
ARG BUEFY_VERSION=0.9.21

ENV DJANGO_DEBUG=false \
    DJANGO_DB_HOST= \
    DJANGO_DB_PORT=5432 \
    DJANGO_DB_USER= \
    DJANGO_DB_NAME=cesium \
    DJANGO_DB_PASSWORD= \
    DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,cesium.tv \
    DJANGO_REDIS_HOST=redis \
    DJANGO_REDIS_PORT=6379 \
    DJANGO_SCSS_PATH=/var/scss \
    UWSGI_STATIC=on

ADD ./api /app

RUN mkdir -p ${DJANGO_SCSS_PATH}
WORKDIR /app

RUN apt update && \
    apt install -y \
        git postgresql-client gcc libffi-dev gconf-service libasound2 procps \
        libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 \
        libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 \
        libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 \
        libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 \
        libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 ca-certificates \
        fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils wget netcat && \
    wget -qO- https://github.com/jgthms/bulma/archive/refs/tags/${BULMA_VERSION}.tar.gz /| \
        tar xzf - --strip=1 --one-top-level=${DJANGO_SCSS_PATH}/bulma bulma-${BULMA_VERSION}/sass bulma-${BULMA_VERSION}/bulma.sass && \
    wget -qO- https://github.com/buefy/buefy/archive/refs/tags/v${BUEFY_VERSION}.tar.gz | \
        tar xzf - --strip=1 --one-top-level=${DJANGO_SCSS_PATH}/buefy buefy-${BUEFY_VERSION}/src/scss && \
    wget -O ${DJANGO_SCSS_PATH}/bulma-divider.sass  https://raw.githubusercontent.com/Wikiki/bulma-divider/master/src/sass/index.sass && \
    wget https://raw.githubusercontent.com/eficode/wait-for/master/wait-for -O /wait-for && \
    pip3 install pipenv && \
    pipenv install --system --dev && \
    pyppeteer-install && \
    apt remove -y git wget && \
    apt autoremove -y && \
    rm -rf /var/lib/apt/lists/*

RUN find ${DJANGO_SCSS_PATH}
RUN chmod +x /wait-for
ADD ./docker/api/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
RUN usermod -s /bin/sh nobody

RUN python3 manage.py collectstatic --noinput

ENTRYPOINT [ "/entrypoint.sh" ]
