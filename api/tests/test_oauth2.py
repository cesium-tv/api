from urllib.parse import urlencode, urlparse, parse_qs

from django.test import TestCase, Client
from django.urls import reverse


class OAuth2TestCase(TestCase):
    fixtures = [
        'user',
        'oauth2client',
    ]

    def setUp(self):
        self.client = Client()

    def test_password_grant(self):
        r = self.client.post(reverse('oauth_token_view'), {
            'client_id': '19bbc55f-0f6f-4fca-95bc-f86286db43da',
            'client_secret': '50ec237f-20b0-4a47-8a25-b329f6d53beb',
            'grant_type': 'password',
            'username': 'test',
            'password': 'password',
        })
        self.assertEqual(200, r.status_code)
        self.assertIn('access_token', r.json())

    def test_device_code_grant(self):
        # 1. Get device_code and user_code and verify url.
        r = self.client.post(reverse('oauth_device_code_view'), {
            'client_id': '19bbc55f-0f6f-4fca-95bc-f86286db43da',
            'client_secret': '50ec237f-20b0-4a47-8a25-b329f6d53beb',
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
        })
        self.assertEqual(200, r.status_code)
        device_code = r.json()['device_code']
        user_code = r.json()['user_code']
        verify_uri = r.json()['verification_uri']
        # 2. Poll for our token (should fail)
        r = self.client.post(reverse('oauth_token_view'), {
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
            'client_id': '19bbc55f-0f6f-4fca-95bc-f86286db43da',
            'client_secret': '50ec237f-20b0-4a47-8a25-b329f6d53beb',
            'device_code': device_code,
        })
        self.assertEqual(400, r.status_code)
        # 3. User verifies using user_code:
        # NOTE: we use a second Django test client here (authenticated)...
        userClient = Client()
        userClient.login(username='test', password='password')
        r = userClient.post(verify_uri, {
            'confirm': 'true',
            'user_code': user_code,
        })
        self.assertEqual(201, r.status_code)
        # 4. Now polling should yield a token.
        r = self.client.post(reverse('oauth_token_view'), {
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
            'client_id': '19bbc55f-0f6f-4fca-95bc-f86286db43da',
            'client_secret': '50ec237f-20b0-4a47-8a25-b329f6d53beb',
            'device_code': device_code,
        })
        self.assertEqual(200, r.status_code)
        self.assertIn('access_token', r.json())

    def test_auth_code_grant(self):
        # 1. User authorizes our app and is redirected back to our app.
        userClient = Client()
        userClient.login(username='test', password='password')
        qs = {
            'client_id': '19bbc55f-0f6f-4fca-95bc-f86286db43da',
            'response_type': 'code',
            'redirect_uri': 'http://localhost:8080/api/oauth/shanty/authorize/',
            'state': 'foobar',
            'nonce': 'foobar',
        }
        url = reverse('oauth_auth_code_view') + '?' + urlencode(qs)
        r = userClient.post(url, {
            'confirm': 'true',
        })
        self.assertEqual(302, r.status_code)
        # Extract data from redirect uri.
        data = parse_qs(urlparse(r.headers['Location']).query)
        # 2. Retrieve token from token endpoint.
        r = self.client.post(reverse('oauth_token_view'), {
            'client_id': '19bbc55f-0f6f-4fca-95bc-f86286db43da',
            'client_secret': '50ec237f-20b0-4a47-8a25-b329f6d53beb',
            'grant_type': 'authorization_code',
            'code': data['code'][0],
            'redirect_uri': 'http://localhost:8080/api/oauth/shanty/authorize/',
        })
        self.assertEqual(200, r.status_code)
        self.assertIn('access_token', r.json())
