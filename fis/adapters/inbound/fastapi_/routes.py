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
"""TODO"""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from fis.adapters.inbound.fastapi_.http_authorization import (
    IngestTokenAuthContext,
    require_token,
)

router = APIRouter()


@router.post(
    "/ingest",
    summary="Processes encrypted output data from the S3 upload script and ingests it "
    + "into the Encryption Key Store, Internal File Registry and Download Controller.",
    operation_id="ingestFileUploadMetadata",
    tags=["FileIngestService"],
    status_code=status.HTTP_202_ACCEPTED,
    response_model=None,
    response_description="Received and decrypted data successfully.",
    responses={
        status.HTTP_403_FORBIDDEN: {"": None},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"": None},
    },
)
@inject
async def ingest_file_upload_metadata(token: IngestTokenAuthContext = require_token):
    ...
