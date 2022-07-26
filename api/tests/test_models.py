from django.test import TestCase

from rest.models import Platform, Channel, Video


JSON = {
'a': {'a': '.lf6yv.lf6yv.1ajr41..ku.9i7o60',
    'aden': [1, 0, 1],
    'ads': [],
    'ae': '.lf6yv.lf6yv.1ajr41..ku.ax48c0',
    'ap': [False, 0],
    'loop': [],
    'ov': 1,
    'timeout': -1,
    'u': 'lf6yv'},
'author': {'name': 'ATimcastIRL', 'url': 'https://rumble.com/c/ATimcastIRL'},
'autoplay': 1,
'cc': [],
'duration': 2217,
'evt': {'e': '/l/pte...1ajr41.1sd4vld',
        't': '/l/timeline...1ajr41.1pl.1j5w598',
        'v': '/l/view...1ajr41.109ldmb',
        'wt': 0},
'fps': 30,
'h': 1080,
'i': 'https://sp.rmbl.ws/s8/6/9/D/a/7/9Da7e.OvCc.jpg',
'l': '/v1d5x19-mtg-member-podcast-2022-show.html',
'live': 0,
'loaded': 1,
'mod': [],
'own': True,
'player': {'colors': {'background': '#4CC0E0',
                    'hover': '#FFFFFF',
                    'hoverBackground': '#303030',
                    'play': '#FFFFFF',
                    'scrubber': '#4CC0E0'},
            'logo': {'allow': True,
                    'h': '58',
                    'link': '//rumble.com/c/ATimcastIRL',
                    'th': 22,
                    'tw': 75,
                    'w': '200'},
            'timestamp': 1620930686},
'pubDate': '2022-07-22T02:45:35+00:00',
'r': 1,
'restrict': [-3, 0],
'timeline': [0, 0],
'title': 'mtg member podcast 2022 show',
'track': 1,
'u': {'mp4': {'meta': {'bitrate': 815, 'h': 480, 'size': 225913415, 'w': 854},
            'url': 'https://sp.rmbl.ws/s8/2/9/D/a/7/9Da7e.caa.mp4'},
    'webm': {'meta': {'bitrate': 812,
                        'h': 480,
                        'size': 225289219,
                        'w': 854},
                'url': 'https://sp.rmbl.ws/s8/2/9/D/a/7/9Da7e.daa.webm'}},
'ua': {'mp4': {'1080': {'meta': {'bitrate': 2688,
                                'h': 1080,
                                'size': 745193382,
                                'w': 1920},
                        'url': 'https://sp.rmbl.ws/s8/2/9/D/a/7/9Da7e.haa.mp4'},
                '240': {'meta': {'bitrate': 203,
                                'h': 360,
                                'size': 56439397,
                                'w': 640},
                        'url': 'https://sp.rmbl.ws/s8/2/9/D/a/7/9Da7e.oaa.mp4'},
                '360': {'meta': {'bitrate': 635,
                                'h': 360,
                                'size': 176094971,
                                'w': 640},
                        'url': 'https://sp.rmbl.ws/s8/2/9/D/a/7/9Da7e.baa.mp4'},
                '480': {'meta': {'bitrate': 815,
                                'h': 480,
                                'size': 225913415,
                                'w': 854},
                        'url': 'https://sp.rmbl.ws/s8/2/9/D/a/7/9Da7e.caa.mp4'},
                '720': {'meta': {'bitrate': 1968,
                                'h': 720,
                                'size': 545501875,
                                'w': 1280},
                        'url': 'https://sp.rmbl.ws/s8/2/9/D/a/7/9Da7e.gaa.mp4'}},
        'webm': {'480': {'meta': {'bitrate': 812,
                                'h': 480,
                                'size': 225289219,
                                'w': 854},
                        'url': 'https://sp.rmbl.ws/s8/2/9/D/a/7/9Da7e.daa.webm'}}},
'vid': 78183937,
'w': 1920}


class TestModels(TestCase):
    def setUp(self):
        self.channel = Channel.objects.get(pk=1)
