insert into auth_user (id, email, date_joined, password, is_superuser, is_staff, is_active, username, first_name, last_name) select memid, email, coalesce(firstdate, NOW()), 'imported', false, false, true, memid, '', '' from members;

SELECT setval(pg_get_serial_sequence('"auth_user"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "auth_user";
