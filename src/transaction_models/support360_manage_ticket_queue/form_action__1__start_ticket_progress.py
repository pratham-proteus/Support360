# project: Support360
# object_type: T
# object_name: support360_manage_ticket_queue
# event_type: form_action
# function_name: start_ticket_progress
# form_no: 1
# action_name: Start Progress
# language: python
# description: Agent starts working an assigned ticket
# functional_specification: On the current SUPPORT360_TICKET row, when STATUS is 'Assigned' or 'Reopen', set STATUS to 'In Progress'. Append one entry to the ticket's Activity/History Log (table to be confirmed once the Ticket Activity Log object is designed) with TICKET_NO = this ticket, ACTION_TYPE = 'Status-Changed', FIELD_CHANGED = 'STATUS', OLD_VALUE = the ticket's actual prior STATUS ('Assigned' or 'Reopen'), NEW_VALUE = 'In Progress', CHANGED_BY = current user, CHANGE_DATE = now. Return {"updates": {"status": "In Progress"}}.
# business_logic: Agent starts working an assigned ticket

def run(args):
    ticket_no = args.get('ticket_no')
    status = args.get('status')
    assigned_agent = args.get('assigned_agent')
    current_user = args.get('_current_user') or args.get('current_user')

    # Ticket must be Assigned or Reopened to the current agent before work can start
    if status not in ('Assigned', 'Reopen') or assigned_agent != current_user:
        return 'Ticket must be Assigned to you before starting work'

    ts = now()

    # Persist the status change to SUPPORT360_TICKET keyed by TICKET_NO
    db.update('SUPPORT360_TICKET', {
        'STATUS': 'In Progress',
    }, {'TICKET_NO': ticket_no})

    # Insert activity log entry
    db.insert('SUPPORT360_TICKET_ACTLOG', {
        'TICKET_NO': ticket_no,
        'ACTION_TYPE': 'Status-Changed',
        'FIELD_CHANGED': 'STATUS',
        'OLD_VALUE': status,
        'NEW_VALUE': 'In Progress',
        'CHANGED_BY': current_user,
        'CHANGE_DATE': ts,
    })

    return {'updates': {'status': 'In Progress'}}
