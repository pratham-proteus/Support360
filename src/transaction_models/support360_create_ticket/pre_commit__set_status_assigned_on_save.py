# project: Support360
# object_type: T
# object_name: support360_create_ticket
# event_type: pre_commit
# function_name: set_status_assigned_on_save
# language: python
# description: Flip a Pending ticket to Assigned on save
# functional_specification: Before the ticket is committed on Save or Save & Close (action = add or edit), if STATUS = 'Pending', set STATUS = 'Assigned'. Leave STATUS unchanged for any other current value. Does not touch ASSIGNED_AGENT or any other column, and never blocks the save.
# business_logic: Flip a Pending ticket to Assigned on save


def run(args):
    action = (args.get('action') or args.get('ACTION') or '').strip().lower()
    if action not in ('add', 'edit'):
        return None

    return None
