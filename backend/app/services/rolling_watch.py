import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.integrations.moonraker import MoonrakerClient
from app.models.entities import Printer, utc_now
from app.schemas.console import MoonrakerNotificationIn
from app.services.console_entries import ingest_moonraker_notification
from app.services.retention import prune_rolling_entries


@dataclass
class WatchRuntimeStatus:
    active_printer_ids: list[int]
    task_count: int
    background_watch_enabled: bool


class RollingWatchManager:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._tasks: dict[int, asyncio.Task[None]] = {}

    def status(self) -> WatchRuntimeStatus:
        self._tasks = {printer_id: task for printer_id, task in self._tasks.items() if not task.done()}
        return WatchRuntimeStatus(
            active_printer_ids=sorted(self._tasks),
            task_count=len(self._tasks),
            background_watch_enabled=self.settings.background_watch_enabled,
        )

    async def run(self, stop_event: asyncio.Event) -> None:
        if not self.settings.background_watch_enabled:
            await stop_event.wait()
            return

        last_prune_at: datetime | None = None
        while not stop_event.is_set():
            await self._sync_watch_tasks(stop_event)
            last_prune_at = self._maybe_prune(last_prune_at)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=self.settings.watch_manager_interval_seconds)
            except TimeoutError:
                pass

        for task in self._tasks.values():
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._tasks.clear()

    async def _sync_watch_tasks(self, stop_event: asyncio.Event) -> None:
        enabled_ids = self._enabled_printer_ids()

        for printer_id, task in list(self._tasks.items()):
            if task.done() or printer_id not in enabled_ids:
                task.cancel()
                self._tasks.pop(printer_id, None)

        for printer_id in enabled_ids:
            if printer_id not in self._tasks:
                self._tasks[printer_id] = asyncio.create_task(self._watch_printer(printer_id, stop_event))

    def _enabled_printer_ids(self) -> set[int]:
        with SessionLocal() as db:
            return set(
                db.scalars(
                    select(Printer.id).where(
                        Printer.is_enabled.is_(True),
                        Printer.console_watch_enabled.is_(True),
                    )
                ).all()
            )

    def _maybe_prune(self, last_prune_at: datetime | None) -> datetime:
        now = datetime.now(UTC)
        if (
            last_prune_at is None
            or (now - last_prune_at).total_seconds() >= self.settings.retention_prune_interval_seconds
        ):
            with SessionLocal() as db:
                prune_rolling_entries(db, now=now)
            return now
        return last_prune_at

    async def _watch_printer(self, printer_id: int, stop_event: asyncio.Event) -> None:
        while not stop_event.is_set():
            with SessionLocal() as db:
                printer = db.get(Printer, printer_id)
                if printer is None or not printer.is_enabled or not printer.console_watch_enabled:
                    return
                client = MoonrakerClient(printer.base_url, printer.api_key)
                printer.connection_status = "connecting"
                printer.last_error = None
                printer.updated_at = utc_now()
                db.commit()

            try:
                async for payload in client.listen_notifications():
                    with SessionLocal() as db:
                        printer = db.get(Printer, printer_id)
                        if printer is None or not printer.is_enabled or not printer.console_watch_enabled:
                            return
                        notification = MoonrakerNotificationIn.model_validate(payload)
                        ingest_moonraker_notification(db, printer=printer, notification=notification)
                        printer.connection_status = "connected"
                        printer.last_connected_at = utc_now()
                        printer.last_error = None
                        printer.updated_at = utc_now()
                        db.commit()
                    if stop_event.is_set():
                        return
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                with SessionLocal() as db:
                    printer = db.get(Printer, printer_id)
                    if printer is not None:
                        printer.connection_status = "error"
                        printer.last_error = str(exc)
                        printer.updated_at = utc_now()
                        db.commit()
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=self.settings.moonraker_reconnect_delay_seconds)
                except TimeoutError:
                    pass
