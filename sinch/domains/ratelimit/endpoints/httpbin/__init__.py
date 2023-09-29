from typing import Any

from sinch.core.endpoint import HTTPEndpoint
from sinch.core.enums import HTTPMethods, HTTPAuthentication
from sinch.core.models.base_model import SinchRequestBaseModel
from sinch.core.models.http_response import HTTPResponse


class GetHttpbinEndpoint(HTTPEndpoint):
    ENDPOINT_URL = "{origin}/anything/123/"
    HTTP_METHOD = HTTPMethods.GET.value
    HTTP_AUTHENTICATION = HTTPAuthentication.OAUTH.value

    def __init__(self, project_id: str, request_data: SinchRequestBaseModel):
        self.project_id = project_id
        self.request_data = request_data

    def build_url(self, sinch):
        return self.ENDPOINT_URL.format(origin="httpbin.eu1tst.api-services-test.int.staging.sinch.com")

    def handle_response(self, response: HTTPResponse) -> Any:
        return response.headers
