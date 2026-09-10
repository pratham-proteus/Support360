# project: Support360
# object_type: T
# object_name: support360_create_ticket
# event_type: form_action
# function_name: assign_agent
# form_no: 1
# action_name: Assign Agent
# language: python
# description: Assign Agent
# functional_specification: Assign Agent action for the ticket.
# business_logic: Assign Agent


def run(args):
    """Auto-assign a random, currently Active + Available agent to the ticket.

    Looks up every agent whose AGENT_STATUS is 'Active' and AGENT_AVAILABILITY
    is 'Available', picks one at random, sets the ticket's ASSIGNED_AGENT to
    that agent and moves the ticket's STATUS from 'Open' to 'Assigned'. The
    ticket must currently be Open; otherwise the action is rejected.
    """
    out = {'errors': []}

    ticket_no = args.get('TICKET_NO')

    if is_empty(ticket_no):
        out['errors'].append({'code': 'ASGN001', 'field': 'ticket_no', 'type': 'E',
                              'message': 'Ticket number is required to assign an agent.'})
        out['error'] = out['errors'][0]['message']
        return out

    ticket = db.query_one(
        'SELECT TICKET_NO, STATUS, ASSIGNED_AGENT, TITLE, PRIORITY_CODE '
        'FROM ' + db.t('SUPPORT360_TICKET') + ' WHERE TICKET_NO = :t',
        {'t': ticket_no})
    if not ticket:
        out['errors'].append({'code': 'ASGN002', 'field': 'ticket_no', 'type': 'E',
                              'message': 'Ticket ' + str(ticket_no) + ' does not exist.'})
        out['error'] = out['errors'][0]['message']
        return out

    status = (ticket.get('STATUS') or ticket.get('status') or '').strip()

    if status != 'Open':
        out['errors'].append({'code': 'ASGN003', 'field': 'assigned_agent', 'type': 'E',
                              'message': 'Ticket can only be assigned while it is Open.'})
        out['error'] = out['errors'][0]['message']
        return out

    # find every agent who is both Active and Available
    candidates = db.query(
        'SELECT AGENT_ID, AGENT_NAME, AGENT_AVAILABILITY, AGENT_STATUS '
        'FROM ' + db.t('SUPPORT360_AGENT') +
        ' WHERE AGENT_STATUS = :st AND AGENT_AVAILABILITY = :av',
        {'st': 'Active', 'av': 'Available'})

    if not candidates:
        out['errors'].append({'code': 'ASGN004', 'field': 'assigned_agent', 'type': 'E',
                              'message': 'No active and available agent found to assign this ticket.'})
        out['error'] = out['errors'][0]['message']
        return out

    # pick one candidate uniformly at random (no random module available,
    # so the current microsecond timestamp is used to derive the index)
    stamp = now()
    pick_index = int(stamp.strftime('%f')) % len(candidates)
    agent = candidates[pick_index]
    agent_id = agent.get('AGENT_ID') or agent.get('agent_id')

    db.update(
        'SUPPORT360_TICKET',
        {'ASSIGNED_AGENT': agent_id, 'STATUS': 'Assigned', 'CHG_DATE': stamp,
         'CHG_USER': args.get('CHG_USER')},
        {'TICKET_NO': ticket_no})

    agent_name = agent.get('AGENT_NAME') or agent.get('agent_name') or agent_id
    return {
        'prompts': [{'code': 'ASGN100', 'type': 'P',
                     'message': 'Ticket ' + str(ticket_no) + ' assigned to ' + str(agent_name) + '.'}],
        'updates': {'ASSIGNED_AGENT': agent_id, 'STATUS': 'Assigned'},
    }
