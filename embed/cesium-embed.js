var BASE_URL = 'http://localhost:8000/embed';
var el = document.getElementById('cesium-embed');

function objToCss(o) {
    var styles = [];

    for (var name in o) {
        if (o.hasOwnProperty(name)) {
            styles.push(name + ': ' + o[name]);
        }
    }

    return styles.join('; ');
}

if (el) {
    // retrieve settings from user.
    var hash = null;
    var width = el.getAttribute('width') || el.dataset.width || 400;
    var height = el.getAttribute('height') || el.dataset.height || 200;
    var bg = el.getAttribute('bg') || el.dataset.bg || 'white';
    var video = el.getAttribute('video') || el.dataset.video;

    // Build URL for embedding.
    var url = new URL(BASE_URL);
    url.searchParams.append('bg', bg);
    url.searchParams.append('video', video);

    // Create and iframe element.
    var iframe = document.createElement('iframe');
    iframe.setAttribute('src', url.toString());
    iframe.setAttribute('width', width);
    iframe.setAttribute('height', height);
    iframe.setAttribute('scrolling', 'no');
    iframe.setAttribute('style', objToCss({
        overflow: 'hidden',
        border: 'none'
    }));

    // Replace the div with our iframe.
    el.parentNode.replaceChild(iframe, el);
}