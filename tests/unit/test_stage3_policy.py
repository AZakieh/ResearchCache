import httpx
import pytest
from sqlalchemy import delete, select

from researchcache.pipeline.stage3_policy import lookup_policy
from researchcache.store.db import PolicyORM, get_session_factory


@pytest.fixture(autouse=True)
async def clean_policies_table():
    session_factory = get_session_factory()
    async with session_factory() as session:
        await session.execute(delete(PolicyORM))
        await session.commit()
    yield
    async with session_factory() as session:
        await session.execute(delete(PolicyORM))
        await session.commit()


@pytest.fixture
async def db_session():
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


def _mock_zenodo_response(mocker, *, licence: str | None = "cc-by-4.0", status_code: int = 200):
    payload = {"metadata": {"license": {"id": licence}}} if licence else {"metadata": {}}
    response = httpx.Response(
        status_code, json=payload, request=httpx.Request("GET", "https://zenodo.org")
    )

    async def fake_get(self, url, *args, **kwargs):
        return response

    mocker.patch("httpx.AsyncClient.get", fake_get)


async def test_lookup_policy_fetches_zenodo_licence_and_persists(mocker, db_session):
    _mock_zenodo_response(mocker, licence="cc-by-4.0")

    policy = await lookup_policy(
        object_id="obj-1",
        origin_url="https://zenodo.org/records/12345/files/data.zip",
        session=db_session,
    )

    assert policy.licence == "cc-by-4.0"
    assert policy.access_tier == "open"

    row = (
        await db_session.execute(select(PolicyORM).where(PolicyORM.object_id == "obj-1"))
    ).scalar_one()
    assert row.licence == "cc-by-4.0"
    assert row.access_tier == "open"
    assert row.origin_url == "https://zenodo.org/records/12345/files/data.zip"


async def test_lookup_policy_defaults_to_unknown_when_no_fetcher_available(db_session):
    policy = await lookup_policy(
        object_id="obj-2",
        origin_url="https://ftp.ebi.ac.uk/pub/databases/some/file.gz",
        session=db_session,
    )

    assert policy.licence == "unknown"
    assert policy.access_tier == "open"

    row = (
        await db_session.execute(select(PolicyORM).where(PolicyORM.object_id == "obj-2"))
    ).scalar_one()
    assert row.licence == "unknown"
    assert row.access_tier == "open"


async def test_lookup_policy_defaults_to_unknown_on_zenodo_fetch_failure(mocker, db_session):
    async def raise_timeout(self, url, *args, **kwargs):
        raise httpx.ConnectTimeout("timed out", request=httpx.Request("GET", url))

    mocker.patch("httpx.AsyncClient.get", raise_timeout)

    policy = await lookup_policy(
        object_id="obj-3",
        origin_url="https://zenodo.org/records/12345/files/data.zip",
        session=db_session,
    )

    assert policy.licence == "unknown"


async def test_lookup_policy_upserts_rather_than_duplicates(db_session):
    await lookup_policy(object_id="obj-4", origin_url="https://ftp.ebi.ac.uk/a", session=db_session)
    await lookup_policy(object_id="obj-4", origin_url="https://ftp.ebi.ac.uk/b", session=db_session)

    rows = (
        (await db_session.execute(select(PolicyORM).where(PolicyORM.object_id == "obj-4")))
        .scalars()
        .all()
    )
    assert len(rows) == 1
    assert rows[0].origin_url == "https://ftp.ebi.ac.uk/b"


async def test_lookup_policy_handles_legacy_zenodo_record_url(mocker, db_session):
    _mock_zenodo_response(mocker, licence="cc0-1.0")

    policy = await lookup_policy(
        object_id="obj-5",
        origin_url="https://zenodo.org/record/999/files/data.zip",
        session=db_session,
    )

    assert policy.licence == "cc0-1.0"
