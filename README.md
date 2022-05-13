# Members-django

Rewriting of the (Flask-based) Members app in Django

## Dependencies

- python3.7.3
- python3-django
- postgresql
- python-psycopg2
- pyenv
- python-virtualenv

## Install

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
python manage.py migrate
sudo -u postgres psql -c 'create role <username>' ; sudo -u postgres psql -c 'create database membersdjango'
```

You can also use the ansible script to deploy the application in a testing or production environment.

## Import database content from the old members app

```
sudo -u postgres pg_dump --data-only --no-owner --no-privileges --serializable-deferrable -T vote_log -T vote_session -T vote_voter -T members_memid_seq spimembers > spimembers.sql
sudo chown $USER:postgres /tmp/spimembers.sql
sudo -u postgres psql --single-transaction membersdjango < /tmp/spimembers.sql
sudo -u postgres psql -f import_from_members.sql membersdjango
```

## Tests

To run tests, the current user must have the rights to create a database. In postgres, run:
```
alter user <USERNAME> CREATEDB;
```
