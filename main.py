from src.fabric_shim.interfaces import Chaincode, ChaincodeStubInterface
from src.fabric_shim.server import start

from fabric_protos_python.peer import proposal_response_pb2 as pb

HOST = '127.0.0.1'
PORT = 9999
address_str: str = f"{HOST}:{PORT}"
cc_id: str = "basic_1.0:6f953644cba819469faf754a24e6a839b3065703a0e55d559e419de3c6361a9d"


class MyChaincode(Chaincode):
    def init(self, stub: ChaincodeStubInterface) -> pb.Response:
        pass

    def invoke(self, stub: ChaincodeStubInterface) -> pb.Response:
        pass


if __name__ == '__main__':
    mycc = MyChaincode
    start(cc_id, address_str, mycc)
    # from fabric_protos_python.peer import transaction_pb2 as tx_pb2

    # print("-->> ", tx_pb2.MetaDataKeys.VALIDATION_PARAMETER)
