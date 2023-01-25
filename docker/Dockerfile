FROM python:3-slim-buster AS django

ARG BULMA_VERSION=0.9.4
ARG BUEFY_VERSION=0.9.21

ENV DJANGO_DEBUG=false
ENV DJANGO_DB_HOST=db
ENV DJANGO_DB_PORT=5432
ENV DJANGO_DB_USER=cesium
ENV DJANGO_DB_NAME=cesium
ENV DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,cesium.tv
ENV DJANGO_REDIS_HOST=redis
ENV DJANGO_REDIS_PORT=6379
ENV DJANGO_SCSS_PATH=/var/scss/
ENV DJANGO_MEDIA_ROOT=/app/static/
ENV UWSGI_STATIC=on
ENV PUBLIC_PGP_KEY_FILE=/var/lib/keys/public.pem
ENV PRIVATE_PGP_KEY_FILE=/var/lib/keys/private.pem

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
    wget https://raw.githubusercontent.com/eficode/wait-for/master/wait-for -O /wait-for && \
    pip3 install pipenv && \
    pipenv install --system --dev && \
    apt remove -y git && \
    apt autoremove -y && \
    rm -rf /var/lib/apt/lists/*

RUN find ${DJANGO_SCSS_PATH}
RUN chmod +x /wait-for
ADD ./docker/entrypoint-django.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
RUN mkdir -p /home/nobody
RUN chown nobody:nogroup /home/nobody
RUN usermod -s /bin/sh -d /home/nobody nobody

RUN pyppeteer-install

ENTRYPOINT [ "/entrypoint.sh" ]


FROM node:19-buster-slim AS vue

ENV NODE_OPTIONS=--openssl-legacy-provider

ADD ./ui /app
ADD ./docker/entrypoint-vue.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
WORKDIR /app
RUN npm i --include=dev

ENTRYPOINT [ "/entrypoint.sh" ]


FROM vue as vue-build

RUN npm run build


FROM django AS prod

RUN python3 manage.py collectstatic --noinput
COPY --from=vue-build /app/dist/* ${DJANGO_MEDIA_ROOT}

USER nobody
