from pathlib import Path

from py_scripts.utils import gen_pool_metadata_hash, gen_pool_registration_cert, wait_for_new_tip, send_funds, \
    calculate_tx_ttl, calculate_tx_fee, get_registered_stake_pools_ledger_state, get_file_location_if_exists, \
    create_stake_addr_delegation_cert, read_address_from_file, get_address_balance, get_key_deposit, get_stake_pool_id, \
    get_current_test_location, get_user_home_location

pool_metadata_url = "https://raw.githubusercontent.com/truststakepool/a/master/a.json"
pool_metadata_file = get_file_location_if_exists(get_current_test_location(), "pool_metadata.json")

# So pool earn 100 ADA, you have 10 ADA fees, 100 - 10 = 90, then you have 10% margin, 90 * 0.1 = 9 so you earn 19 ADA and the delegators to your pool split the remaining 81
pool_pledge = 90000
pool_cost = 1000
pool_margin = 0.05
pool_name = "pool"

files_location = get_user_home_location() + "/shelley_testnet/files"

addr_file = get_file_location_if_exists(files_location, "owner.addr")
owner_addr = read_address_from_file(addr_file)
addr_skey_file = get_file_location_if_exists(files_location, "owner.skey")

stake_addr_file = get_file_location_if_exists(files_location, "owner_stake.addr")
owner_stake_addr = read_address_from_file(stake_addr_file)
stake_addr_vkey_file = get_file_location_if_exists(files_location, "owner_stake.vkey")
stake_addr_skey_file = get_file_location_if_exists(files_location, "owner_stake.skey")
stake_addr_reg_cert_file = get_file_location_if_exists(files_location, "owner_stake.reg.cert")

pool_vrf_vkey_file = get_file_location_if_exists(files_location, "pool_vrf.vkey")
pool_cold_vkey_file = get_file_location_if_exists(files_location, "pool_cold.vkey")
pool_cold_skey_file = get_file_location_if_exists(files_location, "pool_cold.skey")

print(f"====== Step1: create the pool metadata hash for the pool")
pool_metadata_hash = gen_pool_metadata_hash(pool_metadata_file)
print(f"pool_metadata_hash: {pool_metadata_hash}")

print(f"====== Step2: create the stake pool registration certificate, including the pool metadata hash")
pool_reg_cert_file = gen_pool_registration_cert(pool_pledge, pool_cost, pool_margin, pool_vrf_vkey_file,
                                                pool_cold_vkey_file, stake_addr_vkey_file,
                                                files_location, pool_name,
                                                pool_metadata=[pool_metadata_url, pool_metadata_hash])
print(f"Stake pool registration certificate created - {pool_reg_cert_file}")

print(f"====== Step3: crete the owner-delegation.cert in order to meet the pledge requirements")
stake_addr_delegation_cert_file = create_stake_addr_delegation_cert(files_location, stake_addr_vkey_file,
                                                                    pool_cold_vkey_file, "owner")
print(f"Stake pool owner-delegation certificate created - {stake_addr_delegation_cert_file}")

print(f"====== Step4: submit 3 certificates through a tx - pool registration, stake address registration, "
      f"stake address delegation")
src_address = owner_addr
certificates_list = [pool_reg_cert_file, stake_addr_reg_cert_file, stake_addr_delegation_cert_file]
signing_keys_list = [addr_skey_file, stake_addr_skey_file, pool_cold_skey_file]

tx_ttl = calculate_tx_ttl()
tx_fee = calculate_tx_fee(src_address, [src_address], tx_ttl, certificates=certificates_list)

src_add_balance_init = get_address_balance(src_address)

send_funds(src_address, tx_fee + get_key_deposit(), tx_ttl,
           certificates=certificates_list,
           signing_keys=signing_keys_list)

wait_for_new_tip()
wait_for_new_tip()

stake_pool_id = get_stake_pool_id(pool_cold_vkey_file)
print(f"====== Step5: check that the pool was registered on chain; pool id: {stake_pool_id}")
if stake_pool_id not in list(get_registered_stake_pools_ledger_state().keys()):
    print(f"ERROR: newly created stake pool id is not shown inside the available stake pools; "
          f"\n\t- Pool ID: {stake_pool_id} vs Existing IDs: {list(get_registered_stake_pools_ledger_state().keys())}")
    exit(2)
else:
    print(f"{stake_pool_id} is included into the output of ledger_state() command")

print(f"====== Step6: check the on chain pool details for pool id: {stake_pool_id}")
on_chain_stake_pool_details = get_registered_stake_pools_ledger_state().get(stake_pool_id)
on_chain_pool_details_errors_list = []
if on_chain_stake_pool_details['owners'][0] != owner_stake_addr:
    on_chain_pool_details_errors_list.append(f"'owner' value is different than expected; "
                                             f"Expected: {owner_stake_addr} vs Returned: {on_chain_stake_pool_details['owners'][0]}")

if on_chain_stake_pool_details['cost'] != pool_cost:
    on_chain_pool_details_errors_list.append(f"'cost' value is different than expected; "
                                             f"Expected: {pool_cost} vs Returned: {on_chain_stake_pool_details['cost']}")

if on_chain_stake_pool_details['margin'] != pool_margin:
    on_chain_pool_details_errors_list.append(f"'margin' value is different than expected; "
                                             f"Expected: {pool_margin} vs Returned: {on_chain_stake_pool_details['margin']}")

if on_chain_stake_pool_details['pledge'] != pool_pledge:
    on_chain_pool_details_errors_list.append(f"'pledge' value is different than expected; "
                                             f"Expected: {pool_pledge} vs Returned: {on_chain_stake_pool_details['pledge']}")

if on_chain_stake_pool_details['metadata'] is None:
    on_chain_pool_details_errors_list.append(f"'metadata' value is different than expected; "
                                             f"Expected: not None vs Returned: {on_chain_stake_pool_details['metadata']}")

if on_chain_stake_pool_details['metadata']['hash'] is None:
    on_chain_pool_details_errors_list.append(f"'metadata hash' value is different than expected; "
                                             f"Expected: not None vs Returned: {on_chain_stake_pool_details['metadata']['hash']}")

