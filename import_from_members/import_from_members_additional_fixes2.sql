SELECT setval(pg_get_serial_sequence('"vote_election"','ref'), coalesce(max("ref"), 1), max("ref") IS NOT null) FROM "vote_election";
