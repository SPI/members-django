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

Import database to membersdjango:
```
sudo -u postgres pg_dump --data-only --no-owner --no-privileges --serializable-deferrable -T vote_log -T vote_session -T vote_voter -T members_memid_seq -T members -T temp spimembers > spimembers.sql
sudo -u postgres psql spimembers -c 'create table temp as select memid, email, name, phone, pgpkey, firstdate, expirydate, iscontrib, ismanager, sub_private, lastactive, createvote from members where memid IN (SELECT member from applications where validemail is not null or validemail_date is not null);'
sudo -u postgres pg_dump --no-owner --no-privileges --serializable-deferrable -t temp spimembers > temp_table.sql
sudo -u postgres psql spimembers -c 'drop table temp';

sudo chown $USER:postgres /tmp/spimembers.sql /tmp/temp_table.sql

sudo -u postgres psql membersdjango < /tmp/temp_table.sql
sudo -u postgres psql membersdjango < import_from_members_additional_fixes.sql
sudo -u postgres psql --single-transaction membersdjango < /tmp/spimembers.sql
```

Import users in pgweb:
```
sudo -u postgres psql spimembers -c "update applications set validemail_date=null where appid = 2067;"  # fix illogical corner case
sudo -u postgres psql spimembers -c "delete from members where memid = 1641;"  # twice in db with same email address
sudo -u postgres psql spimembers -c "delete from applications where member = 1641;"

sudo -u postgres psql spimembers -c "\copy (select memid,left(replace(name,',',' '),30),lower(email),password,ismanager,emailkey_date from members, applications where applications.member = members.memid and (validemail ='t' or validemail_date is not null)  order by memid) to /tmp/members.csv with csv delimiter ',';"

utils/convert_members.sh /tmp/members.csv > members.sql
sudo -u postgres psql spi_pgweb < members.sql

```

## Tests

To run tests, the current user must have the rights to create a database. In postgres, run:
```
alter user <USERNAME> CREATEDB;
```
