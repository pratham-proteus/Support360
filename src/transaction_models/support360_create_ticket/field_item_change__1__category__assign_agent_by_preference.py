# project: Support360
# object_type: T
# object_name: support360_create_ticket
# event_type: field_item_change
# function_name: assign_agent_by_preference
# form_no: 1
# field_name: category
# language: python
# description: Auto-assign ticket to the agent whose PREFERENCE matches the selected CATEGORY: STATUS becomes Assigned if that agent is Active+Available, Queued if Active+Occupied, otherwise the ticket stays Pending.
# business_logic: Auto-assign ticket to the agent whose PREFERENCE matches the selected CATEGORY: STATUS becomes Assigned if that agent is Active+Available, Queued if Active+Occupied, otherwise the ticket stays Pending.


def run(args):
    category = (args.get('CATEGORY') or '').strip()
    if is_empty(category):
        return {'updates': {'ASSIGNED_AGENT': None, 'ASSIGNED_AGENT_NAME': None, 'STATUS': 'Pending'}}

    # Active agents with this preference; prefer an Available one over an Occupied one
    agents = db.query(
        'SELECT AGENT_ID, AGENT_NAME, AGENT_AVAILABILITY FROM ' + db.t('SUPPORT360_AGENT')
        + ' WHERE PREFERENCE = :cat AND AGENT_STATUS = :st ORDER BY AGENT_ID',
        {'cat': category.upper(), 'st': 'Active'},
    ) or []

    chosen = None
    status = 'Pending'
    for a in agents:
        if (a['AGENT_AVAILABILITY'] or '').strip() == 'Available':
            chosen, status = a, 'Assigned'
            break
    if chosen is None:
        for a in agents:
            if (a['AGENT_AVAILABILITY'] or '').strip() == 'Occupied':
                chosen, status = a, 'Queued'
                break

    if chosen is None:
        return {'updates': {'ASSIGNED_AGENT': None, 'ASSIGNED_AGENT_NAME': None, 'STATUS': 'Pending'}}

    return {'updates': {
        'ASSIGNED_AGENT': (chosen['AGENT_ID'] or '').strip(),
        'ASSIGNED_AGENT_NAME': chosen['AGENT_NAME'],
        'STATUS': status,
    }}
