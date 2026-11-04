import json
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from fastapi.testclient import TestClient
from backend.portal import create_portal
from backend.accounts import password_matches

BASE='http://127.0.0.1:8770'
PASSWORD='Temporary-test-password-947!'


class PortalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.app=create_portal(Path(self.tmp.name)/'accounts.db',local_preview=True)
        self.client=TestClient(self.app,base_url=BASE,headers={'Origin':BASE})
        nonce=self.client.get('/api/auth/setup').json()['nonce']
        response=self.client.post('/api/auth/owner',json={'email':'owner@example.test','password':PASSWORD,'name':'Test Owner','nonce':nonce})
        self.assertEqual(response.status_code,200,response.text)
        self.csrf=response.json()['csrf']
        self.client.headers['X-TQIG-CSRF']=self.csrf

    def tearDown(self):
        self.client.close();self.tmp.cleanup()

    def fresh(self):return TestClient(self.app,base_url=BASE,headers={'Origin':BASE})

    def invite(self,**changes):
        response=self.client.post('/api/admin/invitations',json={'label':'Test invitation',**changes})
        self.assertEqual(response.status_code,200,response.text)
        return response.json()['code']

    def member(self,email='member@example.test'):
        client=self.fresh()
        response=client.post('/api/auth/signup',json={'email':email,'name':'Test Member','password':PASSWORD,'invitation':self.invite()})
        self.assertEqual(response.status_code,200,response.text)
        client.headers['X-TQIG-CSRF']=response.json()['csrf']
        self.addCleanup(client.close)
        return client,response.json()['user']

    def enrolled(self):
        response=self.client.post('/api/computers/enrollment',json={'name':'Test home computer'})
        code=response.json()['code']
        agent=self.fresh();self.addCleanup(agent.close)
        response=agent.post('/api/agent/enroll',json={'code':code})
        self.assertEqual(response.status_code,200,response.text)
        credentials=response.json()
        agent.headers['Authorization']='Bearer '+credentials['secret']
        return agent,credentials,code

    def test_account_and_admin_endpoints_reject_anonymous_access(self):
        with self.fresh() as client:
            for path in ['/api/admin/users','/api/admin/invitations','/api/computers']:
                self.assertEqual(client.get(path).status_code,401)
            self.assertIsNone(client.get('/api/auth/session').json()['user'])

    def test_signup_requires_valid_single_use_invitation(self):
        code=self.invite()
        payload={'email':'new@example.test','name':'New Member','password':PASSWORD,'invitation':code}
        with self.fresh() as client:
            self.assertEqual(client.post('/api/auth/signup',json={**payload,'invitation':'not-a-valid-invitation'}).status_code,409)
            self.assertEqual(client.post('/api/auth/signup',json=payload).status_code,200)
            self.assertEqual(client.post('/api/auth/signup',json={**payload,'email':'other@example.test'}).status_code,409)

    def test_single_use_invitation_remains_atomic_during_concurrent_signup(self):
        code=self.invite()
        def register(index):
            try:self.app.state.store.create_user(f'parallel{index}@example.test','Parallel Member',PASSWORD,code);return True
            except ValueError:return False
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(register,[1,2]))
        self.assertEqual(sorted(results),[False,True])

    def test_invitation_email_restriction_expiry_and_revocation(self):
        code=self.invite(email='intended@example.test')
        payload={'email':'wrong@example.test','name':'Wrong User','password':PASSWORD,'invitation':code}
        with self.fresh() as client:self.assertEqual(client.post('/api/auth/signup',json=payload).status_code,409)
        iid=self.client.get('/api/admin/invitations').json()['invitations'][0]['id']
        self.client.post('/api/admin/invitations/'+iid+'/revoke',json={})
        with self.fresh() as client:self.assertEqual(client.post('/api/auth/signup',json={**payload,'email':'intended@example.test'}).status_code,409)
        expired=self.invite()
        with self.app.state.store.db() as db:db.execute('UPDATE invitations SET expires=0')
        with self.fresh() as client:self.assertEqual(client.post('/api/auth/signup',json={**payload,'invitation':expired}).status_code,409)

    def test_owner_cannot_be_claimed_twice_or_via_signup_role(self):
        self.assertFalse(self.client.get('/api/auth/setup').json()['allowed'])
        with self.fresh() as client:
            response=client.post('/api/auth/signup',json={'email':'bad@example.test','name':'Bad Owner','password':PASSWORD,'invitation':self.invite(),'role':'owner'})
            self.assertEqual(response.status_code,422)

    def test_password_hashes_and_user_responses_never_expose_credentials(self):
        users=self.client.get('/api/admin/users').json()['users']
        self.assertNotIn('password',users[0]);self.assertNotIn(PASSWORD,json.dumps(users))
        with self.app.state.store.db() as db:encoded=db.execute('SELECT password FROM users').fetchone()[0]
        self.assertNotEqual(encoded,PASSWORD);self.assertTrue(password_matches(PASSWORD,encoded));self.assertFalse(password_matches('wrong',encoded))

    def test_configured_owner_username_keeps_device_link_and_revokes_old_sessions(self):
        agent,credentials,_=self.enrolled()
        original=self.client.get('/api/auth/session').json()['user']
        changed=self.app.state.store.configure_owner_login('test-owner','short')
        self.assertEqual(changed['id'],original['id'])
        self.assertEqual(self.client.get('/api/admin/users').status_code,401)
        self.assertEqual(agent.post('/api/agent/heartbeat',json={'status':{}}).status_code,200)
        with self.fresh() as client:
            response=client.post('/api/auth/signin',json={'email':'TEST-OWNER','password':'short','remember':True})
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json()['user']['id'],original['id'])
            self.assertIn('Max-Age=2592000',response.headers['set-cookie'])
            self.assertEqual(client.get('/api/computers').json()['computers'][0]['id'],credentials['id'])
        with self.fresh() as client:
            self.assertEqual(client.post('/api/auth/signin',json={'email':original['email'],'password':'short'}).status_code,200)

    def test_username_is_not_a_default_login_and_registration_still_requires_long_password(self):
        with self.fresh() as client:
            self.assertEqual(client.post('/api/auth/signin',json={'email':'test-owner','password':'short'}).status_code,401)
        self.app.state.store.configure_owner_login('test-owner','short')
        with self.fresh() as client:
            self.assertEqual(client.post('/api/auth/signin',json={'email':'test-owner','password':'wrong'}).status_code,401)
            self.assertEqual(client.post('/api/auth/signin',json={'email':'owner@example.test','password':PASSWORD}).status_code,401)
            self.assertEqual(client.post('/api/auth/signup',json={'email':'new@example.test','name':'Test Member','password':'short','invitation':'a-fixture-invitation'}).status_code,422)

    def test_remember_cookie_logout_and_session_expiry(self):
        with self.fresh() as client:
            response=client.post('/api/auth/signin',json={'email':'owner@example.test','password':PASSWORD,'remember':True})
            self.assertEqual(response.status_code,200)
            header=response.headers['set-cookie'].lower()
            self.assertIn('httponly',header);self.assertIn('samesite=lax',header);self.assertIn('max-age=2592000',header)
            csrf=response.json()['csrf'];client.headers['X-TQIG-CSRF']=csrf
            self.assertEqual(client.post('/api/auth/signout',json={}).status_code,200)
            self.assertIsNone(client.get('/api/auth/session').json()['user'])
        with self.app.state.store.db() as db:db.execute('UPDATE sessions SET expires=0')
        self.assertEqual(self.client.get('/api/admin/users').status_code,401)

    def test_wrong_csrf_and_foreign_origins_are_rejected(self):
        self.assertEqual(self.client.post('/api/admin/invitations',json={'label':'Bad'},headers={'X-TQIG-CSRF':'wrong'}).status_code,403)
        self.assertEqual(self.client.post('/api/auth/signin',json={'email':'owner@example.test','password':PASSWORD},headers={'Origin':'https://untrusted.example'}).status_code,403)

    def test_member_cannot_read_owner_users_or_create_invitations(self):
        member,_=self.member()
        self.assertEqual(member.get('/api/admin/users').status_code,403)
        self.assertEqual(member.post('/api/admin/invitations',json={'label':'No'}).status_code,403)

    def test_disabling_member_revokes_existing_sessions_and_agent_access(self):
        member,user=self.member()
        self.assertEqual(member.get('/api/computers').status_code,200)
        response=self.client.post('/api/admin/users/'+user['id'],json={'disabled':True})
        self.assertEqual(response.status_code,200)
        self.assertEqual(member.get('/api/computers').status_code,401)
        self.assertEqual(member.post('/api/auth/signin',json={'email':user['email'],'password':PASSWORD}).status_code,401)
        owner_id=self.client.get('/api/auth/session').json()['user']['id']
        self.assertEqual(self.client.post('/api/admin/users/'+owner_id,json={'disabled':True}).status_code,409)

    def test_enrollment_is_one_use_and_no_agent_secret_is_listed(self):
        agent,credentials,code=self.enrolled()
        self.assertEqual(agent.post('/api/agent/enroll',json={'code':code}).status_code,409)
        listing=self.client.get('/api/computers').json()
        self.assertNotIn(credentials['secret'],json.dumps(listing));self.assertNotIn('secret_hash',json.dumps(listing))

    def test_remote_commands_require_ownership_and_actual_agent_acknowledgement(self):
        agent,credentials,_=self.enrolled();cid=credentials['id']
        agent.post('/api/agent/poll',json={'status':{'connection':'connected','device':{'name':'Test iPhone','id':'PRIVATE-APPLE-IDENTITY','ios':'26.6','transport':'USB'}}})
        payload={'action':'location','payload':{'lat':28.5550254,'lng':-81.7661906}}
        member,_=self.member()
        self.assertEqual(member.post('/api/computers/'+cid+'/commands',json=payload).status_code,409)
        queued=self.client.post('/api/computers/'+cid+'/commands',json=payload).json()
        self.assertEqual(queued['state'],'queued')
        command=agent.post('/api/agent/poll',json={'status':{'connection':'connected'}}).json()['command']
        self.assertEqual(command['payload'],payload['payload'])
        self.assertEqual(self.client.get('/api/commands/'+queued['id']).json()['state'],'delivered')
        self.assertEqual(agent.post('/api/agent/poll',json={'status':{}}).json()['command'],None)
        response=agent.post('/api/agent/result',json={'command':command['id'],'result':{'state':'active','simulation':'set_acknowledged','device':{'id':'PRIVATE-APPLE-IDENTITY'}}})
        self.assertEqual(response.status_code,200)
        outcome=self.client.get('/api/commands/'+queued['id']).json()
        self.assertEqual(outcome['state'],'acknowledged')
        self.assertNotIn('PRIVATE-APPLE-IDENTITY',json.dumps(outcome))
        with self.app.state.store.db() as db:self.assertEqual(db.execute('SELECT payload FROM commands WHERE id=?',(command['id'],)).fetchone()[0],'{}')

    def test_revoked_computer_and_offline_commands_fail(self):
        agent,credentials,_=self.enrolled();cid=credentials['id']
        self.assertEqual(self.client.post('/api/computers/'+cid+'/commands',json={'action':'stop'}).status_code,409)
        agent.post('/api/agent/heartbeat',json={'status':{'connection':'connected'}})
        self.client.post('/api/computers/'+cid+'/revoke',json={})
        self.assertEqual(agent.post('/api/agent/poll',json={'status':{}}).status_code,401)

    def test_expired_delivery_is_unknown_not_silently_replayed(self):
        agent,credentials,_=self.enrolled();agent.post('/api/agent/poll',json={'status':{}})
        response=self.client.post('/api/computers/'+credentials['id']+'/commands',json={'action':'stop'})
        command=response.json()['id']
        with self.app.state.store.db() as db:db.execute('UPDATE commands SET expires=0 WHERE id=?',(command,))
        outcome=self.client.get('/api/commands/'+command).json()
        self.assertEqual(outcome['state'],'expired');self.assertIn('unknown',outcome['error'])

    def test_invalid_remote_location_and_command_types_are_rejected(self):
        agent,credentials,_=self.enrolled();cid=credentials['id'];agent.post('/api/agent/heartbeat',json={'status':{}})
        self.assertEqual(self.client.post('/api/computers/'+cid+'/commands',json={'action':'location','payload':{'lat':100,'lng':0}}).status_code,409)
        self.assertEqual(self.client.post('/api/computers/'+cid+'/commands',json={'action':'shell','payload':{}}).status_code,422)
