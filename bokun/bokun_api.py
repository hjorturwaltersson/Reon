import datetime
import hashlib
import hmac
import base64
import uuid
import json
from copy import deepcopy
from urllib.parse import urljoin, urlencode

import requests

from django.conf import settings


class BokunApiException(Exception):
    def __init__(self,
                 request_method,
                 request_url,
                 request_query,
                 request_headers,
                 request_body,
                 response_data):
        self.request_url = request_url
        self.request_query = request_query
        self.request_headers = request_headers
        self.request_body = request_body

        self.message = response_data['message']
        self.fields = response_data['fields']

        super().__init__(self.message)

    def __str__(self):
        return json.dumps({
            "url": self.request_url,
            "query": self.request_query,
            "headers": self.request_headers,
            "body": self.request_body,
            "message": self.message,
            "fields": self.fields,
        }, indent=2)

class BokunApi:
    def __init__(self, url=None, access_key=None, secret_key=None):
        self.url = url or settings.BOKUN_API_URL
        self.access_key = access_key or settings.BOKUN_ACCESS_KEY
        self.secret_key = secret_key or settings.BOKUN_SECRET_KEY

    def _make_headers(self, method, path):
        """Make authentication headers for the Bokun API"""

        now_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        token = ''.join([now_date, self.access_key, method, path])
        digester = hmac.new(bytes(self.secret_key, 'ascii'),
                            bytes(token, 'ascii'), hashlib.sha1)
        signature = base64.standard_b64encode(digester.digest())

        return {
            'X-Bokun-Date': now_date,
            'X-Bokun-AccessKey': self.access_key,
            'X-Bokun-Signature': signature.decode('ascii')
        }

    def get(self, path, query=None):
        """Send a GET request to the Bokun API"""

        if query:
            path = '%s?%s' % (path, urlencode(query))

        url = urljoin(self.url, path)

        headers = self._make_headers('GET', path)

        res = requests.get(url, headers=headers)

        return self.handle_response('GET', url, query, headers, None, res)

    def post(self, path, body={}, query=None):
        """Send a POST request to the Bokun API"""

        if query:
            path = '%s?%s' % (path, urlencode(query))

        headers = self._make_headers('POST', path)
        headers.update({
            'Content-Type': 'application/json',
        })

        url = urljoin(self.url, path)

        res = requests.post(url, headers=headers, json=body or {})

        return self.handle_response('POST', url, query, headers, body, res)

    def handle_response(self, method, url, query, headers, body, response):
        data = response.json()

        if 'message' in data and 'fields' in data:
            raise BokunApiException(
                request_method=method,
                request_url=url,
                request_query=query,
                request_headers=headers,
                request_body=body,
                response_data=data,
            )

        return response

    def paginated_post(self, path, body={}, query=None, paginate_on='items'):
        """
        Send POST requests to the Bokun API per page

        Returns a generator

        On each iteration the generator will send a post request with
        page parameters added to the request body. For example:

        ```json
        {
            "pageSize": 100,  // Is always 100
            "page": 1,        // Will increment per page request
            ... other parameters ...
        }
        ```

        The generator will continue to send a request and return a value
        as long as the last page returned at least 100 results.

        NOTE: This means that if the total result count is a multiple of 100,
              the last request sent will yeild zero results.
              Currently there is no known way to avoid this when using
              the Bokun API
        """

        body = deepcopy(body)
        body['pageSize'] = 100

        page = 1
        done = False
        while not done:
            _body = {}
            _body.update(body)
            _body['page'] = page

            res = self.post(path, _body, query)

            if len(res.json()[paginate_on]) < 100:
                done = True
            else:
                page += 1

            yield _body, res
