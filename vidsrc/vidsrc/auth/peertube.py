from urllib.parse import urljoin

import requests


class PeerTubeAuth:
    def __init__(self, url):
        self.url = url

    def login(self, credentials):
        r = requests.get(urljoin(self.url, '/oauth-clients/local/'))
        params = r.json()
        r = requests.post(urljoin(self.url, '/users/token/'), data={
            'client_id': params['client_id'],
            'client_secret': params['client_secret'],
            'grant_type': 'password',
            'username': credentials['username'],
            'password': credentials['password'],
        })
        token = r.json()
        return {
            'headers': {
                'Authorization': f"Bearer {token['access_token']}"
            }
        }
