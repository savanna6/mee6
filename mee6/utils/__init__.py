from mee6.utils.logger import Logger

def chunk(l, n):
    l = list(l)
    return [l[i:i+n] for i in range(0, len(l), n)]
