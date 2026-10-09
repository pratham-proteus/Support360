# project: Support360
# object_type: T
# object_name: support360_manage_all_tickets
# event_type: form_action
# function_name: assign_agent
# form_no: 1
# action_name: Assign Agent
# language: python
# description: Open the Ticket Assignment screen for this ticket so an agent can be assigned
# functional_specification: Given the current record's TICKET_NO (PK), open the support360_ticket_assignment screen passing TICKET_NO so the admin/agent can assign an agent to this ticket from there. Only applicable while STATUS = 'Pending' and ASSIGNED_AGENT is empty/null on the current record. Return {"message": "Opening ticket assignment for {TICKET_NO}"} to confirm the navigation; return {"error": "..."} if the ticket no longer qualifies (status is not Pending or an agent is already assigned).
# business_logic: Open the Ticket Assignment screen for this ticket so an agent can be assigned


def run(args):
    ticket_no = (args.get('TICKET_NO') or '').strip()
    if is_empty(ticket_no):
        return {'error': 'Ticket number is required to assign an agent.'}

    # Re-read the persisted ticket so the decision reflects the current DB state
    row = db.query_one(
        'SELECT status, assigned_agent FROM ' + db.t('SUPPORT360_TICKET') +
        ' WHERE ticket_no = :t',
        {'t': ticket_no},
    )
    if row is None:
        return {'error': 'Ticket ' + ticket_no + ' was not found.'}

    status = (row['STATUS'] or '').strip()
    agent = (row['ASSIGNED_AGENT'] or '').strip()

    if status != 'Pending':
        return {'error': 'Ticket ' + ticket_no + ' cannot be assigned: status is '
                + (status or 'blank') + ' (must be Pending).'}
    if not_empty(agent):
        return {'error': 'Ticket ' + ticket_no + ' is already assigned to agent ' + agent + '.'}

    return {
        'message': 'Opening ticket assignment for ' + ticket_no,
        'navigate': {
            'screen': 'support360_ticket_assignment',
            'params': {'TICKET_NO': ticket_no},
        },
    }
