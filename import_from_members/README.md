# Import database content from the old members app

Import database to membersdjango:
```
sudo -u postgres pg_dump --data-only --no-owner --no-privileges --serializable-deferrable -T vote_log -T vote_session -T vote_voter -T members_memid_seq -T members -T temp -T applications spimembers > spimembers.sql
sudo -u postgres psql spimembers -c 'create table temp as select memid, email, name, firstdate, ismember, iscontrib, ismanager, sub_private, lastactive, createvote from members where memid IN (SELECT member from applications where validemail is not null or validemail_date is not null);'
sudo -u postgres psql spimembers -c 'create table temp2 as select appid, appdate, member, contrib, comment, lastchange, manager, manager_date, approve, approve_date, contribapp, emailkey_date, validemail_date from applications;'
sudo -u postgres pg_dump --no-owner --no-privileges --serializable-deferrable -t temp spimembers > temp_table.sql
sudo -u postgres pg_dump --no-owner --no-privileges --serializable-deferrable -t temp2 spimembers > applications.sql
sudo -u postgres psql spimembers -c 'drop table temp'; sudo -u postgres psql spimembers -c 'drop table temp2';

sudo chown $USER:postgres spimembers.sql temp_table.sql

sudo -u postgres psql spimembers -c "\copy (select memid,left(COALESCE(substring(replace(name,',',' ') from '(.*?) '),replace(name,',',' ')),30),COALESCE(left(substring(replace(name,',',' ') from ' (.*)'),30),'.'),lower(email),password,ismanager,emailkey_date from members, applications where applications.member = members.memid and (validemail is not null or validemail_date is not null)  order by memid) to members.csv with csv delimiter ',';"

utils/convert_members.sh members.csv > members.sql
sudo -u postgres psql membersdjango < members.sql

sudo -u postgres psql membersdjango < temp_table.sql
sudo -u postgres psql --single-transaction membersdjango < applications.sql
sudo -u postgres psql membersdjango < import_from_members_additional_fixes.sql
sudo -u postgres psql --single-transaction membersdjango < spimembers.sql
sudo -u postgres psql membersdjango < import_from_members_additional_fixes2.sql
sudo -u postgres psql -c 'delete from applications where member NOT in (select memid from members);' membersdjango
sudo -u postgres psql -c "update auth_user set is_superuser = 't' where id=2054;" membersdjango
```
