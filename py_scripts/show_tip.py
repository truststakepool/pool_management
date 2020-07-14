from py_scripts.utils import get_current_tip

block_no, header_hash, slot_no = get_current_tip()

print(f"block_no    : {block_no}")
print(f"header_hash : {header_hash}")
print(f"slot_no     : {slot_no}")
