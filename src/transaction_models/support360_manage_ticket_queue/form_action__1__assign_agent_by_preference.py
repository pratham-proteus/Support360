# project: Support360
# object_type: T
# object_name: support360_manage_ticket_queue
# event_type: form_action
# function_name: assign_agent_by_preference
# form_no: 1
# action_name: Assign Agent
# language: python
# description: Auto-assign the ticket to the Support Agent whose PREFERENCE matches the ticket's category
# functional_specification: On click, look up table SUPPORT360_AGENT where PREFERENCE = this ticket's CATEGORY_CODE (column SUPPORT360_TICKET.CATEGORY_CODE), AGENT_STATUS = 'Active', and AGENT_AVAILABILITY = 'Available'. If exactly one or more agents match, pick one and set SUPPORT360_TICKET.ASSIGNED_AGENT = that agent's AGENT_ID and SUPPORT360_TICKET.STATUS = 'Assigned' on this row (return {"updates": {"assigned_agent": ..., "status": "Assigned"}}). The Assigned To display column (assigned_agent_name, sourced from SUPPORT360_AGENT.AGENT_NAME via the existing left join on ASSIGNED_AGENT) needs no direct update — it resolves automatically once ASSIGNED_AGENT changes. If no Active+Available agent has a matching PREFERENCE (including the case where a matching agent exists but is Active+Occupied), make no changes to ASSIGNED_AGENT or STATUS and surface a non-blocking message to the user that no eligible agent was found for this category.
# business_logic: Auto-assign the ticket to the Support Agent whose PREFERENCE matches the ticket's category


def run(args):
    category = args.get('category_code')

    # Fall back to the stored ticket's category if the form value is missing
    if is_empty(category) and not_empty(args.get('ticket_no')):
        category = db.scalar(
            'SELECT category_code FROM ' + db.t('SUPPORT360_TICKET') +
            ' WHERE ticket_no = :t',
            {'t': args.get('ticket_no')})

    if is_empty(category):
        return {'errors': [{'code': 'AAPNOCAT', 'field': 'category_code', 'type': 'P',
                            'message': 'Ticket has no category; no eligible agent was found.'}]}

    category = str(category).strip()

    agent = db.query_one(
        'SELECT agent_id, agent_name FROM ' + db.t('SUPPORT360_AGENT') +
        ' WHERE preference = :pref'
        " AND agent_status = 'Active'"
        " AND agent_availability = 'Available'"
        ' ORDER BY agent_id',
        {'pref': category.upper()})

    if not agent:
        return {'errors': [{'code': 'AAPNOAGT', 'field': 'assigned_agent', 'type': 'P',
                            'message': 'No eligible (Active and Available) agent found for category '
                                       + category + '.'}]}

    agent_id = str(agent['agent_id']).strip()
    return {
        'updates': {
            'assigned_agent': agent_id,
            'status': 'Assigned',
        },
        'errors': [{'code': 'AAPASSIGNED', 'type': 'P',
                    'message': 'Ticket assigned to ' + str(agent['agent_name']).strip()
                               + ' (' + agent_id + ').'}],
    }
