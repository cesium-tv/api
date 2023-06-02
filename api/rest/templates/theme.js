window.CesiumTheme = {
    "menu": [{% for item in menu_items %}
        {
            "name": "{{ item.name }}",
            "title": {% if item.title is None %}null{% else %}"{{ item.title }}"{% endif %},
        },{% endfor %}
    ],
    "default_menu_item": "{{ options.default_menu_item }}",
    "auth_method": "{{ options.auth_method }}",
    "auth_required": {% if options.auth_required %}true{% else %}false{% endif %},
    "title": "{{ options.title }}",
    "name": "{{ site.name }}",
    "domain": "{{ site.domain }}",
    "default_lang": "{{ options.default_lang }}",
    "logo": "{{ brand.logo.url }}",
};

document.title = window.CesiumTheme.title;
