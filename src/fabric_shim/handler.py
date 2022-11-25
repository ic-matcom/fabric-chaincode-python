# handler.py

# Copyright the Institute of Cryptography, Faculty of Mathematics and Computer Science at University of Havana
# contributors. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# ChaincodeSupportClient Class

# The main API list of ChaincodeSupportClient is as follows:
#
#      chat_with_peer(): Starts a two-way communication flow with the peer node

import datetime
import asyncio
from typing import AsyncIterable

import grpc
from google.protobuf.message import DecodeError

from src.fabric_shim.interfaces import Chaincode
from src.fabric_shim.logging import LOGGER
from src.fabric_shim.response import new_error_msg
from src.fabric_shim.utils import ResponseCode
from src.fabric_shim.stub import ChaincodeStub
from src.fabric_shim.msg_queue_handler import MsgQueueHandler, QueueMessage
from fabric_protos_python.peer import chaincode_shim_pb2 as ccshim_pb2
from fabric_protos_python.peer import chaincode_pb2 as cc_pb2


class STATES:
    CREATED = "created"  # start state
    ESTABLISHED = "established"  # connection established
    READY = "ready"  # ready for requests


MIN_UNICODE_RUNE_VALUE = '\u0000'  # U + 0000
MAX_UNICODE_RUNE_VALUE = '\u0010FFFF'  # U+10FFFF - maximum (and unallocated) code point
COMPOSITEKEY_NS = '\x00'
EMPTY_KEY_SUBSTITUTE = '\x01'

STATE = STATES.CREATED

class Handler:
    def __init__(self, cc_id: str, cc: Chaincode) -> None:
        self.chaincode_id = cc_pb2.ChaincodeID()
        self.chaincode_id.name = cc_id
        self.chaincode = cc

    def handle_stub_interaction(self, msg, action="Invoke"):
        """handle_message calls the Init | Invoke function of the associated chaincode."""
        # Get the function and args from Payload
        cc_input = cc_pb2.ChaincodeInput()
        try:
            cc_input.ParseFromString(msg)
        except DecodeError as e:
            raise Exception(e)
        
        try:
            stub = ChaincodeStub(self, msg.channel_id, msg.txid, cc_input, msg.proposal)
        except Exception as e:
            raise Exception('Failed to construct a chaincode stub instance from message: %s' % e)

        if action == 'init':
            resp = self.chaincode.init(stub)
            method = 'Init'
        else:
            resp = self.chaincode.invoke(stub)
            method = 'Invoke'

        # check that a response object has been returned otherwise assume an error.

        if not resp or not resp.status:
            errMsg = '%s Calling chaincode %s() has not called success or error.' % (msg.logging_prefix(), method)
            print(errMsg)

            resp = {
                status: ResponseCode.ERROR,
                message: errMsg
            }
        
        print('%s Calling chaincode %s(), response status: %s' % (msg.logging_prefix(), method, resp.status))

        response = { message: resp.message, status: resp.status, payload: resp.payload }

        if resp.status >= ResponseCode.ERROR:
            errMsg = '%s Calling chaincode %s() returned error response [%s]. Sending COMPLETED message back to peer' % (msg.logging_prefix(), method, resp.message)
            print(errMsg)

            nextStateMsg = ccshim_pb2.ChaincodeMessage(
                type = ccshim_pb2.ChaincodeMessage.COMPLETED,
                payload = response.serializeBinary(),
                txid = msg.txid,
                channel_id = msg.channel_id,
                chaincode_event = stub.chaincodeEvent
            )
        else:
            print('%s Calling chaincode %s() succeeded. Sending COMPLETED message back to peer' % (msg.logging_prefix(), method))

            nextStateMsg = ccshim_pb2.ChaincodeMessage(
                type = ccshim_pb2.ChaincodeMessage.COMPLETED,
                payload = response.serializeBinary(),
                txid = msg.txid,
                channel_id = msg.channel_id,
                chaincode_event = stub.chaincodeEvent
            )

        return nextStateMsg


    def handle_message_ready(self, msg):
        """handle_message_ready handles messages received from the peer when the handler is in the "ready" state."""
        if msg.type == ccshim_pb2.ChaincodeMessage.RESPONSE or msg.type == ccshim_pb2.ChaincodeMessage.ERROR:
            LOGGER.info("+++ ERROR or RESPONSE +++")
            raise Exception("+++ ERROR or RESPONSE +++")
        elif msg.type == ccshim_pb2.ChaincodeMessage.INIT:
            LOGGER.info("+++ call INIT +++")
            return
        elif msg.type == ccshim_pb2.ChaincodeMessage.TRANSACTION:
            LOGGER.info("+++ call INVOKE +++")
            return
        else:
            return new_error_msg(msg, STATE)


    def handle_message_established(self, msg):
        """
        handle_message_established handles messages received from the peer when the handler is in the "established" state.
        """
        global STATE
        if msg.type != ccshim_pb2.ChaincodeMessage.READY:
            # context.abort()
            LOGGER.error(f'Chaincode is in "ready" state, can only process messages of type "established", '
                        f'but received "{msg.type}"')
            return new_error_msg(msg, STATE)
        else:
            LOGGER.info('Successfully established communication with peer node. State transferred to "ready"')
            STATE = STATES.READY


    def handle_message_created(self, msg):
        """handle_message_created handles messages received from the peer when the handler is in the "created" state."""
        global STATE
        if msg.type != ccshim_pb2.ChaincodeMessage.REGISTERED:
            # can not process any message other than "registered"
            # from the peer when in "created" state
            # send an error message telling the peer about this
            LOGGER.error(f'Chaincode is in "created" state, can only process messages of type "registered", '
                        f'but received "{msg.type}"')
            return new_error_msg(msg, STATE)
        else:
            LOGGER.info('Successfully registered with peer node. State transferred to "established"')
            STATE = STATES.ESTABLISHED


    def handle_message(self, msg: ccshim_pb2.ChaincodeMessage):
        """handle_message message handles loop for shim side of chaincode/peer stream."""
        LOGGER.warning('-->> Look out!')
        global STATE

        if msg.type == ccshim_pb2.ChaincodeMessage.KEEPALIVE:
            LOGGER.info('-| KEEPALIVE')
            return self.serial_send_async(msg)

        if STATE == STATES.READY:
            self.handle_message_ready(msg)
        elif STATE == STATES.ESTABLISHED:
            self.handle_message_established(msg)
        elif STATE == STATES.CREATED:
            self.handle_message_created(msg)
        else:
            return new_error_msg(msg, STATE)


    # TODO: basado en la biblioteca de go -- analizar luego su implementacion --
    def serial_send_async(self, msg: ccshim_pb2.ChaincodeMessage):
        """
        serial_send_async sends the provided message asynchronously in a separate
        goroutine. The result of the send is communicated back to the caller via
        errc.
        """
        yield msg


    async def chat_with_peer(self, stream: AsyncIterable[ccshim_pb2.ChaincodeMessage], context: grpc.aio.ServicerContext):
        """chat stream for peer-chaincode interactions post connection"""
        global STATE
        STATE = STATES.CREATED

        self.msg_queue_handler = MsgQueueHandler(self, context)

        # Send the ChaincodeID during register.
        cm = ccshim_pb2.ChaincodeMessage(type=ccshim_pb2.ChaincodeMessage.REGISTER,
                                        payload=self.chaincode_id.SerializeToString())
        cm.timestamp.FromDatetime(datetime.datetime.now())

        # Register on the stream
        await context.write(cm)
        # send_queue.put(cm)

        async for receive_message in stream:
            if receive_message is None:
                err_str = "received nil message, ending chaincode stream"
                LOGGER.error(err_str)
                return ccshim_pb2.ChaincodeMessage(type=ccshim_pb2.ChaincodeMessage.ERROR,
                                                payload=err_str.encode(encoding='utf-8'))
            else:
                self.handle_message(receive_message)

                LOGGER.info(f'->>>>  proposal  {receive_message.proposal}')
                LOGGER.info(f'->>>>  payload  {receive_message.payload}')
                LOGGER.info(f'->>>>  channel ID  {receive_message.channel_id}')
                LOGGER.info(f'->>>>  Tx ID  {receive_message.txid}')

    async def handle_get_state(self, collection, key, channel_id, tx_id):
        msg_pb = cc_pb2.GetState()
        msg_pb.setKey(key)
        msg_pb.setCollection(collection)
        msg = ccshim_pb2.ChaincodeMessage(
            type = ccshim_pb2.ChaincodeMessage.GET_STATE,
            payload = msg_pb.serializeBinary(),
            txid = tx_id,
            channel_id = channel_id
        )
        print('handle_get_state - with key:' + key)
        return await self.__ask_peer_and_listen(msg, 'GetState')
    
    async def handle_put_state(self, collection, key, value, channel_id, tx_id):
        msg_pb = cc_pb2.PutState()
        msg_pb.setKey(key)
        msg_pb.setValue(value)
        msg_pb.setCollection(collection)
        msg = ccshim_pb2.ChaincodeMessage(
            type = ccshim_pb2.ChaincodeMessage.PUT_STATE,
            payload = msg_pb.serializeBinary(),
            txid = tx_id,
            channel_id = channel_id
        )
        return await self.__ask_peer_and_listen(msg, 'PutState')

    async def handle_delete_state(self, collection, key, channel_id, tx_id):
        msg_pb = cc_pb2.DelState()
        msg_pb.setKey(key)
        msg_pb.setCollection(collection)
        msg = ccshim_pb2.ChaincodeMessage(
            type = ccshim_pb2.ChaincodeMessage.DEL_STATE,
            payload = msg_pb.serializeBinary(),
            txid = tx_id,
            channel_id = channel_id
        )
        return await self.__ask_peer_and_listen(msg, 'DeleteState')
    
    def __ask_peer_and_listen(self, msg, action):
        loop = asyncio.get_running_loop()
        fut = loop.create_future()

        message = QueueMessage(msg, action, fut)
        self.msg_queue_handler.queue_msg(message)

        # TODO: fix
        return (await fut)
