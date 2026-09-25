from urllib.parse import urlparse

from arq import cron
from arq.connections import RedisSettings

from app.core.config import get_settings
from app.worker.jobs import (
    create_future_partitions,
    purge_expired_images,
    send_invite,
    sweep_offline_gateways,
)


def redis_settings() -> RedisSettings:
    url = urlparse(get_settings().redis_url)
    db = int(url.path.lstrip("/") or 0)
    return RedisSettings(
        host=url.hostname or "localhost",
        port=url.port or 6379,
        database=db,
        password=url.password,
    )


class WorkerSettings:
    redis_settings = redis_settings()
    functions = [send_invite, create_future_partitions, purge_expired_images, sweep_offline_gateways]
    cron_jobs = [
        cron(create_future_partitions, hour={2}, minute=0),  # nightly lookahead
        cron(purge_expired_images, hour={3}, minute=0),  # retention
        cron(sweep_offline_gateways, minute=set(range(60)), second=45),  # hourly-ish heartbeat sweep
    ]
