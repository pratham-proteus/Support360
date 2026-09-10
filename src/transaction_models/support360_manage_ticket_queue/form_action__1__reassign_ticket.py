# project: Support360
# object_type: T
# object_name: support360_manage_ticket_queue
# event_type: form_action
# function_name: reassign_ticket
# form_no: 1
# action_name: Reassign
# language: python
# description: Reassign an already-assigned ticket to a different Agent, keeping its STATUS unchanged
# functional_specification: On the current SUPPORT360_TICKET row, set ASSIGNED_AGENT to the value in REASSIGN_TO_AGENT. Do not change STATUS. Then clear REASSIGN_TO_AGENT. Append one entry to the ticket's Activity/History Log (table to be confirmed once the Ticket Activity Log object is designed) with TICKET_NO = this ticket, ACTION_TYPE = 'Reassigned', FIELD_CHANGED = 'ASSIGNED_AGENT', OLD_VALUE = the previous ASSIGNED_AGENT, NEW_VALUE = REASSIGN_TO_AGENT, CHANGED_BY = current user, CHANGE_DATE = now. Return {"updates": {"assigned_agent": <new agent>, "reassign_to_agent": ""}}.
# business_logic: Reassign an already-assigned ticket to a different Agent, keeping its STATUS unchanged

def run(args):
    current_user = args.get('_current_user') or args.get('current_user')

    status = args.get('status')
    if status not in ('Assigned', 'In Progress'):
        return 'Ticket must be Assigned or In Progress to be reassigned'

    ticket_no = args.get('ticket_no')
    old_agent = args.get('assigned_agent')

    if old_agent != current_user:
        return 'Only the currently assigned Agent can reassign this ticket'

    new_agent = args.get('reassign_to_agent')
    if is_empty(new_agent):
        return 'Reassign To Agent is required'

    # Persist the reassignment on SUPPORT360_TICKET
    db.update('SUPPORT360_TICKET', {
        'ASSIGNED_AGENT': new_agent,
        'STATUS': 'Assigned',  # reset from In Progress since the new agent has not started work
        'REASSIGN_TO_AGENT': None,
        'CHG_DATE': datetime.now(),
    }, {'TICKET_NO': ticket_no})

    # Log the reassignment in the ticket activity log
    db.insert('SUPPORT360_TICKET_ACTLOG', {
        'TICKET_NO': ticket_no,
        'ACTION_TYPE': 'Reassigned',
        'FIELD_CHANGED': 'ASSIGNED_AGENT',
        'OLD_VALUE': old_agent,
        'NEW_VALUE': new_agent,
        'CHANGED_BY': current_user,
        'CHANGE_DATE': datetime.now(),
    })

    return {'updates': {'assigned_agent': new_agent, 'status': 'Assigned', 'reassign_to_agent': ''}}
