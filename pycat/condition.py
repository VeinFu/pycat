#! /usr/bin/python

#--------------------------------------------------------------------------
# Default Comparing Functions
#
# All comparing functions are named as
#     datetype_operation(valuea, valueb)
# valuea and valueb should be formed in string. The comparing functions can
# translate them into proper type.
# 
#--------------------------------------------------------------------------

def int_less_than(vala, valb):
    vala = int(vala)
    valb = int(valb)
    if vala < valb:
        return True
    else:
        return False

def int_less_equal(vala, valb):
    vala = int(vala)
    valb = int(valb)
    if vala <= valb:
        return True
    else:
        return False

def int_equal(vala, valb):
    vala = int(vala)
    valb = int(valb)
    if vala == valb:
        return True
    else:
        return False

def int_not_equal(vala, valb):
    vala = int(vala)
    valb = int(valb)
    if vala != valb:
        return True
    else:
        return False

def int_greater_than(vala, valb):
    vala = int(vala)
    valb = int(valb)
    if vala > valb:
        return True
    else:
        return False

def int_greater_equal(vala, valb):
    vala = int(vala)
    valb = int(valb)
    if vala >= valb:
        return True
    else:
        return False

def float_less_than(vala, valb):
    vala = float(vala)
    valb = float(valb)
    if vala < valb:
        return True
    else:
        return False

def float_less_equal(vala, valb):
    vala = float(vala)
    valb = float(valb)
    if vala <= valb:
        return True
    else:
        return False

def float_equal(vala, valb):
    vala = float(vala)
    valb = float(valb)
    if vala == valb:
        return True
    else:
        return False

def float_not_equal(vala, valb):
    vala = float(vala)
    valb = float(valb)
    if vala != valb:
        return True
    else:
        return False


def float_greater_than(vala, valb):
    vala = float(vala)
    valb = float(valb)
    if vala > valb:
        return True
    else:
        return False

def float_greater_equal(vala, valb):
    vala = float(vala)
    valb = float(valb)
    if vala >= valb:
        return True
    else:
        return False

def string_equal(vala, valb):
    assert isinstance(vala, str)
    assert isinstance(valb, str)
    if vala == valb:
        return True
    else:
        return False

def string_not_equal(vala, valb):
    assert isinstance(vala, str)
    assert isinstance(valb, str)
    if vala != valb:
        return True
    else:
        return False

def binary_equal(vala, valb):
    """
        Example:
        vala:   0b00010101
        valb:   0b00x101xx
        mask:     11011100
        expect:   00010100
        vala & mask == expect
    """
    assert isinstance(vala, str)
    assert isinstance(valb, str)
    mask = valb[2:].replace("0", "1").replace("x", "0")
    highbits = len(vala) - 2 - len(mask)
    if highbits > 0:
        mask = "1" * highbits + mask
    mask = int(mask, 2)
    expect = int(valb[2:].replace("x", "0"), 2)
    vala = int(vala, 2)
    if vala & mask == expect:
        return True
    else:
        return False

def binary_not_equal(vala, valb):
    assert isinstance(vala, str)
    assert isinstance(valb, str)
    mask = valb[2:].replace("0", "1").replace("x", "0")
    highbits = len(vala) - 2 - len(mask)
    if highbits > 0:
        mask = "1" * highbits + mask
    mask = int(mask, 2)
    expect = int(valb[2:].replace("x", "0"), 2)
    vala = int(vala, 2)
    if vala & mask != expect:
        return True
    else:
        return False

COMPARE_FUNCS = {
    ("int", "less-than"): int_less_than,
    ("int", "less-equal"): int_less_equal,
    ("int", "equal"): int_equal,
    ("int", "not-equal"): int_not_equal,
    ("int", "greater-than"): int_greater_than,
    ("int", "greater-equal"): int_greater_equal,
    ("float", "less-than"): float_less_than,
    ("float", "less-equal"): float_less_equal,
    ("float", "equal"): float_equal,
    ("float", "not-equal"): float_not_equal,
    ("float", "greater-than"): float_greater_than,
    ("float", "greater-equal"): float_greater_equal,
    ("string", "equal"): string_equal,
    ("string", "not-equal"): string_not_equal,
    ("binary", "equal"): binary_equal,
    ("binary", "not-equal"): binary_not_equal
}

#--------------------------------------------------------------------------
# Condition Class
#
#
#--------------------------------------------------------------------------

"""
valdict = {
"current": "00",
"default": "01",
"x":"02",
"y":"03"
}

cond = ConditionSet("and")
cond1 = CompareCond("int", "less-than", "current", "default")
cond2 = CompareCond("int", "equal", "x", "y")
cond.append(cond1, cond2)
cond.is_satisfied(valdict)
"""
class Condition(object):
    def __init__(self):
        pass

    def is_satisfied(value_dict):
        pass

class ConditionSet(Condtion):
    def __init__(self, logic_type):
        pass

class CompareCond(Condition):
    def __init__(self, datetype, operation, vala, valb):
        pass


