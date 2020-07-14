from py_scripts.utils import get_actual_kes_period, get_current_slot_no, get_slots_per_kes_period

print(f"actual_slot_no      : {get_current_slot_no()}")
print(f"slots_per_kes_period: {get_slots_per_kes_period()}")
print(f"current KES period  : {get_actual_kes_period()}")
