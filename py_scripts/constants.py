import os
from pathlib import Path

CWD = os.getcwd()
HOME = str(Path.home())

TESTNET_MAGIC = "42"
PROTOCOL_PARAMS_FILENAME = "protocol-params.json"
PROTOCOL_PARAMS_FILEPATH = os.path.join(CWD, PROTOCOL_PARAMS_FILENAME)
NODE_SOCKET_PATH = os.path.join(HOME, "shelley_testnet/db/node.socket")
