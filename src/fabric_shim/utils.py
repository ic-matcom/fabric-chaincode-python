# Auxiliary tools

def enum_type(*sequential, **named) -> type:
    """enum other than class Enum. better performance

    Typical usage example:
        >> Numbers = enum('ZERO', 'ONE', 'TWO')
        >> Numbers.ZERO
        0
    or:
        >> Numbers = enum_type(ONE=1, TWO=2, THREE='three')
        >> Numbers.THREE
        'three'
    Args:
        sequential: Collects all the positional arguments in a tuple.
        named: Collects all the keyword arguments in a dictionary.

    """
    print(sequential, ": ", named)
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

class ResponseCode:
    OK = 200,
    ERROR_THRESHOLD = 400,
    ERROR = 500
