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
"""Ports for S3 upload metadata ingest"""

from abc import ABC, abstractmethod

from ghga_event_schemas.pydantic_ import FileUploadValidationSuccess

from fis.core import models


class UploadMetadataProcessorPort(ABC):
    """Port for"""

    class DecryptionError(RuntimeError):
        """Thrown when decryption with the provided private key failed"""

        def __init__(self):
            message = "Could not decrypt received payload with the given key."
            super().__init__(message)

    class WrongDecryptedFormatError(RuntimeError):
        """Thrown when the decrypted payload"""

        def __init__(self, *, cause: str):
            message = f"Decrypted payload does not conform to expected format: {cause}."
            super().__init__(message)

    @abstractmethod
    async def decrypt_payload(
        self, *, encrypted: models.FileUploadMetadataEncrypted
    ) -> models.FileUploadMetadata:
        """Decrypt upload metadata using private key"""

    @abstractmethod
    async def populate_by_event(self, *, event: FileUploadValidationSuccess):
        """Send FileUploadValidationSuccess event to be processed by downstream services"""

    @abstractmethod
    async def store_secret(self, *, file_secret: str) -> str:
        """Communicate with HashiCorp Vault to store file secret and get secret ID"""
