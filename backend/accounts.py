"""Account and relay storage. Apple pairing credentials never belong in this database."""
import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def password_hash(password):
    salt = secrets.token_bytes(16)
    value = hashlib.scrypt(password.encode(), salt=salt, n=32768, r=8, p=1, maxmem=128*1024*1024)
    return f'scrypt${salt.hex()}${value.hex()}'


def password_matches(password, encoded):
    try:
        kind, salt, expected = encoded.split('$')
        if kind != 'scrypt': return False
        actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=32768, r=8, p=1, maxmem=128*1024*1024)
        return hmac.compare_digest(actual.hex(), expected)
    except (ValueError, TypeError): return False


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
              id TEXT PRIMARY KEY,email TEXT UNIQUE NOT NULL,name TEXT NOT NULL,password TEXT NOT NULL,
              role TEXT NOT NULL DEFAULT 'member',disabled INTEGER NOT NULL DEFAULT 0,created REAL NOT NULL,last_login REAL);
            CREATE TABLE IF NOT EXISTS sessions (
              token_hash TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),csrf TEXT NOT NULL,
              expires REAL NOT NULL,remember INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS session_details (
              id TEXT PRIMARY KEY,token_hash TEXT UNIQUE NOT NULL REFERENCES sessions(token_hash) ON DELETE CASCADE,
              created REAL NOT NULL,last_seen REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS invitations (
              id TEXT PRIMARY KEY,code_hash TEXT UNIQUE NOT NULL,label TEXT NOT NULL,email TEXT,
              max_uses INTEGER NOT NULL,uses INTEGER NOT NULL DEFAULT 0,expires REAL NOT NULL,
              revoked INTEGER NOT NULL DEFAULT 0,created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS enrollments (
              code_hash TEXT PRIMARY KEY,user_id TEXT NOT NULL,name TEXT NOT NULL,expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS computers (
              id TEXT PRIMARY KEY,user_id TEXT NOT NULL,name TEXT NOT NULL,secret_hash TEXT NOT NULL,
              revoked INTEGER NOT NULL DEFAULT 0,last_seen REAL NOT NULL,status TEXT NOT NULL DEFAULT '{}');
            CREATE TABLE IF NOT EXISTS commands (
              id TEXT PRIMARY KEY,computer_id TEXT NOT NULL,action TEXT NOT NULL,payload TEXT NOT NULL,
              state TEXT NOT NULL,created REAL NOT NULL,expires REAL NOT NULL,result TEXT,error TEXT);
            CREATE INDEX IF NOT EXISTS command_queue ON commands(computer_id,state,created);
            ''')
            if 'username' not in {row['name'] for row in db.execute('PRAGMA table_info(users)')}:
                db.execute('ALTER TABLE users ADD COLUMN username TEXT')
            db.execute('CREATE UNIQUE INDEX IF NOT EXISTS users_username ON users(username COLLATE NOCASE) WHERE username IS NOT NULL')
            # Add non-secret session identifiers without invalidating existing sign-ins.
            for row in db.execute('SELECT token_hash,expires,remember FROM sessions WHERE token_hash NOT IN (SELECT token_hash FROM session_details)').fetchall():
                created=row['expires']-(30*86400 if row['remember'] else 8*3600)
                db.execute('INSERT INTO session_details VALUES(?,?,?,?)',(secrets.token_urlsafe(16),row['token_hash'],created,created))

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db: yield db
        finally: db.close()

    def has_owner(self):
        with self.db() as db: return db.execute("SELECT 1 FROM users WHERE role='owner'").fetchone() is not None

    def owner_uses_temporary_password(self):
        with self.db() as db:
            owner = db.execute("SELECT password FROM users WHERE role='owner' AND disabled=0").fetchone()
        return owner is not None and password_matches('admin', owner['password'])

    def cleanup(self):
        with self.db() as db:
            db.execute('DELETE FROM sessions WHERE expires<?',(time.time(),))
            db.execute('DELETE FROM enrollments WHERE expires<?',(time.time(),))
            db.execute("UPDATE commands SET state='expired',payload='{}',error='Delivery expired; device outcome unknown.' WHERE expires<? AND state IN ('queued','delivered')",(time.time(),))
            db.execute('DELETE FROM commands WHERE created<?',(time.time()-86400,))

    def create_user(self, email, name, password, invitation=None, owner=False):
        encoded = password_hash(password)
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            if owner:
                if db.execute("SELECT 1 FROM users WHERE role='owner'").fetchone(): raise ValueError('Owner setup is already complete.')
            else:
                invite = db.execute('SELECT * FROM invitations WHERE code_hash=?', (digest(invitation or ''),)).fetchone()
                if not invite or invite['revoked'] or invite['expires'] < time.time() or invite['uses'] >= invite['max_uses'] or invite['email'] and invite['email'] != email:
                    raise ValueError('This invitation is invalid, expired, used, or belongs to another email.')
            uid = secrets.token_urlsafe(16)
            try: db.execute('INSERT INTO users(id,email,name,password,role,created) VALUES(?,?,?,?,?,?)', (uid,email,name,encoded,'owner' if owner else 'member',time.time()))
            except sqlite3.IntegrityError: raise ValueError('Unable to register this email. Try signing in.') from None
            if not owner: db.execute('UPDATE invitations SET uses=uses+1 WHERE id=?', (invite['id'],))
        return self.user(uid)

    @staticmethod
    def public_user(row):
        return {k:row[k] for k in ['id','email','name','role','disabled','created','last_login']}

    def user(self, uid):
        with self.db() as db:
            row = db.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
            return self.public_user(row) if row else None

    def _login_row(self, identifier):
        identifier=identifier.strip().casefold()
        with self.db() as db:
            return db.execute('SELECT * FROM users WHERE email=? OR username=? COLLATE NOCASE',(identifier,identifier)).fetchone()

    def configure_owner_login(self, username, password):
        """Local management only. Preserve the owner identity and its linked computers."""
        username=username.strip().casefold()
        if not re.fullmatch(r'[a-z0-9][a-z0-9_.-]{2,31}',username):
            raise ValueError('Use a username of 3–32 letters, numbers, dots, dashes or underscores.')
        if not isinstance(password,str) or not 1<=len(password)<=128:
            raise ValueError('Use a password from 1 to 128 characters.')
        encoded=password_hash(password)
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            owners=db.execute("SELECT id FROM users WHERE role='owner' AND disabled=0").fetchall()
            if len(owners)!=1:raise ValueError('Exactly one active owner is required.')
            uid=owners[0]['id']
            try:db.execute('UPDATE users SET username=?,password=? WHERE id=?',(username,encoded,uid))
            except sqlite3.IntegrityError:raise ValueError('That username is already in use.') from None
            db.execute('DELETE FROM sessions WHERE user_id=?',(uid,))
        return self.user(uid)

    def login(self, email, password):
        row = self._login_row(email)
        # Use the same expensive hash path for unknown accounts.
        valid = password_matches(password, row['password']) if row else bool(password_hash(password) and False)
        if not valid or row['disabled']: return None
        with self.db() as db: db.execute('UPDATE users SET last_login=? WHERE id=?',(time.time(),row['id']))
        return self.user(row['id'])

    def new_session(self, uid, remember):
        with self.db() as db:return self._new_session(db,uid,remember)

    @staticmethod
    def _new_session(db, uid, remember):
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        expires = time.time() + (30*86400 if remember else 8*3600)
        db.execute('DELETE FROM sessions WHERE expires<?',(time.time(),))
        db.execute('INSERT INTO sessions VALUES(?,?,?,?,?)',(digest(token),uid,csrf,expires,int(remember)))
        db.execute('INSERT INTO session_details VALUES(?,?,?,?)',(secrets.token_urlsafe(16),digest(token),time.time(),time.time()))
        return token, csrf, expires

    def login_session(self,email,password,remember):
        row=self._login_row(email)
        valid=password_matches(password,row['password']) if row else bool(password_hash(password) and False)
        if not valid or row['disabled']:return None
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            # A password changed during the expensive verification must not mint a stale sign-in.
            changed=db.execute('UPDATE users SET last_login=? WHERE id=? AND password=? AND disabled=0',(time.time(),row['id'],row['password'])).rowcount
            if not changed:return None
            tokens=self._new_session(db,row['id'],remember)
        return self.user(row['id']),tokens

    def session(self, token):
        if not token: return None
        with self.db() as db:
            row = db.execute('''SELECT users.*,sessions.csrf,sessions.expires,sessions.remember FROM sessions
              JOIN users ON users.id=sessions.user_id WHERE sessions.token_hash=? AND sessions.expires>? AND users.disabled=0''',(digest(token),time.time())).fetchone()
            if row:db.execute('UPDATE session_details SET last_seen=? WHERE token_hash=? AND last_seen<?',(time.time(),digest(token),time.time()-60))
        return {'user':self.public_user(row),'csrf':row['csrf'],'expires':row['expires'],'remember':bool(row['remember'])} if row else None

    def logout(self, token):
        with self.db() as db: db.execute('DELETE FROM sessions WHERE token_hash=?',(digest(token),))

    def browser_sessions(self, uid, current_token):
        with self.db() as db:
            rows=db.execute('''SELECT session_details.id,session_details.created,session_details.last_seen,
              sessions.expires,sessions.remember,sessions.token_hash=? AS current
              FROM sessions JOIN session_details USING(token_hash)
              WHERE sessions.user_id=? AND sessions.expires>? ORDER BY current DESC,last_seen DESC LIMIT 100''',
              (digest(current_token),uid,time.time())).fetchall()
        return [{**dict(row),'current':bool(row['current']),'remember':bool(row['remember'])} for row in rows]

    def revoke_browser_session(self,uid,session_id,current_token):
        with self.db() as db:
            row=db.execute('''SELECT sessions.token_hash FROM sessions JOIN session_details USING(token_hash)
              WHERE sessions.user_id=? AND session_details.id=?''',(uid,session_id)).fetchone()
            if not row:raise ValueError('Browser session not found.')
            if hmac.compare_digest(row['token_hash'],digest(current_token)):raise ValueError('Use Sign out to close this browser session.')
            db.execute('DELETE FROM sessions WHERE token_hash=?',(row['token_hash'],))

    def revoke_other_sessions(self,uid,current_token):
        with self.db() as db:
            return db.execute('DELETE FROM sessions WHERE user_id=? AND token_hash<>?',(uid,digest(current_token))).rowcount

    def change_password(self,uid,current_password,new_password):
        with self.db() as db:row=db.execute('SELECT password FROM users WHERE id=? AND disabled=0',(uid,)).fetchone()
        if not row or not password_matches(current_password,row['password']):raise ValueError('Your current password is incorrect.')
        if current_password==new_password:raise ValueError('Choose a different new password.')
        encoded=password_hash(new_password)
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            changed=db.execute('UPDATE users SET password=? WHERE id=? AND password=? AND disabled=0',(encoded,uid,row['password'])).rowcount
            if not changed:raise ValueError('Your account changed. Sign in again before changing the password.')
            db.execute('DELETE FROM sessions WHERE user_id=?',(uid,))
        return self.user(uid)

    def users(self):
        with self.db() as db: return [self.public_user(r) for r in db.execute('SELECT * FROM users ORDER BY created DESC LIMIT 500')]

    def disable(self, uid, disabled):
        with self.db() as db:
            row=db.execute('SELECT role FROM users WHERE id=?',(uid,)).fetchone()
            if not row: raise ValueError('User not found.')
            if row['role']=='owner': raise ValueError('The owner cannot be disabled here.')
            db.execute('UPDATE users SET disabled=? WHERE id=?',(int(disabled),uid))
            if disabled:
                db.execute('DELETE FROM sessions WHERE user_id=?',(uid,))
                db.execute("UPDATE computers SET revoked=1,status='{}' WHERE user_id=?",(uid,))
                db.execute("UPDATE commands SET state='cancelled',payload='{}' WHERE computer_id IN (SELECT id FROM computers WHERE user_id=?) AND state='queued'",(uid,))

    def create_invitation(self, label, email, max_uses, hours):
        code=secrets.token_urlsafe(24)
        with self.db() as db:
            db.execute('INSERT INTO invitations(id,code_hash,label,email,max_uses,expires,created) VALUES(?,?,?,?,?,?,?)',(secrets.token_urlsafe(12),digest(code),label,email,max_uses,time.time()+hours*3600,time.time()))
        return code

    def invitations(self):
        with self.db() as db: return [dict(r) for r in db.execute('SELECT id,label,email,max_uses,uses,expires,revoked,created FROM invitations ORDER BY created DESC LIMIT 200')]

    def revoke_invitation(self, iid):
        with self.db() as db: db.execute('UPDATE invitations SET revoked=1 WHERE id=?',(iid,))

    def enrollment(self, uid, name):
        code=secrets.token_urlsafe(24)
        with self.db() as db:
            if db.execute('SELECT count(*) FROM computers WHERE user_id=? AND revoked=0',(uid,)).fetchone()[0]>=20:raise ValueError('Unlink an existing computer before adding another.')
            db.execute('DELETE FROM enrollments WHERE expires<?',(time.time(),))
            db.execute('DELETE FROM enrollments WHERE user_id=?',(uid,))
            db.execute('INSERT INTO enrollments VALUES(?,?,?,?)',(digest(code),uid,name,time.time()+300))
        return code

    def enroll(self, code):
        secret=secrets.token_urlsafe(32)
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT enrollments.* FROM enrollments JOIN users ON users.id=enrollments.user_id WHERE code_hash=? AND expires>? AND users.disabled=0',(digest(code),time.time())).fetchone()
            if not row: raise ValueError('Computer link code is invalid or expired.')
            cid=secrets.token_urlsafe(16)
            db.execute('INSERT INTO computers(id,user_id,name,secret_hash,last_seen) VALUES(?,?,?,?,?)',(cid,row['user_id'],row['name'],digest(secret),0))
            db.execute('DELETE FROM enrollments WHERE code_hash=?',(digest(code),))
        return {'id':cid,'secret':secret,'name':row['name']}

    def agent(self, secret):
        with self.db() as db:
            row=db.execute('SELECT computers.* FROM computers JOIN users ON users.id=computers.user_id WHERE secret_hash=? AND revoked=0 AND users.disabled=0',(digest(secret),)).fetchone()
        return dict(row) if row else None

    def computers(self, uid):
        with self.db() as db: rows=db.execute('SELECT id,name,last_seen,status,revoked FROM computers WHERE user_id=? ORDER BY name LIMIT 100',(uid,)).fetchall()
        return [{**dict(r),'status':json.loads(r['status']),'online':not r['revoked'] and time.time()-r['last_seen']<15} for r in rows]

    def revoke_computer(self, uid, cid):
        with self.db() as db:
            if not db.execute('SELECT 1 FROM computers WHERE id=? AND user_id=?',(cid,uid)).fetchone(): raise ValueError('Computer not found.')
            db.execute("UPDATE computers SET revoked=1,status='{}' WHERE id=?",(cid,))
            db.execute("UPDATE commands SET state='cancelled',payload='{}' WHERE computer_id=? AND state='queued'",(cid,))

    def queue(self, uid, cid, action, payload):
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            computer=db.execute('SELECT * FROM computers WHERE id=? AND user_id=? AND revoked=0',(cid,uid)).fetchone()
            if not computer: raise ValueError('Computer not found.')
            if time.time()-computer['last_seen']>=15: raise ValueError('The home helper is offline. No command was sent.')
            db.execute("UPDATE commands SET state='expired',payload='{}',error='Delivery expired; device outcome unknown.' WHERE expires<? AND state IN ('queued','delivered')",(time.time(),))
            if action in {'stop','disconnect'}:
                db.execute("UPDATE commands SET state='cancelled',payload='{}' WHERE computer_id=? AND state='queued'",(cid,))
            elif db.execute("SELECT 1 FROM commands WHERE computer_id=? AND state IN ('queued','delivered')",(cid,)).fetchone(): raise ValueError('Wait for the outstanding command acknowledgement.')
            command=secrets.token_urlsafe(16)
            db.execute('INSERT INTO commands(id,computer_id,action,payload,state,created,expires) VALUES(?,?,?,?,?,?,?)',(command,cid,action,json.dumps(payload),'queued',time.time(),time.time()+120))
        return {'id':command,'state':'queued','action':action}

    def poll(self, cid, status):
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('UPDATE computers SET last_seen=?,status=? WHERE id=?',(time.time(),json.dumps(status),cid))
            db.execute("UPDATE commands SET state='expired',payload='{}',error='Delivery expired; device outcome unknown.' WHERE expires<? AND state IN ('queued','delivered')",(time.time(),))
            row=db.execute("SELECT * FROM commands WHERE computer_id=? AND state='queued' ORDER BY CASE WHEN action IN ('stop','disconnect') THEN 0 ELSE 1 END,created LIMIT 1",(cid,)).fetchone()
            if row: db.execute("UPDATE commands SET state='delivered' WHERE id=?",(row['id'],))
            db.execute('DELETE FROM commands WHERE created<?',(time.time()-86400,))
        return {'id':row['id'],'action':row['action'],'payload':json.loads(row['payload'])} if row else None

    def heartbeat(self, cid, status):
        with self.db() as db:db.execute('UPDATE computers SET last_seen=?,status=? WHERE id=?',(time.time(),json.dumps(status),cid))

    def complete(self, cid, command, result, error):
        with self.db() as db:
            changed=db.execute("UPDATE commands SET state=?,result=?,error=?,payload='{}' WHERE id=? AND computer_id=? AND state='delivered'",('failed' if error else 'acknowledged',json.dumps(result),error,command,cid)).rowcount
            if not changed: raise ValueError('This command is not awaiting an acknowledgement.')

    def command(self, uid, command):
        with self.db() as db:
            db.execute("UPDATE commands SET state='expired',payload='{}',error='Delivery expired; device outcome unknown.' WHERE expires<? AND state IN ('queued','delivered')",(time.time(),))
            row=db.execute('SELECT commands.id,commands.action,commands.state,commands.result,commands.error FROM commands JOIN computers ON computers.id=commands.computer_id WHERE commands.id=? AND computers.user_id=?',(command,uid)).fetchone()
        return {**dict(row),'result':json.loads(row['result']) if row['result'] else None} if row else None
