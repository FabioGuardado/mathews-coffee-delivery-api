import asyncio
import logging
from datetime import datetime, timezone

from app.cassandra import cassandra_execute

logger = logging.getLogger(__name__)

FLUSH_INTERVAL = 30  # segundos entre cada ciclo de flush


# ── Core flush logic ──────────────────────────────────────────────────────────

async def flush_driver(driver_id: str, redis, cassandra) -> None:
    """
    Lee todos los entries del Stream del driver y los inserta en Cassandra.
    Solo hace XTRIM si TODOS los inserts fueron exitosos.
    Si falla alguno, los entries quedan en el Stream para el próximo ciclo.
    """
    entries = await redis.xrange(f"driver:{driver_id}:breadcrumbs")
    if not entries:
        return

    try:
        for _entry_id, fields in entries:
            ts_unix = int(fields["ts"])
            dt = datetime.fromtimestamp(ts_unix, tz=timezone.utc)
            day = dt.date()
            order_id = int(fields["order_id"])

            # ── gps_by_driver ─────────────────────────────────────────────────
            await cassandra_execute(
                cassandra,
                """
                INSERT INTO gps_by_driver (driver_id, day, ts, lat, lng, heading, speed, order_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    driver_id,
                    day,
                    dt,
                    float(fields["lat"]),
                    float(fields["lng"]),
                    int(fields["heading"]),
                    float(fields["speed"]),
                    order_id,
                ),
            )

            # ── gps_by_order ──────────────────────────────────────────────────
            await cassandra_execute(
                cassandra,
                """
                INSERT INTO gps_by_order (order_id, ts, driver_id, lat, lng, heading, speed)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    order_id,
                    dt,
                    driver_id,
                    float(fields["lat"]),
                    float(fields["lng"]),
                    int(fields["heading"]),
                    float(fields["speed"]),
                ),
            )

        # Solo trimear si todos los inserts fueron exitosos
        await redis.xtrim(f"driver:{driver_id}:breadcrumbs", maxlen=0)
        logger.info("Flushed %d breadcrumbs for driver %s", len(entries), driver_id)

    except Exception as e:
        # No trimear — los entries se preservan para el próximo ciclo
        logger.error(
            "Flush failed for driver %s (%d entries preserved): %s",
            driver_id, len(entries), e,
        )


# ── Background task ───────────────────────────────────────────────────────────

async def start_flush_worker(app) -> None:
    """
    Loop que corre cada FLUSH_INTERVAL segundos.
    Itera sobre todos los drivers en available_drivers y flushea sus breadcrumbs.
    Iniciado como asyncio.create_task() en el lifespan.
    """
    logger.info("Breadcrumb flush worker started (interval=%ds)", FLUSH_INTERVAL)

    while True:
        try:
            await asyncio.sleep(FLUSH_INTERVAL)

            driver_ids = await app.state.redis.smembers("available_drivers")
            if not driver_ids:
                continue

            for driver_id in driver_ids:
                await flush_driver(driver_id, app.state.redis, app.state.cassandra)

        except asyncio.CancelledError:
            logger.info("Breadcrumb flush worker stopped")
            raise
        except Exception as e:
            logger.error("Flush worker cycle error: %s", e)
