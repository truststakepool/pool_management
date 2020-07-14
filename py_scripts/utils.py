import json
import pathlib
import re
import shutil
import subprocess
import os
from time import sleep

from py_scripts.constants import TESTNET_MAGIC, NODE_SOCKET_PATH, PROTOCOL_PARAMS_FILEPATH


def delete_folder(location_offline_tx_folder):
    print(f"====== Removing the {location_offline_tx_folder} folder...")
    if os.path.exists(location_offline_tx_folder) and os.path.isdir(location_offline_tx_folder):
        try:
            shutil.rmtree(location_offline_tx_folder)
        except OSError as e:
            print("!!! Error: %s - %s." % (e.filename, e.strerror))
    else:
        print(f"Folder does not exists - {location_offline_tx_folder}")


def set_node_socket_path_env_var():
    os.environ['CARDANO_NODE_SOCKET_PATH'] = NODE_SOCKET_PATH


def create_payment_key_pair(location, key_name):
    try:
        cmd = "cardano-cli shelley address key-gen" + \
              " --verification-key-file " + location + "/" + key_name + ".vkey" + \
              " --signing-key-file " + location + "/" + key_name + ".skey"
        subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
        return location + "/" + key_name + ".vkey", location + "/" + key_name + ".skey"
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode,
                                                                                 ' '.join(str(e.output).split())))


def build_payment_address(location, addr_name):
    try:
        cmd = "cardano-cli shelley address build" + \
              " --payment-verification-key-file " + location + "/" + addr_name + ".vkey" + \
              " --testnet-magic " + TESTNET_MAGIC + \
              " --out-file " + location + "/" + addr_name + ".addr"
        subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
        return read_address_from_file(location, addr_name + ".addr")
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode,
                                                                                 ' '.join(str(e.output).split())))


def create_payment_key_pair_and_address(location, addr_name):
    addr_vkey, addr_skey = create_payment_key_pair(location, addr_name)
    addr = build_payment_address(location, addr_name)
    return addr, addr_vkey, addr_skey


def create_stake_key_pair(location, key_name):
    try:
        cmd = "cardano-cli shelley stake-address key-gen" + \
              " --verification-key-file " + location + "/" + key_name + "_stake.vkey" + \
              " --signing-key-file " + location + "/" + key_name + "_stake.skey"
        subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
        return location + "/" + key_name + "_stake.vkey", location + "/" + key_name + "_stake.skey"
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode,
                                                                                 ' '.join(str(e.output).split())))


def build_stake_address(location, addr_name):
    try:
        cmd = "cardano-cli shelley stake-address build" \
              " --stake-verification-key-file " + location + "/" + addr_name + "_stake.vkey" + \
              " --testnet-magic " + TESTNET_MAGIC + \
              " --out-file " + location + "/" + addr_name + "_stake.addr"
        subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
        return read_address_from_file(location, addr_name + "_stake.addr")
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode,
                                                                                 ' '.join(str(e.output).split())))


def delegate_stake_address(stake_addr_skey_file, pool_id, delegation_fee):
    try:
        cmd = "cardano-cli shelley stake-address delegate" \
              " --signing-key-file " + stake_addr_skey_file + \
              " --pool-id " + pool_id + \
              " --delegation-fee " + str(delegation_fee)
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
        if "runStakeAddressCmd" in result:
            print(f"ERROR: command not implemented yet;\n\t- command: {cmd} \n\t- result: {result}")
            exit(2)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode,
                                                                                 ' '.join(str(e.output).split())))


def get_stake_address_info(stake_addr):
    try:
        cmd = "cardano-cli shelley query stake-address-info" \
              " --address " + stake_addr + \
              " --testnet-magic " + TESTNET_MAGIC
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
        output_json = json.loads(output)

        print(f"output_json: {output_json}")

        delegation = output_json[stake_addr]['delegation']
        reward_account_balance = output_json[stake_addr]['rewardAccountBalance']

        print(f"delegation: {delegation}")
        print(f"reward_account_balance: {reward_account_balance}")

        return delegation, reward_account_balance
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode,
                                                                                 ' '.join(str(e.output).split())))


def create_stake_key_pair_and_address(location, addr_name):
    stake_addr_vkey, stake_addr_skey = create_stake_key_pair(location, addr_name)
    stake_addr = build_stake_address(location, addr_name)
    return stake_addr, stake_addr_vkey, stake_addr_skey


def create_stake_addr_registration_cert(location, stake_addr_vkey_file, addr_name):
    try:
        suffix_str = "_stake.reg.cert"
        cmd = "cardano-cli shelley stake-address registration-certificate" \
              " --stake-verification-key-file " + stake_addr_vkey_file + \
              " --out-file " + location + "/" + addr_name + suffix_str
        subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
        return location + "/" + addr_name + suffix_str
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode,
                                                                                 ' '.join(str(e.output).split())))


def create_stake_addr_delegation_cert(location, stake_addr_vkey_file, node_cold_vkey_file, addr_name):
    try:
        suffix_str = "_stake.deleg.cert"
        cmd = "cardano-cli shelley stake-address delegation-certificate" \
              " --stake-verification-key-file " + stake_addr_vkey_file + \
              " --cold-verification-key-file " + node_cold_vkey_file + \
              " --out-file " + location + "/" + addr_name + suffix_str
        subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
        return location + "/" + addr_name + suffix_str
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode,
                                                                                 ' '.join(str(e.output).split())))


def read_address_from_file(location, address_file_name=None):
    with open(location + "/" + address_file_name, 'r') as file:
        address = file.read().replace('\n', '')
    return address


def get_file_location(sub_directory, filename):
    current_directory = pathlib.Path(__file__).parent.absolute()
    file_location = current_directory + "/" + sub_directory + "/" + filename
    if os.path.isfile(file_location):
        return file_location


def write_to_file(location, content, filename):
    with open(location + "/" + filename, 'w') as file:
        file.write(json.dumps(content))
    return location + "/" + filename


def get_protocol_params():
    set_node_socket_path_env_var()
    try:
        cmd = "cardano-cli shelley query protocol-parameters" \
              " --testnet-magic " + TESTNET_MAGIC + \
              " --out-file " + PROTOCOL_PARAMS_FILEPATH
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode,
                                                                                 ' '.join(str(e.output).split())))


def get_stake_distribution():
    # this will create a dictionary of in this format: {stake_pool_id: staked_value}
    set_node_socket_path_env_var()
    stake_distribution = {}
    try:
        cmd = "cardano-cli shelley query stake-distribution" \
              " --testnet-magic " + TESTNET_MAGIC
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip().splitlines()

        line_no = 0
        for line in result:
            # stake pool values are displayed starting with line 2 from the command output
            if line_no > 1:
                formatted_pool_stake = re.split("[\s,]+", line)
                stake_distribution[formatted_pool_stake[0]] = formatted_pool_stake[1]
            line_no += 1
        return stake_distribution
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode,
                                                                                 ' '.join(str(e.output).split())))


def get_key_deposit():
    get_protocol_params()
    with open('protocol-params.json', 'r') as myfile:
        data = myfile.read()
    protocol_params = json.loads(data)
    return protocol_params["keyDeposit"]


def get_pool_deposit():
    get_protocol_params()
    with open('protocol-params.json', 'r') as myfile:
        data = myfile.read()
    protocol_params = json.loads(data)
    return protocol_params["poolDeposit"]


def get_current_tip():
    set_node_socket_path_env_var()
    try:
        cmd = "cardano-cli shelley query tip --testnet-magic " + TESTNET_MAGIC
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
        output_json = json.loads(output)
        return output_json['blockNo'], output_json['headerHash'], output_json['slotNo']
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode,
                                                                                 ' '.join(str(e.output).split())))


def get_current_slot_no():
    block_no, header_hash, slot_no = get_current_tip()
    return slot_no


def get_current_block_no():
    block_no, header_hash, slot_no = get_current_tip()
    return block_no


def get_current_epoch_no():
    current_slot_no = get_current_slot_no()
    epoch_length = get_epoch_length()
    return int(current_slot_no / epoch_length)


def get_address_utxos(address):
    # this will create a list of utxos in this format: ['utxo_hash', utxo_ix, utxo_amount]
    set_node_socket_path_env_var()
    available_utxos_list = []
    try:
        cmd = "cardano-cli shelley query utxo" \
              " --testnet-magic " + TESTNET_MAGIC + \
              " --address " + address + " | grep '^[^- ]'"
        address_utxo_list = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode(
            "utf-8").strip().splitlines()

        for utxo in address_utxo_list:
            formatted_utxo = re.split("[\s,]+", utxo)
            utxo_hash = formatted_utxo[0]
            utxo_ix = int(formatted_utxo[1])
            utxo_amount = int(formatted_utxo[2])
            available_utxos_list.append([utxo_hash, utxo_ix, utxo_amount])
        return available_utxos_list
    except subprocess.CalledProcessError as e:
        print(f"WARNING: no UTXOs available for address: {address}")
        return available_utxos_list


def get_address_balance(address):
    address_balance = 0
    if get_no_of_utxos_for_address(address) > 0:
        available_utxos_list = get_address_utxos(address)
        for utxo in available_utxos_list:
            utxo_amount = utxo[2]
            address_balance += utxo_amount
    return int(address_balance)


def assert_address_balance(address, expected_balance):
    actual_balance = get_address_balance(address)
    if actual_balance != expected_balance:
        print(
            f"ERROR: Incorrect amount of funds for address. Actual: {actual_balance}  vs  Expected: {expected_balance}")
        exit(2)
    else:
        print(f"Success: Correct balance: {expected_balance} for address {address}")


def get_no_of_utxos_for_address(address):
    available_utxos_list = get_address_utxos(address)
    return len(available_utxos_list)


def get_utxo_with_highest_value(address):
    # this will return the utxo in this format: ('utxo_hash', utxo_ix, utxo_amount)
    utxo_hash_highest_amount = ""
    utxo_ix_highest_amount = ""
    highest_amount = 0
    available_utxos_list = get_address_utxos(address)
    for utxo in available_utxos_list:
        utxo_amount = utxo[2]
        if utxo_amount > highest_amount:
            highest_amount = utxo_amount
            utxo_hash_highest_amount = utxo[0]
            utxo_ix_highest_amount = utxo[1]
    return [utxo_hash_highest_amount, utxo_ix_highest_amount, highest_amount]


def calculate_tx_ttl():
    current_slot_no = get_current_slot_no()
    return current_slot_no + 1000


def calculate_tx_fee(src_addr, dst_addr_list, tx_ttl, witness_count=0, byron_witness_count=0, **options):
    # tx_fee depends on the tx_size, so first we need to build the transaction
    get_protocol_params()
    certificate_files = []

    if options.get("certificates"):
        certificate_files = options.get("certificates")

    # create a dummy dst_amounts_list in order to build the transaction
    dst_amounts_list = list(range(0, len(dst_addr_list)))
    tx_build_result = build_raw_transaction(tx_ttl, 0, src_addr, dst_addr_list, dst_amounts_list,
                                            certificates=certificate_files)
    if not tx_build_result[0]:
        print(f"ERROR: Error while building the transaction --> {tx_build_result[1]}")
        exit(2)
    tx_body_file = tx_build_result[1]

    cmd = "cardano-cli shelley transaction calculate-min-fee" \
          " --tx-body-file " + tx_body_file + \
          " --testnet-magic " + TESTNET_MAGIC + \
          " --tx-in-count " + "1" + \
          " --tx-out-count " + str(len(dst_amounts_list) + 1) + \
          " --witness-count " + str(witness_count) + \
          " --byron-witness-count " + str(byron_witness_count) + \
          " --protocol-params-file " + PROTOCOL_PARAMS_FILEPATH
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
        return int(result.split(" ")[0])
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode,
                                                                                 ' '.join(str(e.output).split())))


def get_slot_length():
    # TO DO: take this value from genesis; first define where genesis will be located
    slot_length = 0.2
    return slot_length


def get_epoch_length():
    # TO DO: take this value from genesis; first define where genesis will be located
    epoch_length = 1500
    return epoch_length


def get_slots_per_kes_period():
    # TO DO: take this value from genesis; first define where genesis will be located (slotsPerKESPeriod)``
    slots_per_kes_period = 129600
    return slots_per_kes_period


def get_max_kes_evolutions():
    # TO DO: take this value from genesis; first define where genesis will be located (maxKESEvolutions)``
    max_kes_evolutions = 60
    return max_kes_evolutions


def wait_for_new_tip():
    print("Waiting for a new block to be created")
    slot_length = get_slot_length()
    timeout_no_of_slots = 200
    current_slot_no = get_current_slot_no()
    initial_slot_no = get_current_slot_no()
    print(f"initial_tip: {initial_slot_no}")
    while current_slot_no == initial_slot_no:
        sleep(slot_length)
        current_slot_no = get_current_slot_no()
        timeout_no_of_slots -= 1
        if timeout_no_of_slots < 2:
            print(f"ERROR: Waited for {timeout_no_of_slots} slots but no new block was created")
            exit(2)
    print(f"New block was created; slot number: {current_slot_no}")


def wait_for_new_epoch(no_of_epochs_to_wait=1):
    slot_length = get_slot_length()
    epoch_length = get_epoch_length()
    current_slot_no = get_current_slot_no()
    current_epoch_no = get_current_epoch_no()
    print(f"Current epoch: {current_epoch_no}; Waiting the beginning of epoch: {current_epoch_no + no_of_epochs_to_wait}")

    timeout_no_of_epochs = no_of_epochs_to_wait + 1
    expected_epoch_no = current_epoch_no + no_of_epochs_to_wait

    while current_epoch_no != expected_epoch_no:
        sleep_slots = (current_epoch_no + 1) * epoch_length - current_slot_no
        sleep_time = int(sleep_slots * slot_length) + 1
        sleep(sleep_time)
        current_epoch_no = get_current_epoch_no()
        current_slot_no = get_current_slot_no()
        timeout_no_of_epochs -= 1
        if timeout_no_of_epochs < 1:
            print(f"ERROR: Waited for {no_of_epochs_to_wait + 1} epochs and expected epoch no is not present")
            exit(2)
    print(f"Expected epoch started; epoch number: {current_epoch_no}")


def build_raw_transaction(ttl, fee, src_address, dst_addr_list, dst_amounts, **options):
    # **options can be: certificates, withdrawal, metadata_json, metadata_cbor, update_proposal
    # tx_in = list of input utxos in this format: (utxo_hash#utxo_ix)
    # tx_out = list of outputs in this format: (address+amount)
    print(f"Building the raw transaction...")
    out_file = "tx_raw.body"

    cmd = "cardano-cli shelley transaction build-raw" \
          " --fee " + str(fee) + \
          " --ttl " + str(ttl) + \
          " --out-file " + out_file

    src_addr_balance = get_address_balance(src_address)
    required_funds = sum(dst_amounts) + fee
    change = src_addr_balance - required_funds

    # create the list of transaction inputs (use all the available UTXOs for the source address)
    input_utxos_list_for_tx = []
    input_utxos_list = get_address_utxos(src_address)
    for utxo in input_utxos_list:
        input_utxos_list_for_tx.append(str(utxo[0]) + "#" + str(utxo[1]))

    # create the list of transaction outputs
    out_change_list = []
    for dst, dst_amount in zip(dst_addr_list, dst_amounts):
        out_change_list.append(dst + "+" + str(dst_amount))
    if change > 0:
        out_change_list.append(src_address + "+" + str(change))

    tx_in_cmd = ''.join([" --tx-in " + tx_in_el for tx_in_el in input_utxos_list_for_tx])
    cmd = cmd + tx_in_cmd

    tx_out_cmd = ''.join([" --tx-out " + tx_out_el for tx_out_el in out_change_list])
    cmd = cmd + tx_out_cmd

    try:
        if options.get("certificates"):
            certificate_files = options.get('certificates')
            certificates_cmd = ''.join([" --certificate-file " + cert_file for cert_file in certificate_files])
            cmd = cmd + certificates_cmd

        if options.get("metadata_json"):
            metadata_files = options.get('metadata_json')
            metadata_json_cmd = ''.join([" --metadata-json-file " + str(metadata_file) for metadata_file in metadata_files])
            cmd = cmd + metadata_json_cmd

        if options.get("metadata_cbor"):
            metadata_files = options.get('metadata_cbor')
            metadata_cbor_cmd = ''.join([" --metadata-cbor-file " + str(metadata_file) for metadata_file in metadata_files])
            cmd = cmd + metadata_cbor_cmd

        if options.get("withdrawal"):
            withdrawal_files = options.get('withdrawal')
            withdrawal_cmd = ''.join([" --withdrawal " + str(withdrawal_file) for withdrawal_file in withdrawal_files])
            cmd = cmd + withdrawal_cmd

        if options.get("update_proposal"):
            update_proposal_files = options.get('update_proposal')
            update_proposal_cmd = ''.join([" --update-proposal-file " + str(update_proposal_file)
                                           for update_proposal_file in update_proposal_files])
            cmd = cmd + update_proposal_cmd

        subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
        return [True, out_file]
    except subprocess.CalledProcessError as e:
        print(f"WARNING: command '{e.cmd}' return with error (code {e.returncode}): {' '.join(str(e.output).split())}")
        return [False, ' '.join(str(e.output).split())]


def sign_raw_transaction(tx_body_file, **options):
    # **options can be: signing_keys
    # signing_keys = list of file paths for the signing keys
    print(f"Signing the raw transaction...")

    out_file = "tx_raw.signed"

    cmd = "cardano-cli shelley transaction sign" \
          " --testnet-magic " + TESTNET_MAGIC + \
          " --tx-body-file " + tx_body_file + \
          " --out-file " + out_file
    try:
        if options.get("signing_keys"):
            signing_keys_list = options.get('signing_keys')
            signing_key_cmd = ''.join([" --signing-key-file " + signing_key for signing_key in signing_keys_list])
            cmd = cmd + signing_key_cmd

        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
        return [True, out_file, result]
    except subprocess.CalledProcessError as e:
        print(f"WARNING: command '{e.cmd}' return with error (code {e.returncode}): {' '.join(str(e.output).split())}")
        return [False, ' '.join(str(e.output).split())]


def submit_raw_transaction(tx_file):
    print(f"Submitting the raw transaction...")
    try:
        cmd = "cardano-cli shelley transaction submit" \
              " --testnet-magic " + TESTNET_MAGIC + \
              " --tx-file " + tx_file
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
        return [True, result]
    except subprocess.CalledProcessError as e:
        print(f"WARNING: command '{e.cmd}' return with error (code {e.returncode}): {' '.join(str(e.output).split())}")
        return [False, ' '.join(str(e.output).split())]


def send_funds(src_address, tx_fee, tx_ttl, **options):
    # **options can be: transferred_amounts, destinations_list, signing_keys, certificates, metadata_list
    input_utxos_list, transferred_amounts, signing_keys_list, certificates_list, metadata_list, destinations_list = \
        [], [], [], [], [], []
    required_funds, change = 0, 0
    tx_signed_file, tx_body_file = None, None

    # check the destination addresses and the transferred amounts
    if options.get("transferred_amounts"):
        if not options.get("destinations_list"):
            print("ERROR: 'transferred_amounts' option was provided but 'destinations_list' option was not provided.")
            exit(2)

        destinations_list = options.get('destinations_list')
        transferred_amounts = options.get('transferred_amounts')

    # create the list of transaction signing keys
    if options.get("signing_keys"):
        signing_keys_list = options.get('signing_keys')

    # create the list of transaction certificates
    if options.get("certificates"):
        certificates_list = options.get('certificates')

    if options.get("metadata_list"):
        metadata_list = options.get('metadata_list')

    # build the raw transaction
    tx_build_result = build_raw_transaction(tx_ttl, tx_fee, src_address, destinations_list, transferred_amounts,
                                            certificates=certificates_list, metadata=metadata_list)
    if not tx_build_result[0]:
        print(f"ERROR: transaction not successfully built --> {tx_build_result[1]}")
        exit(2)
    else:
        tx_body_file = tx_build_result[1]

    # sign the raw transaction
    tx_sign_result = sign_raw_transaction(tx_body_file, signing_keys=signing_keys_list)
    if not tx_sign_result[0]:
        print(f"ERROR: transaction not successfully signed --> {tx_sign_result[1]}")
        exit(2)
    else:
        tx_signed_file = tx_sign_result[1]

    # submit the raw transaction
    tx_submit_result = submit_raw_transaction(tx_signed_file)
    if not tx_submit_result[0]:
        print(f"ERROR: transaction not successfully submitted --> {tx_submit_result[1]}")
        exit(2)


def gen_kes_key_pair(location, node_name):
    try:
        cmd = "cardano-cli shelley node key-gen-KES " + \
              " --verification-key-file " + location + "/" + node_name + "_kes.vkey" + \
              " --signing-key-file " + location + "/" + node_name + "_kes.skey"
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
        return location + "/" + node_name + "_kes.vkey", location + "/" + node_name + "_kes.skey"
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode,
                                                                                 ' '.join(str(e.output).split())))


def gen_vrf_key_pair(location, node_name):
    try:
        cmd = "cardano-cli shelley node key-gen-VRF " + \
              " --verification-key-file " + location + "/" + node_name + "_vrf.vkey" + \
              " --signing-key-file " + location + "/" + node_name + "_vrf.skey"
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
        return location + "/" + node_name + "_vrf.vkey", location + "/" + node_name + "_vrf.skey"
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode,
                                                                                 ' '.join(str(e.output).split())))


def gen_cold_key_pair_and_counter(location, node_name):
    try:
        cmd = "cardano-cli shelley node key-gen" + \
              " --verification-key-file " + location + "/" + node_name + "_cold.vkey" + \
              " --signing-key-file " + location + "/" + node_name + "_cold.skey" + \
              " --operational-certificate-issue-counter " + location + "/" + node_name + "_cold.counter"
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
        return location + "/" + node_name + "_cold.vkey", location + \
               "/" + node_name + "_cold.skey", location + \
               "/" + node_name + "_cold.counter"
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode,
                                                                                 ' '.join(str(e.output).split())))


def get_actual_kes_period():
    actual_slot_no = get_current_slot_no()
    slots_per_kes_period = get_slots_per_kes_period()
    current_kes_period = int(actual_slot_no / slots_per_kes_period)
    return current_kes_period


def gen_node_operational_cert(node_kes_vkey_file, node_cold_skey_file, node_cold_counter_file, location, node_name):
    # this certificate is used when starting the node and not submitted throw a tx
    current_kes_period = get_actual_kes_period()
    suffix_str = ".opcert"
    try:
        cmd = "cardano-cli shelley node issue-op-cert" + \
              " --kes-verification-key-file " + node_kes_vkey_file + \
              " --cold-signing-key-file " + node_cold_skey_file + \
              " --operational-certificate-issue-counter " + node_cold_counter_file + \
              " --kes-period " + str(current_kes_period) + \
              " --out-file " + location + "/" + node_name + suffix_str
        subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
        return location + "/" + node_name + suffix_str
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode,
                                                                                 ' '.join(str(e.output).split())))


def gen_pool_metadata_hash(pool_metadata_file):
    try:
        cmd = "cardano-cli shelley stake-pool metadata-hash" + \
              " --pool-metadata-file " + pool_metadata_file
        metadata_hash = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
        return metadata_hash
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode,
                                                                                 ' '.join(str(e.output).split())))


def gen_pool_registration_cert(pool_pledge, pool_cost, pool_margin, node_vrf_vkey_file, node_cold_vkey_file,
                               owner_stake_addr_vkey_file, location, node_name, **options):
    suffix_str = "_pool_reg.cert"
    cmd = "cardano-cli shelley stake-pool registration-certificate" + \
          " --pool-pledge " + str(pool_pledge) + \
          " --pool-cost " + str(pool_cost) + \
          " --pool-margin " + str(pool_margin) + \
          " --vrf-verification-key-file " + node_vrf_vkey_file + \
          " --cold-verification-key-file " + node_cold_vkey_file + \
          " --pool-reward-account-verification-key-file " + owner_stake_addr_vkey_file + \
          " --pool-owner-stake-verification-key-file " + owner_stake_addr_vkey_file + \
          " --testnet-magic " + TESTNET_MAGIC + \
          " --out-file " + location + "/" + node_name + suffix_str
    try:
        # pool_metadata is a list of: [pool_metadata_url, pool_metadata_hash]
        if options.get("pool_metadata") and len(options.get("pool_metadata")) == 2:
            pool_metadata_url = options.get('pool_metadata')[0]
            pool_metadata_hash = options.get('pool_metadata')[1]
            pool_metadata_cmd = " --metadata-url " + pool_metadata_url + " --metadata-hash " + pool_metadata_hash
            cmd = cmd + pool_metadata_cmd
        subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
        return location + "/" + node_name + suffix_str
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode,
                                                                                 ' '.join(str(e.output).split())))


def gen_pool_deregistration_cert(cold_verification_key_file, epoch_no, location, node_name):
    suffix_str = "_pool_dereg.cert"
    cmd = "cardano-cli shelley stake-pool deregistration-certificate" + \
          " --cold-verification-key-file " + cold_verification_key_file + \
          " --epoch " + str(epoch_no) + \
          " --out-file " + location + "/" + node_name + suffix_str
    try:
        subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
        return location + "/" + node_name + suffix_str
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode,
                                                                                 ' '.join(str(e.output).split())))


def get_ledger_state():
    set_node_socket_path_env_var()
    try:
        cmd = "cardano-cli shelley query ledger-state" + \
              " --testnet-magic " + TESTNET_MAGIC
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
        output_json = json.loads(output)
        return output_json
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode,
                                                                                 ' '.join(str(e.output).split())))


def get_registered_stake_pools_ledger_state():
    ledger_state = get_ledger_state()
    registered_pools_details = ledger_state["esLState"]["_delegationState"]["_pstate"]["_pParams"]
    return registered_pools_details


def get_stake_pool_id(pool_cold_vkey_file):
    try:
        cmd = "cardano-cli shelley stake-pool id" + \
              " --verification-key-file " + pool_cold_vkey_file
        pool_id = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
        return pool_id
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode,
                                                                                 ' '.join(str(e.output).split())))


def create_and_register_stake_pool(location, pool_name, pool_pledge, pool_cost, pool_margin, pool_owner, **options):
    # pool_owner = [addr, addr_vkey_file, addr_skey_file, stake_addr, stake_addr_vkey_file, stake_addr_skey_file]
    # create the KES key pair
    node_kes_vkey_file, node_kes_skey_file = gen_kes_key_pair(location, pool_name)
    print(f"KES keys created - {node_kes_vkey_file}; {node_kes_skey_file}")

    # create the VRF key pair
    node_vrf_vkey_file, node_vrf_skey_file = gen_vrf_key_pair(location, pool_name)
    print(f"VRF keys created - {node_vrf_vkey_file}; {node_vrf_skey_file}")

    # create the cold key pair and node operational certificate counter
    node_cold_vkey_file, node_cold_skey_file, node_cold_counter_file = gen_cold_key_pair_and_counter(location, pool_name)
    print(f"Cold keys created and counter created - {node_cold_vkey_file}; {node_cold_skey_file}; {node_cold_counter_file}")
    # create the stake pool registration certificate
    pool_metadata = []
    if options.get("pool_metadata"):
        # pool_metadata is a list of: [pool_metadata_url, pool_metadata_hash]
        pool_metadata = options.get("pool_metadata")

    register_stake_pool(pool_owner, pool_pledge, pool_cost, pool_margin, node_vrf_vkey_file, node_cold_vkey_file,
                        node_cold_skey_file, location, pool_name, pool_metadata)

    stake_pool_id = get_stake_pool_id(node_cold_vkey_file)
    return stake_pool_id, node_cold_vkey_file, node_cold_skey_file, node_vrf_vkey_file


def register_stake_pool(pool_owner, pool_pledge, pool_cost, pool_margin, node_vrf_vkey_file, node_cold_vkey_file,
                        node_cold_skey_file, location, pool_name, pool_metadata=None):
    # pool_owner = [addr, addr_vkey_file, addr_skey_file, stake_addr, stake_addr_vkey_file, stake_addr_skey_file]
    if pool_metadata is None:
        pool_metadata = []
    pool_reg_cert_file = gen_pool_registration_cert(pool_pledge, pool_cost, pool_margin, node_vrf_vkey_file,
                                                    node_cold_vkey_file, pool_owner[4],
                                                    location, pool_name, pool_metadata=pool_metadata)

    # submit the pool registration certificate through a tx
    tx_ttl = calculate_tx_ttl()
    signing_keys_list = [pool_owner[2], pool_owner[5], node_cold_skey_file]
    tx_fee = 0
    # tx_fee = calculate_tx_fee(1, 1, tx_ttl, certificates=[pool_reg_cert_file], signing_keys=signing_keys_list)
    pool_deposit = get_pool_deposit()
    send_funds(pool_owner[0], tx_fee + pool_deposit, tx_ttl,
               certificates=[pool_reg_cert_file],
               signing_keys=signing_keys_list)

    wait_for_new_tip()
    wait_for_new_tip()
    return pool_reg_cert_file


def deregister_stake_pool(pool_owner, node_cold_vkey_file, node_cold_skey_file, epoch_no, location, pool_name):
    # the pool will be deregistered in pool {epoch_no} but it will take effect after 2 epochs {epoch_no + 2}
    # pool_owner = [addr, addr_vkey_file, addr_skey_file, stake_addr, stake_addr_vkey_file, stake_addr_skey_file]
    print(f"Deregistering stake pool starting with epoch: {epoch_no}; Current epoch is: {get_current_epoch_no()}")
    pool_dereg_cert_file = gen_pool_deregistration_cert(node_cold_vkey_file, epoch_no,
                                                        location, pool_name)

    # submit the pool deregistration certificate through a tx
    tx_ttl = calculate_tx_ttl()
    signing_keys_list = [pool_owner[2], pool_owner[5], node_cold_skey_file]
    tx_fee = 0
    # tx_fee = calculate_tx_fee(1, 1, tx_ttl, certificates=[pool_dereg_cert_file], signing_keys=signing_keys_list)
    send_funds(pool_owner[0], tx_fee, tx_ttl,
               certificates=[pool_dereg_cert_file],
               signing_keys=signing_keys_list)

    wait_for_new_tip()
    wait_for_new_tip()
