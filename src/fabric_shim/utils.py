# Auxiliary tools
from fabric_protos_python.peer import chaincode_shim_pb2 as ccshim_pb2

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

MIN_UNICODE_RUNE_VALUE = '\u0000'
COMPOSITEKEY_NS = '\x00'

def validate_composite_key_attribute(attr):
    if attr is None or not isinstance(attr, str) or len(attr) == 0:
        raise Exception('object type or attribute not a non-zero length string')

def validate_simple_keys(keys):
    for key in keys:
        if key and isinstance(key, str) and key[0] == COMPOSITEKEY_NS:
            raise Exception('first character of the key %s contains a null character which is not allowed' % key)
        
def generate_logging_prefix(channel_id, tx_id):
    return '[%s-%s]' % (channel_id, tx_id)

# TODO: Fill methods
def parse_response(handler, res, method):
    logger_prefix = generate_logging_prefix(res.channel_id, res.txid)

    if res.type == ccshim_pb2.ChaincodeMessage.RESPONSE:
        print('%s Received %s() successful response' % (logger_prefix, method))

        if method == 'GetStateByRange':
            pass
        elif method == 'GetQueryResult':
            # return handleGetQueryResult(handler, res, method)
            pass
        elif method == 'GetHistoryForKey':
            #return handleGetHistoryQueryResult(handler, res)
            pass
        elif method == 'QueryStateNext':
            pass
        elif method == 'QueryStateClose':
            return ccshim_pb2.QueryResponse.deserializeBinary(res.payload)
        elif method == 'InvokeChaincode':
            return ccshim_pb2.ChaincodeMessage.deserializeBinary(res.payload)
        elif method == 'GetStateMetadata':
            #return handleGetStateMetadata(res.payload)
            pass
        return bytes(res.payload)
    elif res.type == ccshim_pb2.ChaincodeMessage.ERROR:
        print('%s Received %s() error response' % (logger_prefix, method))
        raise Exception(res.payload.toString())
    else:
        err_msg = '%s Received incorrect chaincode in response to the %s() call: type="%s", expecting "RESPONSE"' % (logger_prefix, method, res.type)
        print(err_msg)
        raise Exception(err_msg)


