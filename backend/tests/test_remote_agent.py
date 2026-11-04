import asyncio
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from fastapi.testclient import TestClient
from backend.portal import create_portal
from backend.services.remote_agent import RemoteAgent
from backend.relay_contracts import safe_status


class AgentTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.app=create_portal(Path(self.tmp.name)/'portal.db',local_preview=True)
        self.client=TestClient(self.app,base_url='http://127.0.0.1:8770')
        self.addCleanup(self.client.close)
        self.store=self.app.state.store
        self.owner=self.store.create_user('qa@example.test','QA Owner','Test-only-long-password-293!',owner=True)
        self.actions=[]
        self.status={'state':'ready','connection':'connected','simulation':'clear_sent','device':{'id':'PRIVATE-PAIR-IDENTITY','name':'Fixture iPhone','ios':'26.6','transport':'USB'},'journey':{'state':'idle'}}
        async def execute(action,payload):
            self.actions.append((action,payload))
            if action=='location':self.status.update(state='active',simulation='command_accepted',lastAcceptedCoordinates=payload)
            if action=='stop':self.status.update(state='ready',simulation='clear_sent')
            return self.status
        self.agent=RemoteAgent(lambda:self.status,execute,path=Path(self.tmp.name)/'private-agent.json')
        def request(path,body):
            headers={'Authorization':'Bearer '+self.agent.credentials['secret']} if self.agent.credentials else {}
            response=self.client.post('/api/agent/'+path,json=body,headers=headers)
            if response.status_code>=400:raise urllib.error.HTTPError('http://local.test',response.status_code,'Request rejected',{},None)
            return response.json()
        self.agent.request=request
        await self.agent.link(self.store.enrollment(self.owner['id'],'Fixture home PC'),'PRIVATE-PAIR-IDENTITY','usb')
        for _ in range(100):
            if self.store.computers(self.owner['id'])[0]['online']:break
            await asyncio.sleep(.03)
        self.cid=self.agent.credentials['id']

    async def asyncTearDown(self):await self.agent.close(unlink=True)

    async def wait_state(self,command,state):
        for _ in range(150):
            if self.store.command(self.owner['id'],command)['state']==state:return
            await asyncio.sleep(.03)
        self.fail('Expected relay state not reached: '+state)

    async def test_outbound_worker_returns_actual_executor_ack_and_keeps_device_identity_local(self):
        command=self.store.queue(self.owner['id'],self.cid,'location',{'lat':28.5550254,'lng':-81.7661906})
        await self.wait_state(command['id'],'acknowledged')
        self.assertEqual([a for a,p in self.actions].count('location'),1)
        outcome=self.store.command(self.owner['id'],command['id'])
        self.assertEqual(outcome['result']['lastAcceptedCoordinates']['lat'],28.5550254)
        self.assertNotIn('PRIVATE-PAIR-IDENTITY',json.dumps(outcome))
        self.assertNotIn('secret',self.agent.public())
        self.assertNotIn('PRIVATE-PAIR-IDENTITY',json.dumps(self.store.computers(self.owner['id'])))

    async def test_replaced_phone_cannot_be_controlled_but_recovery_remains_available(self):
        self.status['device']['id']='DIFFERENT-LOCAL-PHONE'
        for action,payload in [('connect',{}),('location',{'lat':28.5550254,'lng':-81.7661906})]:
            command=self.store.queue(self.owner['id'],self.cid,action,payload)
            await self.wait_state(command['id'],'failed')
            self.assertIn('different iPhone',self.store.command(self.owner['id'],command['id'])['error'])
        self.assertEqual(self.actions,[])
        command=self.store.queue(self.owner['id'],self.cid,'stop',{})
        await self.wait_state(command['id'],'acknowledged')
        self.assertEqual([action for action,_ in self.actions],['stop'])

    async def test_revocation_stops_local_simulation_and_removes_saved_agent_access(self):
        self.store.revoke_computer(self.owner['id'],self.cid)
        for _ in range(150):
            if not self.agent.active:break
            await asyncio.sleep(.03)
        self.assertFalse(self.agent.active)
        self.assertIsNone(self.agent.credentials)
        self.assertFalse(self.agent.path.exists())
        self.assertIn('stop',[a for a,p in self.actions])

    async def test_stop_cancels_queued_motion_before_delivery(self):
        # Stop remains an independent, prioritized command; it must not wait for a queued move.
        await self.agent.close()
        pending=self.store.queue(self.owner['id'],self.cid,'location',{'lat':28.5550254,'lng':-81.7661906})
        stop=self.store.queue(self.owner['id'],self.cid,'stop',{})
        self.assertEqual(self.store.command(self.owner['id'],pending['id'])['state'],'cancelled')
        delivered=self.store.poll(self.cid,self.status)
        self.assertEqual(delivered['id'],stop['id'])
        self.assertEqual(delivered['action'],'stop')

    async def test_status_contract_rejects_malformed_geometry_and_preserves_playback_rate(self):
        status=safe_status({'connection':{},'device':{'transport':{}},'lastAcceptedCoordinates':{'lat':100,'lng':0},'journey':{'phase':{},'frame':{'lat':'not a coordinate'},'playbackRate':2,'error':'private device identity and address'}})
        self.assertEqual(status['connection'],'disconnected')
        self.assertIsNone(status['lastAcceptedCoordinates'])
        self.assertIsNone(status['journey']['frame'])
        self.assertEqual(status['journey']['playbackRate'],2)
        self.assertNotIn('private device identity',json.dumps(status))
