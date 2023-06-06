# Copyright 2021 - 2023 Universität Tübingen, DKFZ, EMBL, and Universität zu Köln
# for the German Human Genome-Phenome Archive (GHGA)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Authorization specific code for FastAPI"""

from dependency_injector.wiring import Provide
from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from ghga_service_commons.auth.context import AuthContextProtocol
from ghga_service_commons.auth.policies import require_auth_context_using_credentials
from ghga_service_commons.utils.simple_token import check_token
from pydantic import BaseModel, Field

from fis.config import ServiceConfig
from fis.container import Container

__all__ = ["require_token"]


class IngestTokenAuthContext(BaseModel):
    """Auth context holding the ingest token."""

    token: str = Field(
        ...,
        description="A simple alphanumeric token to authenticate the ingest of "
        + "file upload metadata.",
    )


class IngestTokenAuthProvider(AuthContextProtocol[IngestTokenAuthContext]):
    """Provider for the ingest token auth context"""

    def __init__(self, *, token_hashes: list[str]):
        self._token_hashes = token_hashes

    async def get_context(self, token: str) -> IngestTokenAuthContext:
        """Get ingest token auth context"""

        if not check_token(token=token, token_hashes=self._token_hashes):
            raise self.AuthContextValidationError("Invalid Token")

        return IngestTokenAuthContext(token=token)


async def require_token_context(
    service_config: ServiceConfig = Depends(Provide[Container.config]),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=True)),
) -> IngestTokenAuthContext:
    """Require a VIP authentication and authorization context using FastAPI."""
    return await require_auth_context_using_credentials(
        credentials=credentials,
        auth_provider=IngestTokenAuthProvider(token_hashes=service_config.token_hashes),
    )


require_token = Security(require_token_context)
