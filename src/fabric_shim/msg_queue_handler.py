import asyncio
from src.fabric_shim.utils import *

class QueueMessage:
    def __init__(self, msg, method, future: asyncio.Future) -> None:
        self.msg = msg
        self.method = method
        self.future = future

    def get_msg(self):
        return self.msg

    def get_msg_txContextId(self):
        return self.msg.getChannelId() + self.msg.getTxid()

    def get_method(self):
        return self.method

    def success(self, response):
        self.future.set_result(response)

    def fail(self, err):
        self.future.set_exception(Exception(err))

class MsgQueueHandler:
    """This class handles queuing messages to be sent to the peer based on transaction id"""
    
    def __init__(self, handler, context) -> None:
        self.handler = handler
        self.tx_queues = {}
        self.context = context

    def queue_msg(self, msg: QueueMessage):
        """Queue a message to be sent to the peer"""
        tx_context_id = msg.get_msg_txContextId()
        try:
            self.tx_queues[tx_context_id]
        except KeyError:
            self.tx_queues[tx_context_id] = []

        msg_queue = self.tx_queues[tx_context_id]
        msg_queue.append(msg)
        if len(msg_queue) == 1:
            self.__send_msg(tx_context_id)

    def __send_msg(self, tx_context_id):
        """send the current message to the peer"""
        msg: QueueMessage = self.__getCurrentMsg(tx_context_id)
        if msg:
            try:
                self.context.write(msg.get_msg())
            except Exception as e:
                msg.fail(e)

    def handle_msg_response(self, response):
        tx_id = response.tx_id
        channel_id = response.channel_id
        tx_context_id = channel_id + tx_id
        msg: QueueMessage = self.__get_current_msg(tx_context_id)

        if msg:
            try:
                parsed_response = parse_response(self.handler, response, msg.get_method())
                msg.success(parsed_response)
            except Exception as e:
                msg.fail(e)
            self.__remove_current_and_send_next(tx_context_id)

    def __get_current_msg(self, tx_context_id):
        """returns the message at the top of the queue for the particular transaction"""
        msg_queue = self.tx_queues[tx_context_id]
        if msg_queue:
            return msg_queue[0]
        
        print('Failed to find a message for transaction context id %s' % tx_context_id)

    def __remove_current_and_send_next(self, tx_context_id):
        """Remove the current message and send the next message in the queue if there is one"""
        msg_queue = self.tx_queues[tx_context_id]
        if msg_queue and msg_queue.length > 0:
            msg_queue.pop(0)
            if len(msg_queue) != 0:
                self.__send_msg(tx_context_id)
                