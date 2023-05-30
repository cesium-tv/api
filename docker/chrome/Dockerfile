FROM zenika/alpine-chrome

ENV PORT=9222
USER root

ADD ./docker/chrome/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN apk add --no-cache socat

USER chrome
ENTRYPOINT [ "/entrypoint.sh" ]
