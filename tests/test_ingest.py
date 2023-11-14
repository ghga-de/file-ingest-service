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

"""Test ingest functions"""

import base64
import os

import pytest
from ghga_service_commons.utils.crypt import encrypt, generate_key_pair

from fis.core.models import EncryptedPayload, LegacyUploadMetadata, UploadMetadata
from tests.fixtures.joint import (  # noqa: F401
    JointFixture,
    KafkaFixture,
    joint_fixture,
    kafka_fixture,
)


@pytest.mark.asyncio
async def test_decryption_happy(joint_fixture: JointFixture):  # noqa: F811
    """Test decryption with valid keypair and correct file upload metadata format."""
    upload_metadata_processor = (
        await joint_fixture.container.upload_metadata_processor()
    )

    payload = UploadMetadata(
        **joint_fixture.payload.model_dump(),
        secret_id="test_secret_id",
    )

    encrypted_payload = EncryptedPayload(
        payload=encrypt(
            data=payload.model_dump_json(),
            key=joint_fixture.keypair.public,
        )
    )

    processed_payload = await upload_metadata_processor.decrypt_payload(
        encrypted=encrypted_payload
    )
    assert processed_payload == payload


@pytest.mark.asyncio
async def test_legacy_decryption_happy(joint_fixture: JointFixture):  # noqa: F811
    """Test decryption with valid keypair and correct file upload metadata format."""
    upload_metadata_processor = (
        await joint_fixture.container.legacy_upload_metadata_processor()
    )

    payload = LegacyUploadMetadata(
        **joint_fixture.payload.model_dump(),
        file_secret=base64.b64encode(os.urandom(32)).decode("utf-8"),
    )

    encrypted_payload = EncryptedPayload(
        payload=encrypt(
            data=payload.model_dump_json(),
            key=joint_fixture.keypair.public,
        )
    )

    processed_payload = await upload_metadata_processor.decrypt_payload(
        encrypted=encrypted_payload
    )
    assert processed_payload == payload


@pytest.mark.asyncio
async def test_decryption_sad(joint_fixture: JointFixture):  # noqa: F811
    """Test decryption throws correct errors for payload and key issues"""
    upload_metadata_processor = (
        await joint_fixture.container.legacy_upload_metadata_processor()
    )

    # test faulty payload
    encrypted_payload = EncryptedPayload(
        payload=encrypt(
            data=joint_fixture.payload.model_dump_json(),
            key=joint_fixture.keypair.public,
        )
    )

    with pytest.raises(upload_metadata_processor.WrongDecryptedFormatError):
        await upload_metadata_processor.decrypt_payload(encrypted=encrypted_payload)

    # test wrong key
    keypair2 = generate_key_pair()

    payload = UploadMetadata(
        **joint_fixture.payload.model_dump(),
        secret_id="test_secret_id",
    )

    encrypted_payload = EncryptedPayload(
        payload=encrypt(data=payload.model_dump_json(), key=keypair2.public)
    )

    with pytest.raises(upload_metadata_processor.DecryptionError):
        await upload_metadata_processor.decrypt_payload(encrypted=encrypted_payload)


@pytest.mark.asyncio
async def test_legacy_decryption_sad(joint_fixture: JointFixture):  # noqa: F811
    """Test decryption throws correct errors for payload and key issues"""
    upload_metadata_processor = (
        await joint_fixture.container.upload_metadata_processor()
    )

    # test faulty payload
    encrypted_payload = EncryptedPayload(
        payload=encrypt(
            data=joint_fixture.payload.model_dump_json(),
            key=joint_fixture.keypair.public,
        )
    )

    with pytest.raises(upload_metadata_processor.WrongDecryptedFormatError):
        await upload_metadata_processor.decrypt_payload(encrypted=encrypted_payload)

    # test wrong key
    keypair2 = generate_key_pair()

    payload = LegacyUploadMetadata(
        **joint_fixture.payload.model_dump(),
        file_secret=base64.b64encode(os.urandom(32)).decode("utf-8"),
    )

    encrypted_payload = EncryptedPayload(
        payload=encrypt(data=payload.model_dump_json(), key=keypair2.public)
    )

    with pytest.raises(upload_metadata_processor.DecryptionError):
        await upload_metadata_processor.decrypt_payload(encrypted=encrypted_payload)
