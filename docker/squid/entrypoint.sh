#!/bin/sh -x

PROXY_CONF="/var/run/squid/proxies.conf"
SQUID_CONF="/etc/squid/squid.conf"

if [ -z "${USERNAME}" ]; then
  echo "You have to specify the -e USERNAME=... argument"
  exit
fi
if [ -z "${PASSWORD}" ]; then
  echo "You have to specify the -e PASSWORD=... argument"
  exit
fi

htpasswd -cb /etc/squid/passwd "${USERNAME}" "${PASSWORD}"

# Download proxy list.
rm ${PROXY_CONF}
I=0
for LINE in $(wget -q -O - "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt");
do
    HOST=$(echo ${LINE} | cut -d ":" -f 1)
    PORT=$(echo ${LINE} | cut -d ":" -f 2)

    echo "cache_peer ${HOST} parent ${PORT} 0 no-digest no-netdb-exchange connect-fail-limit=2 connect-timeout=8 round-robin no-query allow-miss proxy-only name=public${I}" >> ${PROXY_CONF}
    I=$((I+1))
done

chown squid:squid /dev/stdout

exec $(which squid) -NYCd 1
