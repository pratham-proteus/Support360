# project: Support360
# object_type: T
# object_name: support360_ticket_assignment
# event_type: pre_commit
# function_name: set_status_assigned_on_save
# language: python
# description: On save, if the ticket is Pending and an agent has been manually selected, set STATUS to Assigned
# functional_specification: When a user manually picks a name from the Assigned Agent Name dropdown (which looks up ASSIGNED_AGENT on SUPPORT360_AGENT.AGENT_ID) and saves the form while STATUS is still Pending, this hook persists STATUS = Assigned. This is in addition to the Assign Agent action's own auto-match path in form_action__1__assign_agent.py, which changes STATUS when it finds a matching agent itself. In every other case (status is not Pending, or no agent is assigned), STATUS, ASSIGNED_AGENT, ASSIGNED_AGENT_NAME and all other columns are left untouched.
# business_logic: If STATUS == 'Pending' and ASSIGNED_AGENT is not empty, update SUPPORT360_TICKET.STATUS to 'Assigned' for this TICKET_NO and reflect the change in the form via {'updates': {'STATUS': 'Assigned'}}. Otherwise return None.


def run(args):
    header = args.get('header') or {}

    def _pick(row, name):
        for key in (name, name.lower(), name.upper()):
            if key in row:
                return row[key]
        return None

    ticket_no = _pick(header, 'TICKET_NO')
    status = _pick(header, 'STATUS')
    assigned_agent = _pick(header, 'ASSIGNED_AGENT')

    if status == 'Pending' and not_empty(assigned_agent):
        db.update('SUPPORT360_TICKET', {'STATUS': 'Assigned'}, {'TICKET_NO': ticket_no})
        return {'updates': {'STATUS': 'Assigned'}}

    return None
