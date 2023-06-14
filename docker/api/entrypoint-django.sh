#!/bin/bash -x

CMD=${@:-api}
DJANGO_MEDIA_ROOT=${DJANGO_MEDIA_ROOT:-/tmp}
DJANGO_LOG_LEVEL=${DJANGO_LOG_LEVEL:-error}

/wait-for ${DJANGO_DB_HOST}:${DJANGO_DB_PORT}
/wait-for ${DJANGO_REDIS_HOST}:${DJANGO_REDIS_PORT}

if [ "${CMD}" == "api" ]; then
    DJANGO_HOST=${DJANGO_HOST:-0.0.0.0}
    DJANGO_PORT=${DJANGO_PORT:-8000}

    if [ ! -z "${DJANGO_DEBUG}" ]; then
        ARGS="${ARGS} --py-autoreload=1"
    fi

    chown -R 65534:65534 ${DJANGO_MEDIA_ROOT}

    uwsgi --enable-threads --http-socket=${DJANGO_HOST}:${DJANGO_PORT} \
        --uid=65534 --gid=65534 --manage-script-name \
        --static-map /=/static --static-gzip-all --static-index=index.html \
        --mount /=api.wsgi:application ${ARGS}

elif [ "${CMD}" == "migrate" ]; then
    python3 manage.py migrate --noinput

elif [ "${CMD}" == "beat" ]; then
    if [ ! -z "${CELERY_UID}" ]; then
        ARGS=" --uid=${CELERY_UID}"
    fi

    if [ ! -z "${CELERY_GID}" ]; then
        ARGS="${ARGS} --gid=${CELERY_GID}"
    fi

    celery -A api beat -l ${DJANGO_LOG_LEVEL}${ARGS}

elif [ "${CMD}" == "celery" ]; then
    if [ ! -z "${CELERY_UID}" ]; then
        ARGS=" --uid=${CELERY_UID}"
    fi

    if [ ! -z "${CELERY_GID}" ]; then
        ARGS="${ARGS} --gid=${CELERY_GID}"
    fi

    python manage.py celery -l ${DJANGO_LOG_LEVEL}${ARGS}

elif [ "${CMD}" == "test" ]; then
    python3 manage.py test

else
    /bin/sh -c "${CMD}"

fi
