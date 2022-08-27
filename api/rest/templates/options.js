var options = {
    "menu": [
        {{ options.menu | safe }}
    ],
    "auth": "{{ options.auth }}",
    "title": "{{ options.title }}",
    "name": "{{ site.name }}",
    "domain": "{{ site.domain }}",
    "default_lang": "{{ options.default_lang }}",
};
