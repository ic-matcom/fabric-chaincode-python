# Copyright the Institute of Cryptography, Faculty of Mathematics and Computer Science at University of Havana
# contributors. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
from src.fabric_shim.interfaces import ChaincodeStubInterface

VALIDATION_PARAMETER: str = 'VALIDATION_PARAMETER'


class ChaincodeStub(ChaincodeStubInterface):
    """The stub encapsulates the APIs between the chaincode implementation and the Fabric peer"""

    def __init__(self, client, channel_id, txid, input, signed_proposal_pb):
        self.client = client
        self.channel_id = channel_id
        self.txid = txid
        self.input = input
        self.signed_proposal_pb = signed_proposal_pb
        self.validationParameterMetakey = VALIDATION_PARAMETER

        # signed_proposal_pb is a legitimate one, meaning it is an internal call to system chaincodes.
        if self.signed_proposal_pb is not None:
            pass

    def get_state(self, key: str) -> bytearray:
        pass

    def get_function_and_parameters(self):  # Get the chaincode calling method name and parameter list
        pass

    def get_txid(self):  # Get the ID of the chaincode calling transaction
        pass

    def get_channel_id(self):  # Get the channel ID of the chaincode calling transaction
        pass

    def get_creator(self):  # Get the user ID of the chaincode calling transaction
        pass

    def get_transient(self):  # Get the transient dataset of chaincode call transactions
        pass

    def get_tx_timestamp(self):  # Get the timestamp of the chaincode calling transaction
        pass
