#!/bin/sh -x

if [ ! -z "${PROXY_SERVER}" ]; then
    ARGS=" --proxy-server=${PROXY_SERVER}"
fi

chromium-browser --headless --remote-debugging-address=0.0.0.0 --remote-debugging-port=9223${ARGS} &

socat -d TCP4-LISTEN:${PORT},fork TCP4:localhost:9223
