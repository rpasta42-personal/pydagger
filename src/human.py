"""This is a utility module used to house measurement conversions from
bytes to human readable versions"""

def fromBytes(nbytes):
    """Converts the provided number of bytes into human readable counterparts"""

    if nbytes == 0:
        return '0 B'
        
    idx = 0
    while nbytes >= 1024 and idx < len(suffixes) - 1:
        nbytes /= 1024.
        idx += 1

    fval = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (fval, suffixes[idx])
