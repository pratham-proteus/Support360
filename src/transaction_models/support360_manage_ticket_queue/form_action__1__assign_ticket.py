# project: Support360
# object_type: T
# object_name: support360_manage_ticket_queue
# event_type: form_action
# function_name: assign_ticket
# form_no: 1
# action_name: Assign
# language: python
# description: Agent takes ownership of an unassigned ticket
# functional_specification: On the current SUPPORT360_TICKET row, verify ASSIGNED_AGENT is blank/null (a ticket already assigned cannot be Assigned again — reject with an error naming the current agent). Update the row: set STATUS to 'Assigned' and ASSIGNED_AGENT to the current logged-in user. Append one entry to the ticket's Activity/History Log (table to be confirmed once the Ticket Activity Log object is designed) with TICKET_NO = this ticket, ACTION_TYPE = 'Assigned', FIELD_CHANGED = 'ASSIGNED_AGENT', OLD_VALUE = '' (blank), NEW_VALUE = current user, CHANGED_BY = current user, CHANGE_DATE = now. Return {"updates": {"status": "Assigned", "assigned_agent": <current user>}}.
# business_logic: Agent takes ownership of an unassigned ticket

def run(args):
    ticket_no = args.get('ticket_no')
    status = args.get('status')
    assigned_agent = args.get('assigned_agent')

    # The agent to assign the ticket to comes from the form's ASSIGNED_AGENT
    # input — the value the Agent picked from the dropdown before clicking
    # Assign — not the current logged-in user.
    selected_agent = assigned_agent

    # Model-level 'Agent required' validation already blocks a blank pick;
    # this is a defensive check in case that somehow doesn't fire.
    if is_empty(selected_agent):
        return 'Please select an Agent to assign this ticket to'

    # The current logged-in user is who performed the action (CHANGED_BY),
    # not who the ticket is being assigned to.
    current_user = coalesce(args.get('CHG_USER'), args.get('ADD_USER'), args.get('RAISED_BY'))

    if is_empty(current_user):
        return 'Unable to determine the current agent — please sign in again before assigning this ticket'

    # Only Open tickets can be assigned
    if status != 'Open':
        return 'Only Open tickets can be assigned'

    ts = now()

    # Persist the update to SUPPORT360_TICKET keyed by TICKET_NO
    db.update('SUPPORT360_TICKET', {
        'STATUS': 'Assigned',
        'ASSIGNED_AGENT': selected_agent,
    }, {'TICKET_NO': ticket_no})

    # Insert activity log entry
    db.insert('SUPPORT360_TICKET_ACTLOG', {
        'TICKET_NO': ticket_no,
        'ACTION_TYPE': 'Assigned',
        'FIELD_CHANGED': 'ASSIGNED_AGENT',
        'OLD_VALUE': '',
        'NEW_VALUE': selected_agent,
        'CHANGED_BY': current_user,
        'CHANGE_DATE': ts,
    })

    return {'updates': {'status': 'Assigned', 'assigned_agent': selected_agent}}
