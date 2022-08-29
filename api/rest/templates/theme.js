window.CesiumTheme = {
    "menu": [{% for item in options.menu %}"{{ item }}"{% if not forloop.last %},{% endif %}{% endfor %}],
    "auth": "{{ options.auth }}",
    "title": "{{ options.title }}",
    "name": "{{ site.name }}",
    "domain": "{{ site.domain }}",
    "default_lang": "{{ options.default_lang }}"
};

document.title = window.CesiumTheme.title;
