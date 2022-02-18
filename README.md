# Members-django

Rewriting of the (Flask-based) Members app in Django

## Dependencies

- python3.7.3
- python3-django
- postgresql
- python-psycopg2

## Install

## Dev environment

Install venv:
```bash
CC=clang pyenv install 3.7.3
virtualenv -p ~/.pyenv/versions/3.7.3/bin/python3 venv
source ./venv/bin/activate
pip install django==3.2
python -m django --version  # Should be 3.2
pip install psycopg2-binary
```

Create database:
```bash
sudo -u postgres psql -c 'create role <username>; create database members'
```

You can also use the ansible script to deploy the application in a testing or production environment.
