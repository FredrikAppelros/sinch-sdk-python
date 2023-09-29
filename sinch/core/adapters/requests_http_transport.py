import time

import requests
import json
from sinch.core.ports.http_transport import HTTPTransport, HttpRequest
from sinch.core.endpoint import HTTPEndpoint
from sinch.core.models.http_response import HTTPResponse


class HTTPTransportRequests(HTTPTransport):
    def __init__(self, sinch):
        super().__init__(sinch)
        self.session = requests.Session()

    def request(self, endpoint: HTTPEndpoint) -> HTTPResponse:
        request_data: HttpRequest = self.prepare_request(endpoint)
        request_data: HttpRequest = self.authenticate(endpoint, request_data)

        self.sinch.configuration.logger.debug(
            f"Sync HTTP {request_data.http_method} call with headers:"
            f" {request_data.headers} and body: {request_data.request_body} to URL: {request_data.url}"
        )

        ready = self.limiter.consume(request_data.url, 1)
        while not ready:
            sleep_time = 1 / self.limiter._rate
            self.sinch.configuration.logger.info(f"Sleeping for {sleep_time} seconds")
            time.sleep(sleep_time)
            ready = self.limiter.consume(request_data.url, 1)
        response = self.session.request(
            method=request_data.http_method,
            url=request_data.url,
            data=request_data.request_body,
            auth=request_data.auth,
            headers=request_data.headers,
            timeout=self.sinch.configuration.connection_timeout,
            params=request_data.query_params
        )

        response_body = response.content
        if response_body:
            response_body = json.loads(response_body)

        self.sinch.configuration.logger.debug(
            f"Sync HTTP {response.status_code} response with headers: {response.headers}"
            f"and body: {response_body} from URL: {request_data.url}"
        )

        return self.handle_response(
            endpoint=endpoint,
            http_response=HTTPResponse(
                status_code=response.status_code,
                body=response_body,
                headers=response.headers
            )
        )
