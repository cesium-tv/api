#!/bin/bash -x

CMD=${@:-api}

/wait-for ${DJANGO_DB_HOST}:${DJANGO_DB_PORT}
/wait-for ${DJANGO_REDIS_HOST}:${DJANGO_REDIS_PORT}

if [ "${CMD}" == "api" ]; then
    DJANGO_HOST=${DJANGO_HOST:-0.0.0.0}
    DJANGO_PORT=${DJANGO_PORT:-8000}

    if [ ! -z "${DJANGO_DEBUG}" ]; then
        ARGS="${ARGS} --py-autoreload=1"
    fi

    if [ ! -z "${UWSGI_STATIC}" ] && [ -z "${DJANGO_DEBUG}" ]; then
        ARGS="${ARGS} --static-map /=/app/static/"
    fi

    chown -R 65534:65534 ${DJANGO_MEDIA_ROOT:-/tmp}

    uwsgi --enable-threads --http-socket=${DJANGO_HOST}:${DJANGO_PORT} \
        --uid=65534 --gid=65534 --manage-script-name \
        --static-map /media=${DJANGO_MEDIA_ROOT:-/tmp} --static-gzip-all \
        --mount /=api.wsgi:application ${ARGS}

elif [ "${CMD}" == "migrate" ]; then
    su nobody -c 'python3 manage.py migrate --noinput'

elif [ "${CMD}" == "beat" ]; then
    su nobody -c 'celery -A api beat -l info'

elif [ "${CMD}" == "celery" ]; then
    python manage.py celery
    # su nobody -c 'celery -A api worker -l info'

elif [ "${CMD}" == "test" ]; then
    python3 manage.py test

else
    /bin/sh -c "${CMD}"

fi
