# project: Support360
# object_type: T
# object_name: support360_manage_ticket_queue
# event_type: form_action
# function_name: resolve_ticket
# form_no: 1
# action_name: Resolve
# language: python
# description: Agent marks the ticket as resolved
# functional_specification: On the current SUPPORT360_TICKET row, set STATUS to 'Resolved'. Append one entry to the ticket's Activity/History Log (table to be confirmed once the Ticket Activity Log object is designed) with TICKET_NO = this ticket, ACTION_TYPE = 'Status-Changed', FIELD_CHANGED = 'STATUS', OLD_VALUE = 'In Progress', NEW_VALUE = 'Resolved', CHANGED_BY = current user, CHANGE_DATE = now. Return {"updates": {"status": "Resolved"}}.
# business_logic: Agent marks the ticket as resolved

def run(args):
    ticket_no = args.get('ticket_no')
    status = args.get('status')
    assigned_agent = args.get('assigned_agent')
    resolution_notes = args.get('resolution_notes')
    current_user = args.get('_current_user') or args.get('current_user')

    # Ticket must be In Progress and assigned to the current agent before it can be resolved
    if status != 'In Progress' or assigned_agent != current_user:
        return 'Ticket must be In Progress and assigned to you to resolve'

    # Resolution notes are required to resolve the ticket
    if is_empty(resolution_notes):
        return 'Resolution notes are required'

    now = datetime.datetime.now()

    # Persist the status change and resolution notes to SUPPORT360_TICKET keyed by TICKET_NO
    db.update('SUPPORT360_TICKET', {
        'STATUS': 'Resolved',
        'RESOLUTION_NOTES': resolution_notes,
    }, {'TICKET_NO': ticket_no})

    # Insert activity log entry
    db.insert('SUPPORT360_TICKET_ACTLOG', {
        'TICKET_NO': ticket_no,
        'ACTION_TYPE': 'Status-Changed',
        'FIELD_CHANGED': 'STATUS',
        'OLD_VALUE': 'In Progress',
        'NEW_VALUE': 'Resolved',
        'CHANGED_BY': current_user,
        'CHANGE_DATE': now,
    })

    return {'updates': {'status': 'Resolved'}}
