import json
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from .models import ShortenedURL, Click


class UrlShortenerTests(TestCase):

    def test_create_url_success(self):
        response = self.client.post(
            '/api/urls/',
            data=json.dumps({'url': 'https://example.com/some/long/path'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(len(body['code']), 7)
        self.assertEqual(body['url'], 'https://example.com/some/long/path')
        self.assertTrue(ShortenedURL.objects.filter(code=body['code']).exists())

    def test_create_invalid_url_returns_400(self):
        response = self.client.post(
            '/api/urls/',
            data=json.dumps({'url': 'not-a-url'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_unknown_code_returns_404(self):
        response = self.client.get('/doesnotexist/')
        self.assertEqual(response.status_code, 404)

    def test_expired_link_returns_410(self):
        ShortenedURL.objects.create(
            code='old1234',
            url='https://example.com',
            expiration_date=timezone.now() - timedelta(days=1),
        )
        response = self.client.get('/old1234/')
        self.assertEqual(response.status_code, 410)

    def test_redirect_records_click(self):
        ShortenedURL.objects.create(code='abc1234', url='https://example.com')
        response = self.client.get('/abc1234/', HTTP_USER_AGENT='TestAgent')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'https://example.com')
        self.assertEqual(Click.objects.count(), 1)
        self.assertEqual(Click.objects.first().client_info, 'TestAgent')