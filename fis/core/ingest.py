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
"""Functionality relating to S3 upload metadata processing"""

import json

from ghga_service_commons.utils.crypt import decrypt
from nacl.exceptions import CryptoError
from pydantic import BaseSettings, Field, ValidationError

from fis.core import models
from fis.ports.inbound.ingest import UploadMetadataProcessorPort
from fis.ports.outbound.event_pub import EventPublisherPort
from fis.ports.outbound.vault.client import VaultAdapterPort


class ServiceConfig(BaseSettings):
    """Specific configs for authentication and encryption"""

    private_key: str = Field(
        ...,
        description="Base64 encoded private key of the keypair whose public key is used "
        + "to encrypt the payload.",
    )
    source_bucket_id: str = Field(
        ...,
        description="ID of the bucket the object(s) corresponding to the upload metadata "
        + "have been uploaded to. This should currently point to the staging bucket.",
    )
    token_hashes: list[str] = Field(
        ...,
        description="List of token hashes corresponding to the tokens that can be used "
        + "to authenticate calls to this service.",
    )


class UploadMetadataProcessor(UploadMetadataProcessorPort):
    """Handler for S3 upload metadata processing"""

    def __init__(
        self,
        *,
        config: ServiceConfig,
        event_publisher: EventPublisherPort,
        vault_adapter: VaultAdapterPort
    ):
        self._config = config
        self._event_publisher = event_publisher
        self._vault_adapter = vault_adapter

    async def decrypt_payload(
        self, *, encrypted: models.FileUploadMetadataEncrypted
    ) -> models.FileUploadMetadata:
        """Decrypt upload metadata using private key"""
        try:
            decrypted = decrypt(data=encrypted.payload, key=self._config.private_key)
        except (ValueError, CryptoError) as error:
            raise self.DecryptionError() from error

        upload_metadata = json.loads(decrypted)

        try:
            return models.FileUploadMetadata(**upload_metadata)
        except ValidationError as error:
            raise self.WrongDecryptedFormatError(cause=str(error)) from error

    async def populate_by_event(
        self, *, upload_metadata: models.FileUploadMetadata, secret_id: str
    ):
        """Send FileUploadValidationSuccess event to be processed by downstream services"""
        await self._event_publisher.send_file_metadata(
            secret_id=secret_id,
            source_bucket_id=self._config.source_bucket_id,
            upload_metadata=upload_metadata,
        )

    async def store_secret(self, *, file_secret: str) -> str:
        """Communicate with HashiCorp Vault to store file secret and get secret ID"""
        try:
            return self._vault_adapter.store_secret(secret=file_secret)
        except self._vault_adapter.SecretInsertionError as error:
            raise self.VaultCommunicationError(message=str(error)) from error
