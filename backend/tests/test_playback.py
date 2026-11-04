import asyncio
import unittest
from backend.services.playback import PlaybackController

class Device:
    connection='connected'
    def __init__(self): self.calls=[];self.busy=False;self.overlap=False;self.fail=False
    async def command(self,name,*args):
        if self.busy:self.overlap=True
        self.busy=True
        try:
            await asyncio.sleep(.005)
            if self.fail:raise ConnectionError('USB removed')
            self.calls.append((name,*args))
        finally:self.busy=False

FRAMES=[{'lat':40.7+i*.00001,'lng':-74.,'t':float(i)*.03,'distance':float(i),'speed':1.} for i in range(8)]

class PlaybackTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):self.device=Device();self.player=PlaybackController(self.device)
    async def asyncTearDown(self):await self.player.stop(clear=False)
    async def test_first_ack_before_success_and_no_overlap(self):
        result=await self.player.start(FRAMES,'Test')
        self.assertEqual(len(self.device.calls),1)
        await self.player.task
        self.assertFalse(self.device.overlap)
        self.assertEqual(self.player.state,'arrived')
        self.assertEqual(len(self.device.calls),len(FRAMES))
    async def test_pause_freezes_progress_and_resume_finishes(self):
        await self.player.start(FRAMES,'Test');await self.player.pause();i=self.player.index
        await asyncio.sleep(.1);self.assertEqual(self.player.index,i)
        await self.player.resume();await self.player.task
        self.assertEqual(self.player.index,len(FRAMES)-1)
    async def test_stop_restores_and_blocks_further_coordinates(self):
        await self.player.start(FRAMES,'Test');await self.player.stop();count=len(self.device.calls)
        await asyncio.sleep(.1)
        self.assertEqual(len(self.device.calls),count)
        self.assertEqual(self.device.calls[-1],('stop',))
    async def test_disconnect_pauses_instead_of_faking_progress(self):
        await self.player.start(FRAMES,'Test');self.device.fail=True;await self.player.task
        self.assertEqual(self.player.state,'paused');self.assertEqual(self.player.index,0)
    async def test_refuses_overlapping_or_invalid_journeys(self):
        bad=[FRAMES[1],FRAMES[0]]
        with self.assertRaises(ValueError):await self.player.start(bad,'Bad')
        await self.player.start(FRAMES,'First')
        with self.assertRaises(RuntimeError):await self.player.start(FRAMES,'Second')
    async def test_failed_first_ack_leaves_explicit_error(self):
        self.device.fail=True
        with self.assertRaises(ConnectionError):await self.player.start(FRAMES,'Failure')
        self.assertEqual(self.player.state,'error')
