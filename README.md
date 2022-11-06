# Members-django

Rewriting of the (Flask-based) Members app in Django

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

## Import database content from the old members app

Import database to membersdjango:
```
sudo -u postgres pg_dump --data-only --no-owner --no-privileges --serializable-deferrable -T vote_log -T vote_session -T vote_voter -T members_memid_seq -T members -T temp -T applications spimembers > spimembers.sql
sudo -u postgres psql spimembers -c 'create table temp as select memid, email, name, firstdate, iscontrib, ismanager, sub_private, lastactive, createvote from members where memid IN (SELECT member from applications where validemail is not null or validemail_date is not null);'
sudo -u postgres psql spimembers -c 'create table temp2 as select appid, appdate, member, contrib, comment, lastchange, manager, manager_date, approve, approve_date, contribapp from applications;'
sudo -u postgres pg_dump --no-owner --no-privileges --serializable-deferrable -t temp spimembers > temp_table.sql
sudo -u postgres pg_dump --no-owner --no-privileges --serializable-deferrable -t temp2 spimembers > applications.sql
sudo -u postgres psql spimembers -c 'drop table temp'; sudo -u postgres psql spimembers -c 'drop table temp2';

sudo chown $USER:postgres spimembers.sql temp_table.sql

sudo -u postgres psql membersdjango < temp_table.sql
sudo -u postgres psql --single-transaction membersdjango < applications.sql
sudo -u postgres psql membersdjango < import_from_members_additional_fixes.sql
sudo -u postgres psql --single-transaction membersdjango < spimembers.sql
sudo -u postgres psql membersdjango < import_from_members_additional_fixes.sql
sudo -u postgres psql -c 'delete from applications where member NOT in (select memid from members);' membersdjango
```

Import users in pgweb:
```
# sudo -u postgres pg_dump --no-owner --no-privileges --serializable-deferrable -t account_communityauthsite -t account_communityauthorg spi_pgweb > communityauth.sql

sudo -u postgres psql spimembers -c "update applications set validemail_date=null where appid = 2067;"  # fix illogical corner case
sudo -u postgres psql spimembers -c "delete from members where memid = 1641;"  # twice in db with same email address
sudo -u postgres psql spimembers -c "delete from applications where member = 1641;"

sudo -u postgres psql spimembers -c "\copy (select memid,left(COALESCE(substring(replace(name,',',' ') from '(.*?) '),replace(name,',',' ')),30),COALESCE(left(substring(replace(name,',',' ') from ' (.*)'),30),'.'),lower(email),password,ismanager,emailkey_date from members, applications where applications.member = members.memid and (validemail ='t' or validemail_date is not null)  order by memid) to members.csv with csv delimiter ',';"

utils/convert_members.sh members.csv > members.sql
sudo -u postgres psql spi_pgweb < members.sql

```

## Tests

To run tests, the current user must have the rights to create a database. In postgres, run:
```
alter user <USERNAME> CREATEDB;
```

# Relationship between Membersdjango, PGWeb and PGLister

Membersdjango is the membership web application. PGWeb handles the centralized login system. PGLister handles mailing lists. For the installation of PGWeb and PGLister, see [here](https://gitlab.com/cmatte/pglister/-/blob/master/INSTALL.md).

## Link between PGWeb and Membersdjango

Similarly to PGLister, a community auth site must be created in PGWeb. First, create a community org auth in [/admin/account/communityauthorg/](https://pgweb.spi-inc.org/admin/account/communityauthorg/). Then create the auth site in [/admin/account/communityauthsite/](https://pgweb.spi-inc.org/admin/account/communityauthsite/).

Use the following parameters:
- Redirecturl: https://your_membersjango_address.tld/auth_receive/
- Apiurl: https://your_pgweb_address.tld/account/auth/1/
- Cryptkey: a random password that you can create using `python tools/communityauth/generate_cryptkey.py`
- Org: the org site you just created

Then add the correct information in membersdjango's `settings.py` (or `local_settings.py`):
```
USE_PG_COMMUNITY_AUTH = True
PGAUTH_REDIRECT = "https://your_pgweb_address.tld/account/auth/1/"
PGAUTH_KEY = "YOUR_CRYPTKEY"
PGAUTH_REDIRECT_SUCCESS = "http://your_membersjango_address.tld/"
PGAUTH_SIGNUP = "https://your_pgweb_address.tld/account/signup/"
PGAUTH_ROOT = "https://your_pgweb_address.tld/"
```

## Scripts

There are several scripts to handle the links between these different components.
- email-stats: send email containing stats on members and applications
- email-voters: email contributing members about open votes
- cleanup-contrib: deal with sending notifications to or cleaning up inactive SPI contributing members
- subprivate: prompt the members application for contributing members list and subscribe them to the spi-private mailing list

Add these as cron jobs such as:
- email-stats, email-voters and cleanup-contrib (ping and clean) are running in the context of the membersdjango application
- subprivate is running in the context of PGLister
