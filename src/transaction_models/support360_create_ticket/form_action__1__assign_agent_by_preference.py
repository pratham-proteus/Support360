# project: Support360
# object_type: T
# object_name: support360_create_ticket
# event_type: form_action
# function_name: assign_agent_by_preference
# form_no: 1
# action_name: Assign Agent
# language: python
# description: Auto-assign the ticket to the Support Agent whose PREFERENCE matches the ticket category
# functional_specification: On click, look up table SUPPORT360_AGENT where PREFERENCE = this ticket's CATEGORY_CODE (column SUPPORT360_TICKET.CATEGORY_CODE), AGENT_STATUS = 'Active', and AGENT_AVAILABILITY = 'Available'. If one or more agents match, pick one and set SUPPORT360_TICKET.ASSIGNED_AGENT = that agent's AGENT_ID and SUPPORT360_TICKET.STATUS = 'Assigned' on this row (return {"updates": {"assigned_agent": ..., "status": "Assigned"}}). ASSIGNED_AGENT_NAME needs no direct update - it resolves automatically via the new left join on ASSIGNED_AGENT. If no Active+Available agent has a matching PREFERENCE (including a matching agent that is Active but Occupied), make no changes and surface a non-blocking message that no eligible agent was found for this category. This action is only reachable while STATUS = 'Pending' and ASSIGNED_AGENT is empty (enforced by the action's visible_when), so no status guard is needed here.
# business_logic: Auto-assign the ticket to the Support Agent whose PREFERENCE matches the ticket category


def run(args):
    category = args.get('CATEGORY_CODE')
    category = str(category).strip() if not_empty(category) else ''

    if not category:
        return {'prompts': [{
            'code': 'ASGAGT01',
            'field': 'category_code',
            'type': 'P',
            'message': 'Select a category before assigning an agent.',
        }]}

    agent = db.query_one(
        'SELECT agent_id FROM ' + db.t('SUPPORT360_AGENT') +
        ' WHERE preference = :pref'
        ' AND agent_status = :st'
        ' AND agent_availability = :av'
        ' ORDER BY agent_id',
        {'pref': category, 'st': 'Active', 'av': 'Available'},
    )

    if not agent:
        return {'prompts': [{
            'code': 'ASGAGT02',
            'field': 'assigned_agent',
            'type': 'P',
            'message': 'No eligible agent available for this category.',
        }]}

    return {'updates': {
        'assigned_agent': str(agent['AGENT_ID']).strip(),
        'status': 'Assigned',
    }}
