#!/bin/bash

TESTNET_MAGIC=42
CWD=$PWD
genesisfile="./shelley_testnet_genesis.json"

slotLength=$(cat ${genesisfile} | jq -r .slotLength) #In Secs
epochLength=$(cat ${genesisfile} | jq -r .epochLength) #In Secs
slotsPerKESPeriod=$(cat ${genesisfile} | jq -r .slotsPerKESPeriod) #Number
startTimeGenesis=$(cat ${genesisfile} | jq -r .systemStart) #In Text
startTimeSec=$(date --date=${startTimeGenesis} +%s) #In Secs(abs)
transTimeEnd=$(( ${startTimeSec}+(2*${epochLength}) )) #In Secs(abs) End of the transPhase(2 Epochs)
transSlots=$(( (2*${epochLength}) / 20 )) #NumSlots in the TransitionPhase(2 Epochs)


get_referenceSlot() {
	local currentTimeSec=$(date -u +%s) #in seconds (UTC)
	#Calculate current slot
	if [[ "${currentTimeSec}" -lt "${transTimeEnd}" ]];
			then #In Transistion Phase between ShelleyGenesisStart and TransitionEnd
			local currentSlot=$(( ${byronSlots} + (${currentTimeSec}-${startTimeSec}) / 20 ))
			else #After Transition Phase
			local currentSlot=$(( ${byronSlots} + ${transSlots} + ((${currentTimeSec}-${transTimeEnd}) / ${slotLength}) ))
	fi
	echo ${currentSlot}
}

get_currentKESPeriod() {
	local currentTimeSec=$(date -u +%s) #in seconds (UTC)
	local currentKES=$(( (${currentTimeSec}-${transTimeEnd}) / (${slotsPerKESPeriod}*${slotLength}) ))
	if [[ "${currentKES}" -lt 0 ]]; then currentKES=0; fi
	echo ${currentKES}
}

#Current KES Period
currentKESPeriod=$(get_currentKESPeriod)
echo "Current KES Period: ${currentKESPeriod}"
echo "slotLength: ${slotLength}"
echo "epochLength: ${epochLength}"
echo "slotsPerKESPeriod: ${slotsPerKESPeriod}"
echo "startTimeGenesis: ${startTimeGenesis}"
echo "startTimeSec: ${startTimeSec}"
echo "transTimeEnd: ${transTimeEnd}"
echo "transSlots: ${transSlots}"


cardano-cli shelley node key-gen-KES \
	--verification-key-file $CWD/pool_kes.vkey \
	--signing-key-file $CWD/pool_kes.skey

cardano-cli shelley node key-gen-VRF \
	--verification-key-file $CWD/pool_vrf.vkey \
	--signing-key-file $CWD/pool_vrf.skey
	
cardano-cli shelley node key-gen \
	--verification-key-file $CWD/pool_cold.vkey \
	--signing-key-file $CWD/pool_cold.skey \
	--operational-certificate-issue-counter $CWD/pool_cold.counter
	
cardano-cli shelley node issue-op-cert \
	--kes-verification-key-file $CWD/pool_kes.vkey \
	--cold-signing-key-file $CWD/pool_cold.skey \
	--operational-certificate-issue-counter $CWD/pool_cold.counter \
	--kes-period ${currentKESPeriod} \
	--out-file $CWD/pool.opcert


