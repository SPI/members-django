\set ON_ERROR_STOP
BEGIN;

-- insert into auth_user (id, email, date_joined, password, is_superuser, is_staff, is_active, username, first_name, last_name) select memid, email, coalesce(firstdate, NOW()), 'imported', false, false, true, memid, '', '' from temp;

insert into members (memid, name, email, ismember, iscontrib, ismanager, sub_private, lastactive, createvote) select memid, name, email, ismember, iscontrib, ismanager, coalesce(sub_private, false), lastactive, createvote from temp;
insert into applications (appid, appdate, member, contrib, comment, lastchange, manager, manager_date, approve, approve_date, contribapp) select appid, appdate, member, contrib, comment, lastchange, manager, manager_date, approve, approve_date, contribapp from temp2;

-- drop table temp;
drop table temp2;

SELECT setval(pg_get_serial_sequence('"auth_user"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "auth_user";

SELECT setval(pg_get_serial_sequence('"vote_vote"','ref'), coalesce(max("ref"), 1), max("ref") IS NOT null) FROM "vote_vote";

COMMIT;

