var options = {
    "menu": [
        {{ options.menu | safe }}
    ],
    "title": "{{ options.title }}",
    "name": "{{ site.name }}",
    "domain": "{{ site.domain }}",
    "default_lang": "{{ options.default_lang }}",
};
