import asyncio
import unittest
from backend.services.playback import PlaybackController
from backend.tests.test_playback import Device

FRAMES=[{'lat':40.,'lng':-74.,'t':0.,'distance':0.,'speed':0.,'phase':'outbound'},
        {'lat':40.00001,'lng':-74.,'t':.03,'distance':1.,'speed':0.,'phase':'stay','event':'stay'},
        {'lat':40.00001,'lng':-74.,'t':.23,'distance':1.,'speed':0.,'phase':'return','event':'stay'},
        {'lat':40.,'lng':-74.,'t':.26,'distance':2.,'speed':0.,'phase':'complete'}]
TRIP={'outboundDuration':.03,'stayDuration':.2,'returnDuration':.03,'outboundDistance':1.,'returnDistance':1.,'returnToStart':True,'travelMode':'walking'}

class TripTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):self.device=Device();self.player=PlaybackController(self.device)
    async def asyncTearDown(self):await self.player.stop(clear=False)
    async def test_stay_holds_acknowledged_destination_and_returns(self):
        await self.player.start(FRAMES,'Walking round trip',1,TRIP)
        await self.player.task
        status=self.player.snapshot();self.assertEqual(status['phase'],'complete');self.assertEqual(status['acknowledgedSamples'],3)
        self.assertEqual(len(self.device.calls),3);self.assertEqual(self.device.calls[-1],('set',40.,-74.))
    async def test_destination_countdown_pauses_and_resumes(self):
        await self.player.start(FRAMES,'Stay test',1,TRIP);await asyncio.sleep(.09)
        self.assertEqual(self.player.snapshot()['phase'],'stay')
        await self.player.pause();clock=self.player.elapsed;remaining=self.player.snapshot()['phaseRemaining']
        await asyncio.sleep(.08);self.assertEqual(self.player.elapsed,clock);self.assertEqual(self.player.snapshot()['phaseRemaining'],remaining)
        await self.player.resume();await self.player.task;self.assertEqual(self.player.state,'arrived')
    async def test_disconnect_during_stay_stops_the_clock(self):
        await self.player.start(FRAMES,'Disconnect hold',1,TRIP);await asyncio.sleep(.07)
        self.device.connection='disconnected';await self.player.task
        self.assertEqual(self.player.state,'paused');clock=self.player.elapsed
        await asyncio.sleep(.08);self.assertEqual(self.player.elapsed,clock)
    async def test_inconsistent_trip_metadata_is_rejected(self):
        with self.assertRaises(ValueError):await self.player.start(FRAMES,'Bad',1,{**TRIP,'stayDuration':100})
        with self.assertRaises(ValueError):await self.player.start(FRAMES,'Bad return',1,{**TRIP,'returnToStart':False})
