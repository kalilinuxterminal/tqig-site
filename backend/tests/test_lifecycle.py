import asyncio
import json
import unittest
from contextlib import asynccontextmanager
from backend.services.device_controller import DeviceController



class TestDevice:
    def __init__(self):
        self.calls = []
        self.fail_set = False
        self.fail_clear = False
        self.closed = False

    async def set(self, lat, lng):
        self.calls.append(("set", lat, lng))
        if self.fail_set:
            raise ConnectionError("Cable lost after write")

    async def clear(self):
        self.calls.append(("clear",))
        if self.fail_clear:
            raise ConnectionError("Cable disconnected")

    @asynccontextmanager
    async def open(self, udid):
        async def ping():
            pass
        try:
            yield self, ping, {"id": udid, "name": "Test-only fixture", "ios": "26.6", "build": "TEST"}
        finally:
            self.closed = True


async def discovery():
    return [{"id": "test-usb", "transport": "USB"}]


class ControllerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.device = TestDevice()
        self.controller = DeviceController(self.device.open, discovery)

    async def asyncTearDown(self):
        await self.controller.close()

    async def test_set_requires_authorized_session(self):
        with self.assertRaisesRegex(RuntimeError, "No authorized"):
            await self.controller.command("set", 40, -74)
        self.assertEqual(self.device.calls, [])

    async def test_set_keeps_session_open_and_distinguishes_observation(self):
        await self.controller.connect("test-usb")
        result = await self.controller.command("set", -33.8, 151.2)
        self.assertEqual(self.device.calls, [("set", -33.8, 151.2)])
        self.assertFalse(self.device.closed)
        self.assertEqual(result["simulation"], "command_accepted")
        self.assertIsNone(result["observedCoordinates"])
        self.assertFalse(result["deviceReadbackAvailable"])
        self.assertEqual(result["lastAcceptedCoordinates"], {"lat": -33.8, "lng": 151.2})

    async def test_stop_sends_clear_without_claiming_restoration(self):
        await self.controller.connect("test-usb")
        await self.controller.command("set", 1, 2)
        result = await self.controller.command("stop")
        self.assertEqual(self.device.calls[-1], ("clear",))
        self.assertEqual(result["simulation"], "clear_sent")
        self.assertFalse(result["restorationVerified"])

    async def test_disconnect_clears_before_closing(self):
        await self.controller.connect("test-usb")
        result = await self.controller.command("disconnect")
        self.assertEqual(result["connection"], "disconnected")
        self.assertEqual(self.device.calls[-1], ("clear",))
        self.assertTrue(self.device.closed)

    async def test_failed_write_never_updates_accepted_coordinates(self):
        await self.controller.connect("test-usb")
        self.device.fail_set = self.device.fail_clear = True
        with self.assertRaises(RuntimeError):
            await self.controller.command("set", 1, 2)
        self.assertEqual(self.controller.snapshot()["simulation"], "unknown")
        self.assertIsNone(self.controller.last_accepted)
        self.assertEqual(self.controller.connection, "disconnected")

    async def test_shutdown_attempts_clear(self):
        await self.controller.connect("test-usb")
        await self.controller.command("set", 1, 2)
        await self.controller.close()
        self.assertEqual(self.device.calls[-1], ("clear",))
        self.assertTrue(self.device.closed)

    async def test_invalid_coordinates_never_reach_device(self):
        await self.controller.connect("test-usb")
        for lat, lng in [(91, 0), (0, 181), (float("nan"), 0), (True, 0), ("1", 2)]:
            with self.assertRaises(ValueError):
                await self.controller.command("set", lat, lng)
        self.assertEqual(self.device.calls, [])

    async def test_missing_device_is_not_auto_selected(self):
        with self.assertRaises(RuntimeError):
            await self.controller.connect("other-device")
        self.assertIsNone(self.controller.task)

    async def test_stationary_hold_refreshes_actual_writes_without_changing_target(self):
        self.controller.hold_refresh_seconds=.035
        await self.controller.connect('test-usb')
        await self.controller.command('set',28.5550254,-81.7661906)
        await asyncio.sleep(.13)
        status=self.controller.snapshot()
        self.assertGreaterEqual(status['holdRefreshes'],2)
        self.assertEqual(status['acknowledgedLocationWrites'],1+status['holdRefreshes'])
        self.assertEqual(status['lastAcceptedCoordinates'],{'lat':28.5550254,'lng':-81.7661906})
        self.assertTrue(all(call==('set',28.5550254,-81.7661906) for call in self.device.calls))

    async def test_stop_prevents_any_more_hold_refreshes(self):
        self.controller.hold_refresh_seconds=.03
        await self.controller.connect('test-usb')
        await self.controller.command('set',28.5550254,-81.7661906)
        await asyncio.sleep(.08)
        await self.controller.command('stop')
        calls=list(self.device.calls);count=self.controller.hold_refreshes
        await asyncio.sleep(.12)
        self.assertEqual(self.device.calls,calls);self.assertEqual(self.controller.hold_refreshes,count)
        self.assertEqual(self.controller.simulation,'clear_sent')

    async def test_failed_hold_refresh_does_not_claim_a_live_simulation(self):
        self.controller.hold_refresh_seconds=.025
        await self.controller.connect('test-usb')
        await self.controller.command('set',28.5550254,-81.7661906)
        self.device.fail_set=self.device.fail_clear=True
        await asyncio.sleep(.09)
        self.assertEqual(self.controller.connection,'disconnected')
        self.assertEqual(self.controller.simulation,'unknown')
        self.assertEqual(self.controller.hold_refreshes,0)

    async def test_developer_service_failure_cannot_report_connected(self):
        @asynccontextmanager
        async def denied(udid):
            raise RuntimeError("Developer Mode is disabled")
            yield
        self.controller.factory = denied
        with self.assertRaisesRegex(RuntimeError, "Developer Mode"):
            await self.controller.connect("test-usb")
        self.assertEqual(self.controller.connection, "disconnected")
        self.assertEqual(self.controller.simulation, "unknown")
        self.assertEqual(self.device.calls, [])
