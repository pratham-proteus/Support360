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
        'SELECT CATEGORY_CODE FROM SUPPORT360_TICKET '
        'WHERE TICKET_NO = :ticket_no',
        {'ticket_no': ticket_no}
    )

    if not ticket:
        return 'Ticket ' + str(ticket_no) + ' could not be found.'

    category_code = ticket.get('CATEGORY_CODE')

    agents = db.query(
        'SELECT AGENT_ID, AGENT_NAME FROM SUPPORT360_AGENT '
        'WHERE PREFERENCE = :category_code '
        "AND AGENT_STATUS = 'Active' AND AGENT_AVAILABILITY = 'Available'",
        {'category_code': category_code}
    )

    if not agents or len(agents) != 1:
        return {
            'updates': {},
            'message': 'No available agent found for ' + str(category_code),
        }

    agent = agents[0]

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
            'ASSIGNED_AGENT': agent.get('AGENT_ID'),
            'ASSIGNED_AGENT_NAME': agent.get('AGENT_NAME'),
            'STATUS': 'Assigned',
        },
        'message': 'Ticket assigned to ' + str(agent.get('AGENT_NAME')),
    }
