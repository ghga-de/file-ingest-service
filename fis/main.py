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
"""REST API configuration and function for CLI"""

from fastapi import FastAPI
from ghga_service_commons.api import configure_app, run_server

from fis.adapters.inbound.fastapi_.custom_openapi import get_openapi_schema
from fis.adapters.inbound.fastapi_.routes import router
from fis.config import Config
from fis.container import Container


def get_configured_container(*, config: Config) -> Container:
    """Create and configure a DI container."""

    container = Container()
    container.config.load_config(config)

    return container


def get_rest_api(*, config: Config) -> FastAPI:
    """
    Creates a FastAPI app.
    For full functionality of the api, run in the context of an CI container with
    correct wireing and initialized resources (see the run_api function below).
    """

    api = FastAPI()
    api.include_router(router)
    configure_app(api, config=config)

    def custom_openapi():
        if api.openapi_schema:
            return api.openapi_schema
        openapi_schema = get_openapi_schema(api)
        api.openapi_schema = openapi_schema
        return api.openapi_schema

    api.openapi = custom_openapi  # type: ignore [assignment]

    return api


async def run_rest():
    """Run the HTTP REST API."""

    config = Config()

    async with get_configured_container(config=config) as container:
        container.wire(
            modules=[
                "fis.adapters.inbound.fastapi_.http_authorization",
                "fis.adapters.inbound.fastapi_.routes",
            ]
        )
        api = get_rest_api(config=config)
        await run_server(app=api, config=config)
