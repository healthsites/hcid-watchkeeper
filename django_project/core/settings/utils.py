# -*- coding: utf-8 -*-
import os

# Absolute filesystem path to the Django project directory:
DJANGO_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ))


def ABS_PATH(*args):
    return os.path.join(DJANGO_ROOT, *args)


def ensure_secret_key_file():
    """Checks that secret.py exists in settings dir.

    If not, creates one with a random generated SECRET_KEY setting."""

    secret_path = ABS_PATH('core', 'settings', 'secret.py')
    secret_file = os.environ.get('SECRET_FILE', 'secret.py')

    if os.path.exists('/run/secrets/{}'.format(secret_file)):
        with open(secret_path, 'w') as f:
            py_script = [
                'import imp\n',
                'imp.load_source(\'tmp_secret\', \'/run/secrets/{}\')\n'.format(secret_file),
                'from tmp_secret import *\n'
            ]
            f.writelines(py_script)
    else:
        if not os.path.exists(secret_path):
            from django.utils.crypto import get_random_string
            secret_key = get_random_string(
                50, 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
            )
            with open(secret_path, 'w') as f:
                f.write("SECRET_KEY = " + repr(secret_key) + "\n")

# Import the secret key
ensure_secret_key_file()
