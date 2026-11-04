import json
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from backend.accounts import Store,password_matches
from backend.tests import test_portal as fixtures

PASSWORD=fixtures.PASSWORD


class SecurityTests(unittest.TestCase):
    setUp=fixtures.PortalTests.setUp
    tearDown=fixtures.PortalTests.tearDown
    fresh=fixtures.PortalTests.fresh
    invite=fixtures.PortalTests.invite
    member=fixtures.PortalTests.member
    enrolled=fixtures.PortalTests.enrolled
    def second_owner_session(self):
        client=self.fresh();self.addCleanup(client.close)
        response=client.post('/api/auth/signin',json={'email':'owner@example.test','password':PASSWORD,'remember':True})
        self.assertEqual(response.status_code,200)
        client.headers['X-TQIG-CSRF']=response.json()['csrf']
        return client

    def test_browser_session_list_has_no_credentials_and_is_scoped(self):
        self.second_owner_session()
        member,_=self.member()
        own=self.client.get('/api/account/security').json()['sessions']
        self.assertEqual(len(own),2);self.assertEqual(sum(s['current'] for s in own),1)
        self.assertTrue(any(s['remember'] for s in own))
        self.assertEqual(len(member.get('/api/account/security').json()['sessions']),1)
        for key in ['token','token_hash','csrf','password','user_id']:
            self.assertNotIn(key,own[0])
        self.assertNotIn(self.client.cookies.get('tqig_preview_session'),json.dumps(own))

    def test_revoking_another_session_preserves_current_and_checks_ownership(self):
        other=self.second_owner_session()
        member,_=self.member()
        sessions=self.client.get('/api/account/security').json()['sessions']
        second=next(s['id'] for s in sessions if not s['current'])
        current=next(s['id'] for s in sessions if s['current'])
        path='/api/account/sessions/'+second+'/revoke'
        self.assertEqual(member.post(path,json={}).status_code,409)
        self.assertEqual(self.client.post('/api/account/sessions/'+current+'/revoke',json={}).status_code,409)
        self.assertEqual(self.client.post(path,json={}).status_code,200)
        self.assertIsNone(other.get('/api/auth/session').json()['user'])
        self.assertIsNotNone(self.client.get('/api/auth/session').json()['user'])

    def test_sign_out_others_preserves_current_and_other_users(self):
        other=self.second_owner_session();member,_=self.member()
        response=self.client.post('/api/account/sessions/others/revoke',json={})
        self.assertEqual(response.json()['revoked'],1)
        self.assertIsNone(other.get('/api/auth/session').json()['user'])
        self.assertIsNotNone(member.get('/api/auth/session').json()['user'])
        self.assertIsNotNone(self.client.get('/api/auth/session').json()['user'])
        with self.app.state.store.db() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM session_details').fetchone()[0],2)

    def test_password_change_checks_current_rotates_cookie_and_revokes_old_sessions(self):
        other=self.second_owner_session();agent,_,_=self.enrolled()
        new='New-unique-test-passphrase-837!'
        old_token=self.client.cookies.get('tqig_preview_session')
        self.assertEqual(self.client.post('/api/account/password',json={'currentPassword':'incorrect','newPassword':new}).status_code,409)
        self.assertIsNotNone(other.get('/api/auth/session').json()['user'])
        response=self.client.post('/api/account/password',json={'currentPassword':PASSWORD,'newPassword':new})
        self.assertEqual(response.status_code,200,response.text)
        self.assertNotEqual(self.client.cookies.get('tqig_preview_session'),old_token)
        self.assertNotEqual(response.json()['csrf'],self.csrf)
        self.assertIsNone(other.get('/api/auth/session').json()['user'])
        self.assertIsNotNone(self.client.get('/api/auth/session').json()['user'])
        self.assertEqual(agent.post('/api/agent/heartbeat',json={'status':{}}).status_code,200)
        with self.fresh() as client:
            self.assertEqual(client.post('/api/auth/signin',json={'email':'owner@example.test','password':PASSWORD}).status_code,401)
            self.assertEqual(client.post('/api/auth/signin',json={'email':'owner@example.test','password':new}).status_code,200)
        self.client.headers['X-TQIG-CSRF']=response.json()['csrf']
        self.assertEqual(len(self.client.get('/api/account/security').json()['sessions']),2)

    def test_security_actions_require_signin_and_csrf(self):
        with self.fresh() as client:
            self.assertEqual(client.get('/api/account/security').status_code,401)
            self.assertEqual(client.post('/api/account/sessions/others/revoke',json={}).status_code,401)
        self.client.headers['X-TQIG-CSRF']='wrong'
        self.assertEqual(self.client.post('/api/account/password',json={'currentPassword':PASSWORD,'newPassword':'Another-password-8492!'}).status_code,403)
        self.assertEqual(self.client.post('/api/account/sessions/others/revoke',json={}).status_code,403)

    def test_existing_sessions_migrate_without_signing_out(self):
        token=self.client.cookies.get('tqig_preview_session')
        with self.app.state.store.db() as db:db.execute('DELETE FROM session_details')
        migrated=Store(self.app.state.store.path)
        user=migrated.session(token)['user']
        self.assertEqual(user['role'],'owner')
        self.assertEqual(len(migrated.browser_sessions(user['id'],token)),1)

    def test_password_change_blocks_an_inflight_old_password_login(self):
        verified=threading.Event();release=threading.Event()
        login_thread=[]
        def paused_check(password,encoded):
            valid=password_matches(password,encoded)
            if threading.get_ident() in login_thread:
                verified.set();release.wait(5)
            return valid
        def login():
            login_thread.append(threading.get_ident())
            return self.app.state.store.login_session('owner@example.test',PASSWORD,True)
        uid=self.client.get('/api/auth/session').json()['user']['id']
        with patch('backend.accounts.password_matches',paused_check),ThreadPoolExecutor(max_workers=1) as pool:
            pending=pool.submit(login)
            try:
                self.assertTrue(verified.wait(5))
                self.app.state.store.change_password(uid,PASSWORD,'A-fresh-passphrase-493!')
            finally:release.set()
            self.assertIsNone(pending.result(5))

