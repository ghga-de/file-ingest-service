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
#

"""Test actual API call and event publishing"""

import pytest

from tests.fixtures.joint import (  # noqa: F401
    JointFixture,
    KafkaFixture,
    joint_fixture,
    kafka_fixture,
)


@pytest.mark.asyncio
async def test_api_call(monkeypatch, joint_fixture: JointFixture):  # noqa: F811
    """Test functionality with incoming API call"""

    # test happy path
    headers = {"Authorization": f"Bearer {joint_fixture.token}"}

    # patch vault call with mock
    with monkeypatch.context() as patch:
        patch.setattr(
            "fis.adapters.outbound.vault.client.VaultAdapter.store_secret",
            lambda self, secret: "very_secret_id",
        )
        response = await joint_fixture.rest_client.post(
            "/ingest", json=joint_fixture.encrypted_payload.dict(), headers=headers
        )

    assert response.status_code == 202

    # test missing authorization
    response = await joint_fixture.rest_client.post(
        "/ingest", json=joint_fixture.encrypted_payload.dict()
    )
    assert response.status_code == 403

    # test malformed payload
    nonsense_payload = joint_fixture.encrypted_payload.copy(
        update={"payload": "abcdefghijklmn"}
    )
    response = await joint_fixture.rest_client.post(
        "/ingest", json=nonsense_payload.dict(), headers=headers
    )
    assert response.status_code == 422
