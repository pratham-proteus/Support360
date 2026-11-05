# project: Support360
# object_type: T
# object_name: support360_create_ticket
# event_type: field_item_change
# function_name: assign_agent_by_preference
# form_no: 1
# field_name: category
# language: python
# description: Auto-assign ticket to the agent whose PREFERENCE matches the selected CATEGORY: STATUS becomes Assigned if a matching Active agent is found, otherwise the ticket stays Pending.
# business_logic: Auto-assign ticket to the agent whose PREFERENCE matches the selected CATEGORY: STATUS becomes Assigned if a matching Active agent is found, otherwise the ticket stays Pending.


def run(args):
    category = (args.get('CATEGORY') or '').strip()
    if is_empty(category):
        return {'updates': {'assigned_agent': None, 'assigned_agent_name': None, 'status': 'Pending'}}

    # Active agents with this preference, in round-robin order by AGENT_ID
    agents = db.query(
        'SELECT AGENT_ID, AGENT_NAME FROM ' + db.t('SUPPORT360_AGENT')
        + ' WHERE PREFERENCE = :cat AND AGENT_STATUS = :st ORDER BY AGENT_ID ASC',
        {'cat': category.upper(), 'st': 'Active'},
    ) or []

    category_master = db.query_one(
        'SELECT CATEGORY_CODE FROM ' + db.t('SUPPORT360_CATEGORY_MASTER')
        + ' WHERE CATEGORY_NAME = :cat',
        {'cat': category},
    )
    if not category_master:
        return {'errors': [{
            'code': 'CATEGORY_CODE_NOT_FOUND',
            'field': 'category',
            'type': 'E',
            'message': 'No matching category code found in SUPPORT360_CATEGORY_MASTER for category "' + category + '".',
        }], 'error': 'No matching category code found in SUPPORT360_CATEGORY_MASTER for category "' + category + '".'}
    category_code = category_master['CATEGORY_CODE']

    chosen = None
    status = 'Pending'
    if agents:
        # Find the most recently assigned agent for this category to continue the rotation
        last_ticket = db.query_one(
            'SELECT ASSIGNED_AGENT FROM ' + db.t('SUPPORT360_TICKET')
            + ' WHERE CATEGORY_CODE = :cat_code AND ASSIGNED_AGENT IS NOT NULL'
            + ' ORDER BY CREATED_DATE DESC, TICKET_NO DESC',
            {'cat_code': category_master['CATEGORY_CODE']},
        )
        last_agent_id = (last_ticket['ASSIGNED_AGENT'] or '').strip() if last_ticket else None

        next_index = 0
        if last_agent_id:
            for idx, agent in enumerate(agents):
                if (agent['AGENT_ID'] or '').strip() == last_agent_id:
                    next_index = (idx + 1) % len(agents)
                    break

        chosen, status = agents[next_index], 'Assigned'

    if chosen is None:
        return {'updates': {'assigned_agent': None, 'assigned_agent_name': None, 'status': 'Pending', 'category_name': category, 'category_code': category_code}}

    return {'updates': {
        'assigned_agent': (chosen['AGENT_ID'] or '').strip(),
        'assigned_agent_name': chosen['AGENT_NAME'],
        'status': status,
        'category_name': category,
        'category_code': category_code,
    }}
