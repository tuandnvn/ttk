BEFORE = 'BEFORE'
AFTER = 'AFTER'
INCLUDES = 'INCLUDES' 
IS_INCLUDED = 'IS_INCLUDED'
DURING = 'DURING'
DURING_INV = 'DURING_INV'
SIMULTANEOUS = 'SIMULTANEOUS'
IBEFORE = 'IBEFORE'
IAFTER  = 'IAFTER'
IDENTITY = 'IDENTITY'
BEGINS = 'BEGINS'
ENDS = 'ENDS'
BEGUN_BY = 'BEGUN_BY'
ENDED_BY = 'ENDED_BY'
NORELATION = 'NORELATION'

identities = [IDENTITY, SIMULTANEOUS]
standards = [BEFORE, INCLUDES, DURING, IBEFORE, BEGINS, BEGUN_BY] 
reverses = [AFTER, IS_INCLUDED, DURING_INV, IAFTER, ENDS, ENDED_BY]

def get_standard ( relType ):
    if relType in standards or relType in identities:
        return relType, True
    try:
        pos = reverses.index(relType)
        return standards[pos], False
    except ValueError:
        raise Exception('unknown relType')

def reverse(relType):
    if relType in identities:
        return relType
    if relType in standards:
        return reverses[standards.index(relType)]
    if relType in reverses:
        return standards[reverses.index(relType)]
    raise Exception('unknown relType')