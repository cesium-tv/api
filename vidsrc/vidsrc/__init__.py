import re

from vidsrc.backends import timcast


BACKENDS = {
    re.compile(r'^https://timcast.com/'): timcast,
}


def download(name, url, options):
    for pattern, backend in BACKENDS.items():
        if pattern.match(url):
            return backend.download(name, url, options)
    raise Exception(f'No backend for {url}')
