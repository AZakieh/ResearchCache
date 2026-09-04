import uuid
from datetime import datetime
from functools import lru_cache
from typing import AsyncGenerator

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from researchcache.config import get_settings


class Base(DeclarativeBase):
    pass


class PolicyORM(Base):
    __tablename__ = "policies"

    policy_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    object_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    licence: Mapped[str] = mapped_column(Text, nullable=False)
    access_tier: Mapped[str] = mapped_column(Text, nullable=False)
    embargo_until: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    captured_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    origin_url: Mapped[str] = mapped_column(Text, nullable=False)


class CacheEntryORM(Base):
    __tablename__ = "cache_entries"

    object_id: Mapped[str] = mapped_column(Text, primary_key=True)
    origin_url: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content_type: Mapped[str] = mapped_column(Text, nullable=False)
    cached_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    last_accessed: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    ttl_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    policy_id: Mapped[int] = mapped_column(ForeignKey("policies.policy_id"), nullable=False)


class AuditEventORM(Base):
    __tablename__ = "audit_events"

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    principal_id: Mapped[str] = mapped_column(Text, nullable=False)
    object_id: Mapped[str] = mapped_column(Text, nullable=False)
    origin_url: Mapped[str] = mapped_column(Text, nullable=False)
    cache_result: Mapped[str] = mapped_column(Text, nullable=False)
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    bytes_served: Mapped[int] = mapped_column(BigInteger, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    client_ip_hash: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("ix_audit_events_timestamp", "timestamp"),
        Index("ix_audit_events_object_id", "object_id"),
    )


class ApiKeyORM(Base):
    __tablename__ = "api_keys"

    key_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    key_hash: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    institution: Mapped[str | None] = mapped_column(Text)
    label: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    rate_limit_rpm: Mapped[int | None] = mapped_column(Integer)


class BenchmarkResultORM(Base):
    __tablename__ = "benchmark_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_name: Mapped[str] = mapped_column(Text, nullable=False)
    origin_url: Mapped[str] = mapped_column(Text, nullable=False)
    origin_speed_mbps: Mapped[float] = mapped_column(nullable=False)
    cache_speed_mbps: Mapped[float] = mapped_column(nullable=False)
    origin_duration_s: Mapped[float] = mapped_column(nullable=False)
    cache_duration_s: Mapped[float] = mapped_column(nullable=False)
    measured_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)


class AllowlistORM(Base):
    __tablename__ = "allowlist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    origin_host: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    label: Mapped[str | None] = mapped_column(Text)
    added_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    added_by: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


@lru_cache
def get_engine():
    return create_async_engine(get_settings().DATABASE_URL)


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_factory()() as session:
        yield session
