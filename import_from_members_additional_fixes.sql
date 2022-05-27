\set ON_ERROR_STOP
BEGIN;

insert into auth_user (id, email, date_joined, password, is_superuser, is_staff, is_active, username, first_name, last_name) select memid, email, coalesce(firstdate, NOW()), 'imported', false, false, true, memid, '', '' from temp;

insert into members (memid, name, phone, pgpkey, firstdate, expirydate, iscontrib, ismanager, sub_private, lastactive, createvote) select memid, name, phone, pgpkey, firstdate, expirydate, iscontrib, ismanager, coalesce(sub_private, false), lastactive, createvote from temp;

drop table temp;

SELECT setval(pg_get_serial_sequence('"auth_user"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "auth_user";

COMMIT;

