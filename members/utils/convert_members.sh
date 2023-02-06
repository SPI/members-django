#!/bin/bash

# This script converts CSV file of the members database into something reimportable in pgweb (see README.md: Import users in pgweb)

f="$1"

echo "COPY auth_user (id, first_name, last_name, username, email, password, is_staff, date_joined, is_superuser, is_active) FROM stdin;"
awk -F , -v OFS='\t' '{print $1, $2, $3, $4, $4, "crypt$"$5"$"$5, $6, $7, "f", "t"}' "$1"
