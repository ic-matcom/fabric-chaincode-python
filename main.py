from src.fabric_shim.interfaces import Chaincode, ChaincodeStubInterface
from src.fabric_shim.server import start
from src.fabric_shim.response import ResponseCode

import json
from fabric_protos_python.peer import proposal_response_pb2 as pb

HOST = '127.0.0.1'
PORT = 9999
address_str: str = f"{HOST}:{PORT}"
cc_id: str = "basic_1.0:7e0e2d4591aaf7b2eceeaa6a2a09faa9665fd1e961fd92840a61018a91d0d0b2"


class Asset:
    def __init__(self, id_, color, size, owner, appraised_value):
        self.id: str = id_
        self.color: str = color
        self.size: int = size
        self.owner: str = owner
        self.appraised_value: int = appraised_value


class MyChaincode(Chaincode):
    async def init(self, stub: ChaincodeStubInterface) -> pb.Response:
        await self.init_ledger(self, stub)
        return pb.Response(status=ResponseCode.OK)

    async def invoke(self, stub: ChaincodeStubInterface) -> pb.Response:
        args = [arg.decode() for arg in stub.cc_input.args]
        action = args[0]
        if action == "InitLedger":
            await self.init_ledger(self, stub)
            return pb.Response(status=ResponseCode.OK)
        if action == "CreateAsset" or action == "UpdateAsset":
            create_inputs = args[1:]
            new_asset = Asset(
                create_inputs[0],
                create_inputs[1],
                create_inputs[2],
                create_inputs[3],
                create_inputs[4])
            await self.create_asset(self, stub, new_asset)
            return pb.Response(status=ResponseCode.OK)
        if action == "ReadAsset":
            asset_id = args[1]
            result = await self.read_asset(self, stub, asset_id)
            return pb.Response(status=ResponseCode.OK, message=result)
        if action == "DeleteAsset":
            asset_id = args[1]
            await self.delete_state(self, stub, asset_id)
            return pb.Response(status=ResponseCode.OK)

        return pb.Response(status=ResponseCode.ERROR)

    async def init_ledger(self, stub: ChaincodeStubInterface):
        init_ledger_values = [
            Asset("asset1", "blue", 5, "Tomoko", 300),
            Asset("asset2", "red", 5, "Brad", 400),
            Asset("asset3", "green", 10, "Jin Soo", 500)
        ]

        for asset in init_ledger_values:
            await self.create_asset(self, stub, asset)

    async def create_asset(self, stub: ChaincodeStubInterface, asset: Asset):
        await stub.put_state(asset.id, json.dumps(asset.__dict__))

    async def read_asset(self, stub: ChaincodeStubInterface, key: str):
        return await stub.get_state(key)

    async def delete_state(self, stub: ChaincodeStubInterface, key: str):
        await stub.delete_state(key)


if __name__ == '__main__':
    mycc = MyChaincode
    start(cc_id, address_str, mycc)
    # from fabric_protos_python.peer import transaction_pb2 as tx_pb2

    # print("-->> ", tx_pb2.MetaDataKeys.VALIDATION_PARAMETER)
