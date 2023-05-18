#!/bin/sh -x

PROXY_CONF="/var/run/squid/proxies.conf"
SQUID_CONF="/etc/squid/squid.conf"
SQUID_PID_FILE="/var/run/squid/squid.pid"

# validate parameters
if [ -z "${USERNAME}" ]; then
  echo "You have to specify the -e USERNAME=... argument"
  exit
fi
if [ -z "${PASSWORD}" ]; then
  echo "You have to specify the -e PASSWORD=... argument"
  exit
fi

function download_proxy_list() {
    # download proxy list.
    rm ${PROXY_CONF}
    I=0
    for LINE in $(wget -q -O - "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt");
    do
        HOST=$(echo ${LINE} | cut -d ":" -f 1)
        PORT=$(echo ${LINE} | cut -d ":" -f 2)

        echo "cache_peer ${HOST} parent ${PORT} 0 no-digest no-netdb-exchange connect-fail-limit=2 connect-timeout=8 round-robin no-query allow-miss proxy-only name=public${I}" >> ${PROXY_CONF}
        I=$((I+1))
    done
}

# some setup
htpasswd -cb /etc/squid/passwd "${USERNAME}" "${PASSWORD}"
download_proxy_list
chown squid:squid /dev/stdout

# start squid
exec $(which squid) -NYCd 1 &

while [ true ]; do
    # refresh proxy list each day.
    sleep 1d
    PID=${!}

    SQUID_PID=$(cat ${SQUID_PID_FILE})

    # busy loop while squid and sleep execute.
    while [ kill -0 ${PID} && kill -0 ${SQUID_PID} ]; do
        sleep 1
    done

    # if squid exited, break.
    if [ ! kill -0 ${SQUID_PID} ]; then
        break
    fi

    # otherwise, download proxy list and start over.
    download_proxy_list
    kill -HUP ${SQUID_PID}
done
