import hashlib
import re
import datetime


def validate(email, password, seed):
    return create(email, seed) == password

def create(email, seed):
    # rotate the hash once a week
    date = datetime.date.today()
    date = date.isocalendar()[0] + date.isocalendar()[1]

    generated_hash = hashlib.md5(seed[:8] +
                                 email.encode('utf-8') +
                                 seed[8:] +
                                 str(date))
    return generated_hash.hexdigest()[:6]

def validdomain(email, domain):
    pattern = re.compile(r'(\w*\.*\w*)@(%s)' % domain)
    found = pattern.findall(email)
    if found:
        safe_email = '%s@%s' % (found[0][0], found[0][1])
        return safe_email
    return None
