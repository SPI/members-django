# Members-django

Rewriting of the (Flask-based) Members app in Django

## Dependencies

- python3.7.3
- python3-django

## Install venv for dev environment

```
CC=clang pyenv install 3.7.3
virtualenv -p ~/.pyenv/versions/3.7.3/bin/python3 venv
source ./venv/bin/activate
pip install django==3.2
python -m django --version  # Should be 3.2
```
