# project: Support360
# object_type: T
# object_name: support360_ticket_assignment
# event_type: form_action
# function_name: assign_agent
# form_no: 1
# action_name: Assign Agent
# language: python
# description: Assign the selected agent to the current ticket
# functional_specification: Read TICKET_NO from the form and fetch the current SUPPORT360_TICKET row to get its CATEGORY_CODE. Search SUPPORT360_AGENT for a row where PREFERENCE equals the ticket's CATEGORY_CODE AND AGENT_STATUS = 'Active' AND AGENT_AVAILABILITY = 'Available'. If exactly one such agent is found, persist ASSIGNED_AGENT, ASSIGNED_AGENT_NAME and STATUS = 'Assigned' on the SUPPORT360_TICKET row for that TICKET_NO, then return updates for ASSIGNED_AGENT/ASSIGNED_AGENT_NAME/STATUS so the form refreshes with the new values immediately. If no single matching agent is found, leave the ticket unchanged and return an empty updates object with a message that no available agent was found.
# business_logic: Assign the single matching available agent to the current ticket based on its category code


def run(args):
    ticket_no = args.get('ticket_no')

    if is_empty(ticket_no):
        return 'Ticket number is required to assign an agent.'

    ticket = db.query_one(
        'SELECT t.STATUS AS STATUS, t.CATEGORY_NAME AS CATEGORY_NAME '
        'FROM SUPPORT360_TICKET t '
        'WHERE t.TICKET_NO = :ticket_no',
        {'ticket_no': ticket_no}
    )

    if not ticket:
        return 'Ticket ' + str(ticket_no) + ' could not be found.'

    status = ticket.get('STATUS')
    category_name = ticket.get('CATEGORY_NAME')

    if status != 'Pending':
        return {
            'errors': [{
                'code': 'TICKET_ALREADY_ASSIGNED',
                'field': 'status',
                'type': 'E',
                'message': 'Ticket already assigned',
            }],
            'error': 'Ticket already assigned',
        }

    agent = db.query_one(
        'SELECT AGENT_ID, AGENT_NAME FROM SUPPORT360_AGENT '
        'WHERE PREFERENCE = :category_name '
        "AND AGENT_STATUS = 'Active' AND AGENT_AVAILABILITY = 'Available'",
        {'category_name': category_name}
    )

    if not agent:
        return {
            'errors': [{
                'code': 'NO_AGENT_AVAILABLE',
                'field': 'assigned_agent',
                'type': 'E',
                'message': 'No active and available agent found with matching preference for category ' + str(category_name) + '.',
            }],
            'error': 'No active and available agent found with matching preference for category ' + str(category_name) + '.',
        }

    db.update(
        'SUPPORT360_TICKET',
        {
            'STATUS': 'Assigned',
            'ASSIGNED_AGENT': agent.get('AGENT_ID'),
            'ASSIGNED_AGENT_NAME': agent.get('AGENT_NAME'),
        },
        {'TICKET_NO': ticket_no}
    )

    return {
        'updates': {
            'TICKET_NO': ticket_no,
            'ASSIGNED_AGENT': agent.get('AGENT_ID'),
            'ASSIGNED_AGENT_NAME': agent.get('AGENT_NAME'),
            'STATUS': 'Assigned',
        },
        'message': 'Ticket assigned to ' + str(agent.get('AGENT_NAME')),
    }
