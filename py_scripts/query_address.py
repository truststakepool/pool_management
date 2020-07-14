import argparse

from py_scripts.utils import get_addr_type, get_address_utxos, get_stake_address_info, get_address_balance

# USAGE: python3 query_address.py -a <ADDRESS>


def main():
    if vars(args)["address"]:
        if get_addr_type(vars(args)["address"]) == "payment":
            print(f"address : {vars(args)['address']}")
            print(f"type    : {get_addr_type(vars(args)['address'])}")
            print(f"balance : {get_address_balance(vars(args)['address'])} Lovelace")
            print(f"available UTXOs: ")
            print(get_address_utxos(vars(args)["address"]))
        elif get_addr_type(vars(args)["address"]) == "stake":
            print(f"address     : {vars(args)['address']}")
            print(f"address type: {get_addr_type(vars(args)['address'])}")
            delegation, reward_account_balance = get_stake_address_info(vars(args)["address"])
            print(f"delegated to: {delegation}")
            print(f"reward_account_balance: {reward_account_balance}")
        else:
            print(f"ERROR: unexpected address type: {get_addr_type(vars(args)['address'])} for address {vars(args)['address']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--address", help="Address value", required=True)

    args = parser.parse_args()
    main()
