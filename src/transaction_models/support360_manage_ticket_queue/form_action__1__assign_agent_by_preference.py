# project: Support360
# object_type: T
# object_name: support360_manage_ticket_queue
# event_type: form_action
# function_name: assign_agent_by_preference
# form_no: 1
# action_name: Assign Agent
# language: python
# description: Auto-assign the ticket to the Support Agent whose PREFERENCE matches the ticket's category
# functional_specification: On click, look up table SUPPORT360_AGENT where PREFERENCE = this ticket's CATEGORY_CODE (column SUPPORT360_TICKET.CATEGORY_CODE) and AGENT_STATUS = 'Active'; AGENT_AVAILABILITY is ignored and not filtered on. If one or more agents match, pick the next agent round-robin by ascending AGENT_ID (based on which matching agent was most recently assigned a ticket in this category) and set SUPPORT360_TICKET.ASSIGNED_AGENT = that agent's AGENT_ID and SUPPORT360_TICKET.STATUS = 'Assigned' on this row (return {"updates": {"assigned_agent": ..., "status": "Assigned"}}). The Assigned To display column (assigned_agent_name, sourced from SUPPORT360_AGENT.AGENT_NAME via the existing left join on ASSIGNED_AGENT) needs no direct update — it resolves automatically once ASSIGNED_AGENT changes. If no Active agent has a matching PREFERENCE, make no changes to ASSIGNED_AGENT or STATUS and surface a non-blocking message to the user that no eligible agent was found for this category.
# business_logic: Auto-assign the ticket to the Support Agent whose PREFERENCE matches the ticket's category


def run(args):
    category = args.get('category')

    # Fall back to the stored ticket's category if the form value is missing
    if is_empty(category) and not_empty(args.get('ticket_no')):
        category = db.scalar(
            'SELECT category FROM ' + db.t('SUPPORT360_TICKET') +
            ' WHERE ticket_no = :t',
            {'t': args.get('ticket_no')})

    if is_empty(category):
        return {'errors': [{'code': 'AAPNOCAT', 'field': 'category_name', 'type': 'P',
                            'message': 'Ticket has no category; no eligible agent was found.'}]}

    category = str(category).strip()

    agents = db.query(
        'SELECT agent_id FROM ' + db.t('SUPPORT360_AGENT') +
        ' WHERE preference = :pref'
        " AND agent_status = 'Active'"
        ' ORDER BY agent_id',
        {'pref': category})

    if not agents:
        return {'errors': [{'code': 'AAPNOAGT', 'field': 'assigned_agent', 'type': 'P',
                            'message': 'No eligible (Active) agent found for category '
                                       + category + '.'}]}

    agent_ids = [str(a['agent_id']).strip() for a in agents]

    # Round-robin: find the agent who most recently received a ticket in this
    # category and assign the next one (by ascending AGENT_ID), wrapping around.
    last_agent = db.scalar(
        'SELECT assigned_agent FROM ' + db.t('SUPPORT360_TICKET') +
        ' WHERE category = :pref'
        ' AND assigned_agent IS NOT NULL'
        ' ORDER BY chg_date DESC'
        ' LIMIT 1',
        {'pref': category})

    if not_empty(last_agent) and str(last_agent).strip() in agent_ids:
        next_idx = (agent_ids.index(str(last_agent).strip()) + 1) % len(agent_ids)
    else:
        next_idx = 0

    agent_id = agent_ids[next_idx]

    agent_name = db.scalar(
        'SELECT agent_name FROM ' + db.t('SUPPORT360_AGENT') +
        ' WHERE agent_id = :id',
        {'id': agent_id})

    return {
        'updates': {
            'assigned_agent': agent_id,
            'status': 'Assigned',
        },
        'errors': [{'code': 'AAPASSIGNED', 'type': 'P',
                    'message': 'Ticket assigned to ' + str(agent_name).strip()
                               + ' (' + agent_id + ').'}],
    }
