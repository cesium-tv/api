from django.test import TestCase

from rest.models import Brand


PRIMARY = '#deadbe'
WARNING = '#c0fee0'
SUCCESS = '#bedead'
LOGO = '4097d4f6-b4c3-4187-9451-86cc31df5c12.png'


class BrandTestCase(TestCase):
    def test_brand_compile(self):
        brand = Brand()
        css = brand.compile(minify=False)
        self.assertIn(PRIMARY, css)
        self.assertIn(WARNING, css)
        self.assertIn(SUCCESS, css)
        self.assertIn(LOGO, css)
