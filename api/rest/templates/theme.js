window.CesiumTheme = {
    "menu": [{% for item in options.menu %}"{{ item }}"{% if not forloop.last %},{% endif %}{% endfor %}],
    "auth_method": "{{ options.auth_method }}",
    "auth_required": {% if options.auth_required %}true{% else %}false{% endif %},
    "title": "{{ options.title }}",
    "name": "{{ site.name }}",
    "domain": "{{ site.domain }}",
    "default_lang": "{{ options.default_lang }}"
};

document.title = window.CesiumTheme.title;
