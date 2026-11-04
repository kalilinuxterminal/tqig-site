"""Own the entire developer session in one task; do not close it after each set."""
import asyncio
import math
import time
from backend.services.connection_health import connection_error
from datetime import datetime, timezone


class DeviceController:
    def __init__(self, factory, discovery, hold_refresh_seconds=4):
        self.factory, self.discovery = factory, discovery
        self.lock = asyncio.Lock()
        self.queue = asyncio.Queue()
        self.task = None
        self.connection = "disconnected"
        self.state = "disconnected"
        self.simulation = "unknown"
        self.device = None
        self.last_accepted = None
        self.error = None
        self.last_event = None
        self.hold_refresh_seconds=hold_refresh_seconds
        self.last_write_at=0.0
        self.hold_refreshes=0
        self.acknowledged_writes=0

    def snapshot(self):
        return {"state": self.state, "connection": self.connection, "simulation": self.simulation,
                "device": self.device, "lastAcceptedCoordinates": self.last_accepted,
                "observedCoordinates": None, "restorationVerified": False,
                "error": self.error, "lastEvent": self.last_event,
                "deviceReadbackAvailable": False,'holdRefreshes':self.hold_refreshes,
                'acknowledgedLocationWrites':self.acknowledged_writes}

    def event(self, action):
        self.last_event = {"action": action, "at": datetime.now(timezone.utc).isoformat()}

    async def connect(self, udid):
        async with self.lock:
            if self.task and not self.task.done():
                raise RuntimeError("Disconnect the current session before connecting another device.")
            if udid not in {d["id"] for d in await self.discovery()}:
                raise RuntimeError("Selected iPhone is not available on the chosen connection. Refresh the device list and try again.")
            self.connection, self.error = "connecting", None
            self.state = "pairing"
            self.simulation = "unknown"
            self.hold_refreshes=self.acknowledged_writes=0
            self.last_write_at=0.0
            if not self.device or self.device.get("id") != udid:
                self.last_accepted = None
            self.device = None
            ready = asyncio.get_running_loop().create_future()
            self.queue = asyncio.Queue()
            self.task = asyncio.create_task(self._session(udid, ready))
            try:
                await asyncio.wait_for(asyncio.shield(ready), 75)
            except BaseException:
                self.task.cancel()
                await asyncio.gather(self.task, return_exceptions=True)
                if ready.done() and not ready.cancelled():
                    ready.exception()
                self.connection = "disconnected"
                raise
            return self.snapshot()

    async def _session(self, udid, ready):
        pending = None
        location = None
        try:
            async with self.factory(udid) as (location, ping, metadata):
                self.device, self.connection = metadata, "connected"
                self.state = "ready"
                self.event("developer_service_opened")
                ready.set_result(True)
                try:
                    while True:
                        try:
                            refresh_due=self.simulation=='command_accepted' and self.last_accepted is not None
                            timeout=min(3,max(.01,self.hold_refresh_seconds-(time.monotonic()-self.last_write_at))) if refresh_due else 3
                            command, args, pending = await asyncio.wait_for(self.queue.get(), timeout)
                        except asyncio.TimeoutError:
                            if self.simulation=='command_accepted' and self.last_accepted is not None and time.monotonic()-self.last_write_at>=self.hold_refresh_seconds:
                                # A stationary hold is a real repeated coordinate write, not
                                # movement or trip-clock progress. Stop/clear disables it.
                                self.simulation='unknown'
                                await asyncio.wait_for(location.set(self.last_accepted['lat'],self.last_accepted['lng']),20)
                                self.last_write_at=time.monotonic()
                                self.hold_refreshes+=1;self.acknowledged_writes+=1
                                self.simulation='command_accepted'
                                self.event('position_hold_refreshed')
                            await asyncio.wait_for(ping(), 10)
                            continue
                        if command == "set":
                            # Mark uncertain before writing: a failed reply may follow a successful device write.
                            self.state = "applying"
                            self.simulation = "unknown"
                            await asyncio.wait_for(location.set(*args), 20)
                            self.last_accepted = {"lat": args[0], "lng": args[1]}
                            self.last_write_at=time.monotonic()
                            self.acknowledged_writes+=1
                            self.simulation = "command_accepted"
                            self.state = "active"
                            self.event("set_command_accepted")
                        elif command == "stop" or command == "disconnect":
                            self.state = "stopping"
                            self.simulation = "unknown"
                            await asyncio.wait_for(location.clear(), 15)
                            # This upstream method expects no device reply. Never call this GPS verification.
                            self.simulation = "clear_sent"
                            self.state = "ready"
                            self.event("clear_command_sent")
                        if not pending.done():
                            pending.set_result(True)
                        pending = None
                        if command == "disconnect":
                            break
                finally:
                    # Clear before closing on normal stop, failed command, shutdown, or disconnect.
                    # A lost cable may make this impossible; preserve unknown state on failure.
                    if self.simulation != "clear_sent":
                        try:
                            await asyncio.wait_for(location.clear(), 5)
                            self.simulation = "clear_sent"
                            self.state = "ready"
                            self.event("cleanup_clear_sent")
                        except BaseException:
                            self.simulation = "unknown"
        except asyncio.CancelledError:
            self.error = "Session interrupted. Verify the iPhone's actual location before continuing."
            if pending and not pending.done():
                pending.set_exception(RuntimeError(self.error))
            if not ready.done():
                ready.cancel()
            raise
        except Exception as exc:
            self.error = connection_error(exc)
            if not ready.done():
                ready.set_exception(RuntimeError(self.error))
            if pending and not pending.done():
                pending.set_exception(RuntimeError(self.error))
        finally:
            self.connection = "disconnected"
            self.state = "error" if self.error else "disconnected"
            while not self.queue.empty():
                _, _, future = self.queue.get_nowait()
                if not future.done():
                    future.set_exception(RuntimeError(self.error or "Device disconnected."))

    async def command(self, name, *args):
        if name not in {"set", "stop", "disconnect"}:
            raise ValueError("Unknown command")
        if name == "set":
            if len(args) != 2 or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in args):
                raise ValueError("Coordinates must be finite numbers")
            if not (-90 <= args[0] <= 90 and -180 <= args[1] <= 180):
                raise ValueError("Coordinates are out of range")
        async with self.lock:
            if self.connection != "connected" or not self.task or self.task.done():
                raise RuntimeError("No authorized developer connection. Connect the iPhone first.")
            result = asyncio.get_running_loop().create_future()
            await self.queue.put((name, args, result))
            try:
                await asyncio.wait_for(asyncio.shield(result), 30)
                if name == "disconnect":
                    await asyncio.wait_for(asyncio.shield(self.task), 10)
            except BaseException:
                self.task.cancel()
                await asyncio.gather(self.task, return_exceptions=True)
                if result.done() and not result.cancelled():
                    result.exception()
                self.simulation = "unknown"
                raise
            return self.snapshot()

    async def close(self):
        if self.task and not self.task.done():
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)
