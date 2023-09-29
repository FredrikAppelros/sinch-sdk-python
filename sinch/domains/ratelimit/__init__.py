from typing import Any

from sinch.core.models.base_model import SinchRequestBaseModel
from sinch.domains.ratelimit.endpoints.httpbin import GetHttpbinEndpoint


class RatelimitBase:
    def __init__(self, sinch):
        self._sinch = sinch


class Ratelimit(RatelimitBase):
    def __init__(self, sinch):
        super(Ratelimit, self).__init__(sinch)

    def httpbin(
            self,
    ) -> Any:
        return self._sinch.configuration.transport.request(
            GetHttpbinEndpoint(
                project_id=self._sinch.configuration.project_id,
                request_data=SinchRequestBaseModel()
            )
        )
