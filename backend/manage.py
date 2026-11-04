"""Interactive owner initialization for a production account server; never accepts passwords in arguments."""
import getpass
from backend.accounts import Store
from backend.portal import DATA,Credentials

def main():
    store=Store(DATA/'portal.sqlite3')
    if store.has_owner():raise SystemExit('Owner setup is already complete.')
    name=input('Owner name: ').strip()
    email=input('Owner email: ').strip()
    password=getpass.getpass('Owner password (12+ characters): ')
    if password!=getpass.getpass('Confirm password: '):raise SystemExit('Passwords did not match.')
    checked=Credentials(email=email,password=password)
    if len(name)<2 or len(name)>60:raise SystemExit('Use a name from 2 to 60 characters.')
    store.create_user(checked.email,name,checked.password,owner=True)
    print('Owner initialized. Sign in on the website to create invitations.')

if __name__=='__main__':main()
