from mee6.utils.logger import Logger

def chunk(l, n):
    l = list(l)
    return [l[i:i+n] for i in range(0, len(l), n)]


import string
digs = string.digits + string.ascii_letters
def int2base(x, base):
    if x == 0: return digs[0]

    digits = []

    while x:
        digits.append(digs[x % base])
        x //= base

    digits.reverse()

    return ''.join(digits)

def get(obj, attr, default=None):
    try:
        return getattr(obj, attr)
    except AttributeError:
        return default
