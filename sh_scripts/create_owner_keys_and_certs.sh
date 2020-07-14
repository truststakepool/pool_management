#!/bin/bash

CWD=$PWD
TESTNET_MAGIC=42

cardano-cli shelley address key-gen \
	--verification-key-file $CWD/owner.vkey \
	--signing-key-file $CWD/owner.skey
	
cardano-cli shelley address build \
	 --payment-verification-key-file $CWD/owner.vkey \
	 --testnet-magic ${TESTNET_MAGIC} \
	 --out-file owner.addr
	
cardano-cli shelley stake-address key-gen \
	--verification-key-file $CWD/owner_stake.vkey \
	--signing-key-file $CWD/owner_stake.skey

cardano-cli shelley stake-address build \
	--stake-verification-key-file $CWD/owner_stake.vkey \
	--testnet-magic ${TESTNET_MAGIC} \
	--out-file owner_stake.addr

cardano-cli shelley stake-address registration-certificate \
	--stake-verification-key-file $CWD/owner_stake.vkey \
	--out-file $CWD/owner_stake.reg.cert


