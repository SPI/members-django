# Members-django

This is the SPI membership web application, which lives at:

https://members.spi-inc.org/

It enables the following actions:

 * New member registration

  Non-contributing members just need to apply for a new account and
  verify their email address.

 * Contributing member application

  Once a user is a valid non-contributing member they can submit an
  application for contributing membership, providing details of why they
  meet the criteria.

 * Management of member applications

  Users who are marked as application managers can review outstanding
  applications for contributing membership and approve or deny them
  as appropriate.

 * Centralized authentication system

  The members applications acts as a centralized authentication system
  for [SPI's mailing list system](https://lists.spi-inc.org) based on
  [PGLister](https://gitlab.com/cmatte/pglister)
  and [its private archives](https://archives-private.spi-inc.org)
  based on [PGArchives](https://gitlab.com/cmatte/pgarchives).

The app is written in Python using the Django frame work and designed to
run on a Debian 10 (Buster) host.

The official code repository for the site lives within the SPI
infrastructure and can be browsed at:

https://gitlab.com/spi-inc/members-django

There is also an unofficial mirrors in GitHub:

https://github.com/SPI/members-django

Patches can be emailed to webmaster@spi-inc.org or submitted via the
pull request feature on these sites.

## Dependencies

- python3.7.3
- python3-django
- postgresql
- python-psycopg2
- pyenv
- python-virtualenv
- python-wxgtk3.0  # for OpenSTV

pip packages:
- django==3.2
- psycopg2-binary
- requests
- pycryptodomex

## Install

This is a role to deploy members in SPI's (currently private) [ansible repository](https://gitlab.com/spi-inc/ansible).

To redeploy, use:

```
ansible-playbook -e @config.yml -e @credentials.yml --vault-password-file .vault_pass.txt playbooks/althea.yml --tags members-django
```

## Dev environment

Install venv:
```bash
CC=clang pyenv install 3.7.3
virtualenv -p ~/.pyenv/versions/3.7.3/bin/python3 venv
source ./venv/bin/activate
pip install django==3.2
python -m django --version  # Should be 3.2
pip install psycopg2-binary requests pycryptodomex
```

Create database:
```bash
sudo -u postgres psql -c 'create role <username>' ; sudo -u postgres psql -c 'create database membersdjango'
python manage.py migrate
```

You can also use the ansible script to deploy the application in a testing or production environment.

## Tests

To run tests, the current user must have the rights to create a database. In postgres, run:
```
alter user <USERNAME> CREATEDB;
```

In the right venv, they can then be run using:
```
PYTHONPATH=membersapp/app/OpenSTV/openstv python manage.py test
```

# Link between Membersdjango, PGLister and PGArchives

To authenticate users in PGLister and PGArchives-private, a community auth site must be created in Membersdjango. First, create a community org auth in [/admin/account/communityauthorg/](https://members.spi-inc.org/admin/account/communityauthorg/). Then create the auth site in [/admin/account/communityauthsite/](https://members.spi-inc.org/admin/account/communityauthsite/).

Use the following parameters:
- Redirecturl: https://lists.spi-inc.org/auth_receive/
- Apiurl: https://members.spi-inc.org/account/auth/1/
- Cryptkey: a random password that you can create using `python tools/communityauth/generate_cryptkey.py`
- Org: the org site you just created

Then add the correct information in membersdjango's `settings.py` (or `local_settings.py`):
```
USE_PG_COMMUNITY_AUTH = True
PGAUTH_REDIRECT = "https://members.spi-inc.org/account/auth/1/""
PGAUTH_KEY = "YOUR_CRYPTKEY"
LOGIN_URL = "/accounts/login/"
```

## Scripts

There are several scripts to handle the links between these different components.
- `email-stats`: send email containing stats on members and applications
- `email-voters`: email contributing members about open votes
- `cleanup-contrib`: deal with sending notifications to or cleaning up inactive SPI contributing members
- `subprivate`: prompt the members application for contributing members list and subscribe them to the spi-private mailing list

Add these as cron jobs such as:
- `email-stats`, `email-voters` and `cleanup-contrib` (`ping` and `clean`) are running in the context of the membersdjango application
- `subprivate` is running in the context of PGLister
