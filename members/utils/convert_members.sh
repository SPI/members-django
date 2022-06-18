#!/bin/bash

# This script converts CSV file of the members database into something reimportable in pgweb (see README.md: Import users in pgweb)

f="$1"

echo "COPY auth_user (first_name, username, email, password, is_staff, date_joined, is_superuser, last_name, is_active) FROM stdin;"
awk -F , -v OFS='\t' '{print $2, $3, $3, "crypt$"$4"$"$4, $5, $6, "f", "", "t"}' "$1"
