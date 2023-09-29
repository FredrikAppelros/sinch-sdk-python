import json
import sys
import time

import aiohttp
from abc import ABC

from token_bucket import Limiter, MemoryStorage

from sinch.core.endpoint import HTTPEndpoint
from sinch.core.models.http_request import HttpRequest
from sinch.core.models.http_response import HTTPResponse
from sinch.core.enums import HTTPAuthentication
from sinch.core.token_manager import TokenState


class HTTPTransport(ABC):
    def __init__(self, sinch):
        self.sinch = sinch
        self.limiter = Limiter(sys.maxsize, sys.maxsize, MemoryStorage())

    def request(self, endpoint: HTTPEndpoint) -> HTTPResponse:
        pass

    def authenticate(self, endpoint, request_data):
        if endpoint.HTTP_AUTHENTICATION == HTTPAuthentication.BASIC.value:
            request_data.auth = (self.sinch.configuration.key_id, self.sinch.configuration.key_secret)
        else:
            request_data.auth = None

        if endpoint.HTTP_AUTHENTICATION == HTTPAuthentication.OAUTH.value:
            token = self.sinch.authentication.get_auth_token().access_token
            request_data.headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

        return request_data

    def prepare_request(self, endpoint: HTTPEndpoint) -> HttpRequest:
        protocol = "http://" if self.sinch.configuration.disable_https else "https://"
        url_query_params = endpoint.build_query_params()

        return HttpRequest(
            headers={},
            protocol=protocol,
            url=protocol + endpoint.build_url(self.sinch),
            http_method=endpoint.HTTP_METHOD,
            request_body=endpoint.request_body(),
            query_params=url_query_params,
            auth=()
        )

    def handle_response(self, endpoint: HTTPEndpoint, http_response: HTTPResponse):
        self.sinch.configuration.logger.info(
            f"HTTP {http_response.status_code}\n{http_response.headers}"
        )
        if http_response.status_code == 401:
            self.sinch.configuration.token_manager.handle_invalid_token(http_response)
            if self.sinch.configuration.token_manager.token_state == TokenState.EXPIRED:
                return self.request(endpoint=endpoint)
        if http_response.status_code == 429:
            retry_after = int(http_response.headers['Retry-After'])
            if retry_after > 0:
                self.sinch.configuration.logger.info(f"Sleeping for {retry_after} seconds")
                time.sleep(retry_after + 1)
            return self.request(endpoint=endpoint)
        else:
            if 'ratelimit' in http_response.headers:
                rl_header = http_response.headers['ratelimit']
                self.sinch.configuration.logger.info(f"Ratelimit header: {rl_header}")
                rl_keywords = dict([t.split('=') for t in rl_header.split(', ')])
                self.limiter._rate = int(rl_keywords['limit']) / int(rl_keywords['reset'])
                self.limiter._capacity = int(rl_keywords['limit'])
            else:
                self.limiter._rate = sys.maxsize
                self.limiter._capacity = sys.maxsize

        return endpoint.handle_response(http_response)


class AsyncHTTPTransport(HTTPTransport):
    async def authenticate(self, endpoint, request_data):
        if endpoint.HTTP_AUTHENTICATION == HTTPAuthentication.BASIC.value:
            request_data.auth = aiohttp.BasicAuth(self.sinch.configuration.key_id, self.sinch.configuration.key_secret)
        else:
            request_data.auth = None

        if endpoint.HTTP_AUTHENTICATION == HTTPAuthentication.OAUTH.value:
            token_response = await self.sinch.authentication.get_auth_token()
            request_data.headers = {
                "Authorization": f"Bearer {token_response.access_token}",
                "Content-Type": "application/json"
            }

        return request_data

    async def handle_response(self, endpoint: HTTPEndpoint, http_response: HTTPResponse):
        if http_response.status_code == 401:
            self.sinch.configuration.token_manager.handle_invalid_token(http_response)
            if self.sinch.configuration.token_manager.token_state == TokenState.EXPIRED:
                return await self.request(endpoint=endpoint)

        return endpoint.handle_response(http_response)
