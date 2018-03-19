from pprint import pprint
from urllib.parse import urljoin

from django.conf import settings
from django.test import TestCase, override_settings

import requests_mock
from freezegun import freeze_time


from .bokun import _make_headers, get, post, paginated_post


@freeze_time('2018-01-01 13:37:00')
@override_settings(BOKUN_API_URL='https://api.bokun.is',
                   BOKUN_ACCESS_KEY='test_access_key',
                   BOKUN_SECRET_KEY='test_sected_key')
@requests_mock.Mocker()
class BokunTestCase(TestCase):
    """Tests for the Bokun API client
    """
    def test_make_headers(self, *args):
        """Test bokun._make_headers()
        """
        self.assertDictEqual(_make_headers('GET', 'test_path?foo=bar'), {
            'X-Bokun-AccessKey': 'test_access_key',
            'X-Bokun-Date': '2018-01-01 13:37:00',
            'X-Bokun-Signature': 'idF8tfaWGZb19rqag4B6f1GAmaM=',
        })

        self.assertDictEqual(_make_headers('POST', 'test_path?foo=bar'), {
            'X-Bokun-AccessKey': 'test_access_key',
            'X-Bokun-Date': '2018-01-01 13:37:00',
            'X-Bokun-Signature': 'Ha3kur2txHlTXqUEoVxo9rwh5LE='
        })

    def test_get(self, req_mock):
        """Test bokun.get()
        """
        req_mock.register_uri('GET',
                              urljoin(settings.BOKUN_API_URL, 'test_path/get'),
                              text='resp')

        res = get('test_path/get')

        self.assertEqual(200, res.status_code)
        self.assertEqual('resp', res.text)
        self.assertEqual('https://api.bokun.is/test_path/get', res.url)
        self.assertDictContainsSubset({
            'X-Bokun-Date': '2018-01-01 13:37:00',
            'X-Bokun-AccessKey': 'test_access_key',
            'X-Bokun-Signature': 'y9TUjSeKo7UsP1G4EwDrTq76dm8=',
        }, res.request.headers)

        res2 = get('test_path/get', {'foo': 'bar'})

        self.assertEqual(200, res2.status_code)
        self.assertEqual('resp', res2.text)
        self.assertEqual('https://api.bokun.is/test_path/get?foo=bar', res2.url)
        self.assertDictContainsSubset({
            'X-Bokun-Date': '2018-01-01 13:37:00',
            'X-Bokun-AccessKey': 'test_access_key',
            'X-Bokun-Signature': 'jEvWz30QrC7VP7MzQXBW795cjH8=',
        }, res2.request.headers)

    def test_post(self, req_mock):
        """Test bokun.post()
        """
        req_mock.register_uri('POST',
                              urljoin(settings.BOKUN_API_URL, 'test_path/post'),
                              text='resp')

        test_body = {
            'payload': 'test'
        }

        res = post('test_path/post', body=test_body)

        self.assertEqual(200, res.status_code)
        self.assertEqual('resp', res.text)
        self.assertEqual('https://api.bokun.is/test_path/post', res.url)
        self.assertDictEqual(res.request.json(), test_body)
        self.assertDictContainsSubset({
            'X-Bokun-Date': '2018-01-01 13:37:00',
            'X-Bokun-AccessKey': 'test_access_key',
            'X-Bokun-Signature': '2UyfPd/zmSDrclTt3n6hCuyUxlk=',
            'Content-Type': 'application/json',
        }, res.request.headers)

        res2 = post('test_path/post', body=test_body, query={'foo': 'bar'})

        self.assertEqual(200, res2.status_code)
        self.assertEqual('resp', res2.text)
        self.assertEqual(
            'https://api.bokun.is/test_path/post?foo=bar', res2.url)
        self.assertDictContainsSubset({
            'X-Bokun-Date': '2018-01-01 13:37:00',
            'X-Bokun-AccessKey': 'test_access_key',
            'X-Bokun-Signature': 'BgAXQgBxqDYwZM0haGwKWbiQKJE=',
            'Content-Type': 'application/json',
        }, res2.request.headers)

        res3 = post('test_path/post', query={'foo': 'bar'})

        self.assertEqual(200, res2.status_code)
        self.assertEqual('resp', res2.text)
        self.assertEqual(
            'https://api.bokun.is/test_path/post?foo=bar', res2.url)
        self.assertDictContainsSubset({
            'X-Bokun-Date': '2018-01-01 13:37:00',
            'X-Bokun-AccessKey': 'test_access_key',
            'X-Bokun-Signature': 'BgAXQgBxqDYwZM0haGwKWbiQKJE=',
            'Content-Type': 'application/json',
        }, res2.request.headers)

    def test_paginated_post(self, req_mock):
        """Test bokun.paginated_post()"""

        def mock_page(length):
            """Create a mock page response"""
            return {
                'status_code': 200,
                'json': {
                    'items': [{'id': id} for id in range(length)],
                }
            }

        req_mock.register_uri(
            'POST',
            urljoin(settings.BOKUN_API_URL, 'test_path/paginated_post'),
            [
                mock_page(100),
                mock_page(100),
                mock_page(99),
                mock_page(100),  # <- This will never be reached
            ]
        )

        #  ====== First page ======
        gen = paginated_post('test_path/paginated_post', body={
            'should_not_change': 'test'
        }, query={
            'query': 1
        })

        req_body, res = next(gen)

        self.assertEqual(100, len(res.json()['items']))
        self.assertDictEqual({
            'should_not_change': 'test',
            'pageSize': 100,
            'page': 1,
        }, req_body)

        #  ====== Second page  ======
        req_body, res = next(gen)

        self.assertEqual(100, len(res.json()['items']))
        self.assertDictEqual({
            'should_not_change': 'test',
            'pageSize': 100,
            'page': 2,
        }, req_body)

        #  ====== Third reich ======
        req_body, res = next(gen)

        self.assertEqual(99, len(res.json()['items']))
        self.assertDictEqual({
            'should_not_change': 'test',
            'pageSize': 100,
            'page': 3,
        }, req_body)

        try:
            next(gen)
        except StopIteration:
            pass
        else:
            self.fail('HALT! There should only be 3 pages!')
