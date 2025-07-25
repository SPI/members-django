#!/bin/bash

# This module configures the local database to allow creating of a
# test environment (to run manage.py test or migrate)

user=$(whoami)

sudo -u postgres psql -c "ALTER ROLE \"$user\" CREATEDB;"
sudo -u postgres psql -c 'create database membersdjango'
sudo -u postgres psql membersdjango -c "GRANT ALL ON DATABASE membersdjango TO \"$user\""
sudo -u postgres psql membersdjango -c "GRANT CREATE ON SCHEMA public TO \"$user\""
sudo -u postgres psql membersdjango -c "GRANT ALL ON ALL TABLES IN SCHEMA public TO \"$user\""
sudo -u postgres psql membersdjango -c "GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO \"$user\""
