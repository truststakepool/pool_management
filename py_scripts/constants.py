import os

CWD = os.getcwd()

print(f"CWD: {CWD}")

TESTNET_MAGIC = 42
PROTOCOL_PARAMS_FILENAME = "protocol-params.json"
PROTOCOL_PARAMS_FILEPATH = os.path.join(CWD, PROTOCOL_PARAMS_FILENAME)

print(f"PROTOCOL_PARAMS_FILEPATH: {PROTOCOL_PARAMS_FILEPATH}")

NODE_SOCKET_PATH = os.path.join(CWD, "shelley_testnet/db/node.socket")

print(f"NODE_SOCKET_PATH: {NODE_SOCKET_PATH}")
