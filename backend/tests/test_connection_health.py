import unittest
from unittest.mock import AsyncMock,patch
from backend.services.connection_health import connection_health,connection_error


class ConnectionHealthTests(unittest.IsolatedAsyncioTestCase):
    async def test_readiness_contains_counts_without_phone_identity_or_location_commands(self):
        discover=AsyncMock(return_value=[{'id':'PRIVATE-TEST-IDENTITY','transport':'USB'}])
        with patch('backend.services.connection_health.psk_available',return_value=True):
            result=await connection_health(discover,True)
        discover.assert_awaited_once()
        self.assertEqual(result['locationWrites'],0)
        self.assertNotIn('PRIVATE-TEST-IDENTITY',str(result))
        self.assertEqual(next(c['state'] for c in result['checks'] if c['key']=='usb'),'pass')

    async def test_missing_phone_or_apple_service_has_an_actionable_result(self):
        with patch('backend.services.connection_health.psk_available',return_value=False):
            empty=await connection_health(AsyncMock(return_value=[]))
            unavailable=await connection_health(AsyncMock(side_effect=ConnectionRefusedError('PRIVATE-ADDRESS')))
        self.assertEqual(next(c['state'] for c in empty['checks'] if c['key']=='usb'),'action')
        self.assertIn('Apple',next(c['description'] for c in unavailable['checks'] if c['key']=='usb'))
        self.assertNotIn('PRIVATE-ADDRESS',str(unavailable))

    async def test_library_failures_do_not_expose_raw_device_details(self):
        closed=type('ConnectionTerminatedError',(Exception,),{})
        locked=type('PasswordRequiredError',(Exception,),{})
        self.assertIn('Unlock',connection_error(locked('PRIVATE-IDENTITY')))
        self.assertIn('USB',connection_error(closed('PRIVATE-ADDRESS')))
        self.assertNotIn('PRIVATE',connection_error(ValueError('PRIVATE-IDENTITY')))

    async def test_authored_recovery_messages_and_timeouts_remain_useful(self):
        self.assertEqual(connection_error(RuntimeError('Connect the cable.')),'Connect the cable.')
        self.assertIn('did not respond',connection_error(TimeoutError('PRIVATE-ADDRESS')))
