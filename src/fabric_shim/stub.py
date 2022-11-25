# Copyright the Institute of Cryptography, Faculty of Mathematics and Computer Science at University of Havana
# contributors. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
from src.fabric_shim.interfaces import ChaincodeStubInterface
from src.fabric_shim.utils import *
from fabric_protos_python.peer import chaincode_pb2 as pb
from fabric_protos_python.common import common_pb2 as cm_pb
from fabric_protos_python.peer import proposal_pb2 as pr_pb
from fabric_protos_python import msp
from fabric_protos_python.peer import chaincode_event_pb2 as e_pb
from collections.abc import Sequence

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
        if self.signed_proposal:
            decoded_sp = {
                'signature': self.signed_proposal.getSignature()
            }

            try:
                proposal = pb.Proposal.deserializeBinary(self.signed_proposal.getProposalBytes())
                decoded_sp['proposal'] = {}
                self.proposal = proposal
            except Exception as e:
                raise Exception('Failed extracting proposal from signedProposal. ' + e)

            proposal_header = proposal.getHeader_asU8()
            if not proposal_header or len(proposal_header) == 0:
                raise Exception('Proposal header is empty')
            

            proposal_payload = proposal.getPayload_asU8()
            if not proposal_payload or len(proposal_payload) == 0:
                raise Exception('Proposal payload is empty')

            try:
                header = cm_pb.Header.deserializeBinary(proposal_header)
                decoded_sp['proposal']['header'] = {}
            except Exception as e:
                raise Exception('Could not extract the header from the proposal: ' + e)

            try:
                signature_header = cm_pb.SignatureHeader.deserializeBinary(header.getSignatureHeader())
                decoded_sp['proposal']['header']['signatureHeader'] = {'nonce': signature_header.getNonce_asU8(), 'creator_u8': signature_header.getCreator_asU8()}
            except Exception as e:
                raise Exception('Decoding SignatureHeader failed: ' + e)

            try:
                creator = msp.SerializedIdentity.deserializeBinary(signature_header.getCreator_asU8())
                decoded_sp['proposal']['header']['signatureHeader']['creator'] = creator
                self.creator = {'mspid': creator.getMspid(), 'idBytes': creator.getIdBytes_asU8()}
            except Exception as e:
                raise Exception('Decoding SerializedIdentity failed: ' + e)

            try:
                channel_header = cm_pb.ChannelHeader.deserializeBinary(header.getChannelHeader_asU8())
                decoded_sp['proposal']['header']['channelHeader'] = channel_header
                self.tx_timestamp = channel_header.getTimestamp()
            except Exception as e:
                raise Exception('Decoding ChannelHeader failed: ' + e)

            try:
                ccpp = pb.ChaincodeProposalPayload.deserializeBinary(proposal_payload)
                decoded_sp['proposal']['payload'] = ccpp
            except Exception as e:
                raise Exception('Decoding ChaincodeProposalPayload failed: %s' + e)

            self.signed_proposal = decoded_sp

    def get_channel_id(self):
        """Get the channel ID of the chaincode calling transaction"""
        return self.channel_id

    def get_tx_timestamp(self):
        """Get the timestamp of the chaincode calling transaction"""
        self.tx_timestamp

    def get_creator(self):
        """Get the user ID of the chaincode calling transaction"""
        self.creator

    def get_txid(self):
        """Get the ID of the chaincode calling transaction"""
        return self.txid

    async def get_state(self, key: str) -> bytearray:
        """Get asset state from ledger"""
        print('get_state called with key:%s' % key)
        # Access public data by setting the collection to empty string
        collection = ''
        return await self.client.handle_get_state(collection, key, self.channel_id, self.txid)

    async def put_state(self, key: str, value):
        """Put asset state to ledger"""
        print('put_state called with key:%s and value:%s' % (key, value))
        # Access public data by setting the collection to empty string
        collection = ''
        if isinstance(value, str):
            value = bytes(value)
        return await self.client.handle_put_state(collection, key, value, self.channel_id, self.txid)

    async def delete_state(self, key: str):
        """Delete asset state from ledger"""
        print('delete_state called with key:%s' % key)
        # Access public data by setting the collection to empty string
        collection = ''
        return await self.client.handle_delete_state(collection, key, self.channel_id, self.txid)

    def create_composite_key(self, object_type, attributes):
        """Creates a composite key by combining the objectType string and the given `attributes` to form a composite key"""
        validate_composite_key_attribute(object_type)
        if not isinstance(attributes, Sequence):
            raise Exception('attributes must be an array')

        composite_key = COMPOSITEKEY_NS + object_type + MIN_UNICODE_RUNE_VALUE
        for attribute in attributes:
            validate_composite_key_attribute(attribute)
            composite_key = composite_key + attribute + MIN_UNICODE_RUNE_VALUE
        return composite_key

    def split_composite_key(self, composite_key):
        object_type = None
        attributes = []
        if composite_key and len(composite_key) > 1 and composite_key[0] == COMPOSITEKEY_NS:
            split_key = composite_key[1:].split(MIN_UNICODE_RUNE_VALUE)
            object_type = split_key[0]
            split_key.pop()
            if len(split_key)  > 1:
                split_key.pop(0)
                attributes = split_key
        return (object_type, attributes)
