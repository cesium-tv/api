FROM alpine:3.18

ENV USERNAME=proxy \
    PASSWORD=proxy

ADD ./docker/squid/squid.conf /etc/squid/squid.conf
ADD ./docker/squid/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN apk add --no-cache squid apache2-utils wget
RUN mkdir -p /etc/squid/conf.d
RUN mkdir -p /var/run/squid  && \
    mkdir -p /var/log/squid/ && \
    chown squid:squid /var/run/squid && \
    chown squid:squid /var/log/squid

EXPOSE 3128

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
CMD [ "https_proxy=\${USERNAME}:\${PASSWORD}@127.0.0.1:3128 http_proxy=\${USERNAME}:\${PASSWORD}@127.0.0.1:3128 && wget -q -Y on  -O - http://httpbin.org/ip || exit 1" ]

ENTRYPOINT [ "/entrypoint.sh" ]
