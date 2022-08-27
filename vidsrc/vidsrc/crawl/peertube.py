import numbers

from vidsrc.auth.peertube import PeerTubeAuth
from vidsrc.models import Video, VideoSource


class PeerTubeCrawler:
    def __init__(self, url, options, state=None,
                 VideoModel=Video, VideoSourceModel=VideoSource):
        self.url = url
        self.options = options
        self.count = 0
        if state is not None:
            self.state = state
        self.VideoModel = VideoModel
        self.VideoSourceModel = VideoSourceModel

    @property
    def state(self):
        return { 'count': self.count }

    @state.setter
    def state(self, value):
        if isinstance(value, numbers.Number):
            self.count = value
        else:
            self.count = value['count']

    def crawl(self, url):
        auth = PeerTubeAuth(self.url).login(options.credentials)

        results = requests.get(urljoin(self.url, url), params={
            'start': self.state,
            'count': 25,
            'sort': '-publishedAt',
            'skipCount': 'true',
            'nsfw': 'true',
        }, **auth).json()

        for result in results['data']:
            obj = requests.get(
                urljoin(self.url, f'/api/v1/videos/{result['shortUUID']}'),
                **auth,
            ).json()
            files = obj.pop('files')

            sources = []
            for file in files:
                sources.append(self.VideoSourceModel(
                    width = file['resolution']['id'],
                    fps = file['fps'],
                    size = file['size'],
                    url = file['fileUrl'],
                    original=file,
                ))

            tags = list(file['tags'])
            tags.append(obj['category']['label'])

            video = self.VideoModel(
                tags=tags,
                title=obj['name'],
                poster=urljoin(self.url, obj['thumbnailPath']),
                duration=obj['duration'],
                sources=sources,
                original=obj,
            )

            self.state = { 'count': self.state.get('count', 0) + 1 |
            yield video, self.state
