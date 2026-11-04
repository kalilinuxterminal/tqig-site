import asyncio
import math
import time

class PlaybackController:
    def __init__(self, device):
        self.device = device
        self.task = None
        self.gate = asyncio.Event()
        self.stop_event = asyncio.Event()
        self.send_lock = asyncio.Lock()
        self.state = 'idle'
        self.frames = []
        self.index = 0
        self.name = None
        self.rate = 1
        self.error = None
        self.trip = None
        self.elapsed = 0.0
        self.acknowledged_samples = 0

    def snapshot(self):
        frame = self.frames[min(self.index, len(self.frames)-1)] if self.frames else None
        phase = frame.get('phase','outbound') if frame else 'outbound'
        remaining = 0
        if self.trip:
            outward=self.trip['outboundDuration'];stay=self.trip['stayDuration'];back=self.trip['returnDuration']
            if self.state=='arrived':phase='complete'
            elif self.elapsed<outward:phase='outbound';remaining=outward-self.elapsed
            elif self.elapsed<outward+stay:phase='stay';remaining=outward+stay-self.elapsed
            elif self.trip['returnToStart']:phase='return';remaining=max(0,outward+stay+back-self.elapsed)
            else:phase='stay' if self.state!='arrived' else 'complete'
            if frame and frame.get('phase')=='outbound' and self.elapsed>=outward and self.state!='arrived':
                phase,remaining='outbound',0
        return {'state': self.state, 'mode': 'device', 'name': self.name, 'index': self.index,
                'totalFrames': len(self.frames), 'frame': frame, 'error': self.error,
                'duration': self.frames[-1]['t'] if self.frames else 0,
                'totalDistance': self.frames[-1]['distance'] if self.frames else 0, 'playbackRate': self.rate,
                'trip':self.trip,'elapsed':self.elapsed,'phase':phase,'phaseRemaining':remaining,
                'acknowledgedSamples':self.acknowledged_samples}

    async def start(self, frames, name, rate=1, trip=None):
        if len(frames)<2 or not math.isfinite(rate) or not .25<=rate<=4:
            raise ValueError('A valid journey and playback rate are required.')
        if self.task and not self.task.done() or self.state == 'paused':
            raise RuntimeError('Stop the current journey before starting another.')
        if self.device.connection != 'connected':
            raise RuntimeError('Connect an authorized iPhone before starting Device Test Mode.')
        for i, frame in enumerate(frames):
            if not all(math.isfinite(frame[k]) for k in ['lat','lng','t','distance','speed']):
                raise ValueError('Journey contains non-finite values.')
            if i and (frame['t'] <= frames[i-1]['t'] or frame['distance'] < frames[i-1]['distance']):
                raise ValueError('Journey times must increase and distance must not decrease.')
        if frames[0]['t'] != 0:
            raise ValueError('A journey must begin at time zero.')
        if trip and abs(sum(trip[k] for k in ['outboundDuration','stayDuration','returnDuration'])-frames[-1]['t'])>.01:
            raise ValueError('Trip durations must match the journey timeline.')
        if trip and (not trip['returnToStart'] and trip['returnDuration']!=0 or abs(trip['outboundDistance']+trip['returnDistance']-frames[-1]['distance'])>.1):
            raise ValueError('Return settings and trip distances must match the journey.')
        self.frames, self.name, self.rate = frames, name, rate
        self.trip,self.elapsed,self.acknowledged_samples=trip,0.0,0
        self.index, self.error, self.state = 0, None, 'starting'
        self.stop_event.clear()
        self.gate.set()
        # Start does not report success before the first actual device acknowledgement.
        try:
            async with self.send_lock:
                await self.device.command('set', frames[0]['lat'], frames[0]['lng'])
                self.acknowledged_samples=1
        except Exception as exc:
            self.state, self.error = 'error', f'First location was not acknowledged: {exc}'
            raise
        self.state = 'playing'
        self.task = asyncio.create_task(self._run())
        return self.snapshot()

    async def _run(self):
        try:
            while self.index < len(self.frames)-1 and not self.stop_event.is_set():
                await self.gate.wait()
                target = self.frames[self.index+1]['t']
                # A paused interval never advances virtual progress or skips route points.
                while self.elapsed < target and not self.stop_event.is_set():
                    await self.gate.wait()
                    if self.device.connection!='connected':
                        raise ConnectionError('iPhone disconnected. The trip clock and device commands are paused.')
                    step = min((target-self.elapsed)/self.rate, .1)
                    start = time.monotonic()
                    await asyncio.sleep(step)
                    if self.gate.is_set():
                        self.elapsed=min(target,self.elapsed+(time.monotonic()-start)*self.rate)
                await self.gate.wait()
                if self.stop_event.is_set():
                    break
                async with self.send_lock:
                    if not self.gate.is_set():
                        continue
                    frame = self.frames[self.index+1]
                    previous=self.frames[self.index]
                    # A stay holds the last acknowledged position. Clock progress is not a new GPS acknowledgement.
                    if frame['lat']!=previous['lat'] or frame['lng']!=previous['lng']:
                        await self.device.command('set', frame['lat'], frame['lng'])
                        self.acknowledged_samples+=1
                    self.index += 1
                if self.index == len(self.frames)-1:
                    self.state = 'arrived'
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self.state = 'paused'
            self.error = f'Journey paused: {exc}. Reconnect before resuming, or Stop to restore.'
            self.gate.clear()

    async def pause(self):
        if self.state not in {'playing','starting'}:
            raise RuntimeError('No running journey to pause.')
        self.gate.clear()
        async with self.send_lock:
            self.state = 'paused'
        return self.snapshot()

    async def resume(self):
        if self.state != 'paused' or self.device.connection != 'connected':
            raise RuntimeError('A paused journey and a connected iPhone are required.')
        self.error, self.state = None, 'playing'
        self.gate.set()
        if not self.task or self.task.done():
            self.task = asyncio.create_task(self._run())
        return self.snapshot()

    async def stop(self, clear=True):
        self.stop_event.set()
        self.gate.set()
        if self.task and not self.task.done():
            await asyncio.wait_for(asyncio.shield(self.task), 30)
        self.state = 'stopped'
        if clear and self.device.connection == 'connected':
            await self.device.command('stop')
        elif clear:
            self.error = 'Phone disconnected. Reconnect and use Stop Simulation to restore; actual location is unknown.'
        return self.snapshot()
