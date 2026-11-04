"""Interactive owner initialization for a production account server; never accepts passwords in arguments."""
import argparse
import getpass
from backend.accounts import Store
from backend.portal import DATA,Credentials

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--enroll-home-pc', action='store_true', help='Create a five-minute owner enrollment code.')
    args = parser.parse_args()
    store=Store(DATA/'portal.sqlite3')
    if args.enroll_home_pc:
        identifier = input('Owner username or email: ')
        owner = store.login(identifier, getpass.getpass('Owner password: '))
        if not owner or owner['role'] != 'owner':
            raise SystemExit('An active owner sign-in is required.')
        print('Home PC enrollment code (expires in five minutes): ' + store.enrollment(owner['id'], 'Home PC'))
        return
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
