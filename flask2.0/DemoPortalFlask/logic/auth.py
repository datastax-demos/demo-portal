import binascii
import hashlib
import os
import re


def hash(input_value, seed):
    dk = hashlib.pbkdf2_hmac('sha256', input_value[:1024], seed, 100000)
    return binascii.hexlify(dk)


def create_new_password():
    return hashlib.md5(os.urandom(1000)).hexdigest()


def is_valid_domain(email, domain):
    pattern = re.compile(r'(\w*\.*\w*)@(%s)' % domain)
    found = pattern.findall(email)
    if found:
        safe_email = '%s@%s' % (found[0][0], found[0][1])
        return safe_email
    return None
