# Copyright the Institute of Cryptography, Faculty of Mathematics and Computer Science at University of Havana
# contributors. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import asyncio
import logging
import os

from typing import AsyncIterable, Iterable

import grpc
import queue

from src.fabric_shim.handler import Handler
from src.fabric_shim.interfaces import Chaincode
from src.fabric_shim.logging import LOGGER
from fabric_protos_python.peer import chaincode_shim_pb2_grpc as ccshim_grpc_pb2
from fabric_protos_python.peer import chaincode_shim_pb2 as ccshim_pb2

# Coroutines to be invoked when the event loop is shutting down.
_cleanup_coroutines = []

send_queue = queue.SimpleQueue()


class ChaincodeService(ccshim_grpc_pb2.ChaincodeServicer):
    """Chaincode as a server - peer establishes a connection to the chaincode as a client
    Currently only supports a stream connection.
    """

    def __init__(self, chaincode_id: str, chaincode: Chaincode):
        self._ccid = chaincode_id
        self._cc = chaincode

    async def Connect(self, request_iterator: AsyncIterable[ccshim_pb2.ChaincodeMessage],
                    context: grpc.aio.ServicerContext) -> None: # Iterable[ccshim_pb2.ChaincodeMessage]:
        try:
            handler = Handler(self._ccid, self._cc)
            await handler.chat_with_peer(request_iterator, context)
        except asyncio.CancelledError:
            LOGGER.info("Cancelling RPC due to exhausted resources.")
            # context.abort()


def load_tls_config(key: bytes = None, cert: bytes = None, client_ca_certs: bytes = None) -> grpc.ServerCredentials:
    """
    load_tls_config loads the TLS configuration for the chaincode

    Returns:
      A grpc.ServerCredentials
    """
    client_auth = True if client_ca_certs else False
    # Loading credentials
    return grpc.ssl_server_credentials(((key, cert,),), client_ca_certs, client_auth)


def _internal_server(**kwargs) -> grpc.aio.Server:
    server = grpc.aio.server()

    key = kwargs.pop("key")
    key = os.getenv('CORE_TLS_CLIENT_KEY_PATH', key)

    cert = kwargs.pop("cert")
    cert = os.getenv('CORE_TLS_CLIENT_CERT_PATH', cert)

    address = kwargs.get("address")

    if not key or not cert:
        port = server.add_insecure_port(address)
    else:
        client_ca_certs = kwargs.pop("client_ca_certs")
        client_ca_certs = os.getenv('CORE_PEER_TLS_ROOTCERT_FILE', client_ca_certs)
        server_credentials = load_tls_config(key, cert, client_ca_certs)
        # Pass down credentials
        port = server.add_secure_port(address, server_credentials)

    ccid = kwargs.get("ccid")
    cc = kwargs.pop("cc")

    ccshim_grpc_pb2.add_ChaincodeServicer_to_server(ChaincodeService(ccid, cc), server)
    logging.info('Server is listening at port :%d', port)
    return server


async def _internal_start(server: grpc.aio.Server) -> None:
    await server.start()

    async def server_graceful_shutdown():
        logging.info("Starting graceful shutdown...")
        # Shuts down the server with 3 seconds of grace period. During the
        # grace period, the server won't accept new connections and allow
        # existing RPCs to continue within the grace period.
        await server.stop(3)

    _cleanup_coroutines.append(server_graceful_shutdown())
    await server.wait_for_termination()


def start(cc: Chaincode, cc_id: str = None, address: str = None, key: bytes = None, cert: bytes = None, client_ca_certs: bytes = None):
    """
    start the server

    address  Is the listen address of the chaincode server.
    key      TLS Private key passed to chaincode server.
    cert     TLS Certificate passed to chaincode server. Note
            that this argument is compatible with 'key' - if some
            are missing, 'TLS disabled'.
    client_ca_certs   Set if connecting peer should be verified.
    """
    cc_id = os.getenv('CHAINCODE_ID', cc_id)
    address = os.getenv('CHAINCODE_SERVER_ADDRESS', address)
    if cc_id is None or cc_id == "":
        raise Exception("cc_id must be specified")
    elif address is None or address == "":
        raise Exception("address must be specified")
    # TODO: valid
    elif isinstance(cc, Chaincode):
        raise Exception("chaincode must be specified")

    server = _internal_server(ccid=cc_id, address=address, cc=cc, key=key, cert=cert, client_ca_certs=client_ca_certs)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(_internal_start(server))
    finally:
        loop.run_until_complete(*_cleanup_coroutines)
        loop.close()
