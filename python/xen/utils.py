from fractions import Fraction 

def isInteger(num):
    if isinstance(num, int):
        return True
    if isinstance(num, float):
        return num.is_integer()
    if isinstance(num, Fraction):
        return num.denominator == 1