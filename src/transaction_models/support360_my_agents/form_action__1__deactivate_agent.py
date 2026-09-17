# project: Support360
# object_type: T
# object_name: support360_my_agents
# event_type: form_action
# function_name: deactivate_agent
# form_no: 1
# action_name: Deactivate Agent
# language: python
# description: Mark the agent Inactive
# functional_specification: Set AGENT_STATUS to 'Inactive' and AGENT_AVAILABILITY to 'Occupied' for the agent in the payload; persist the change on SUPPORT360_AGENT and return {"updates": {"AGENT_STATUS": "Inactive", "AGENT_AVAILABILITY": {"value": "Occupied", "protect": "1"}}}. Refuse with {"error": ...} if the agent is already Inactive.
# business_logic: Mark the agent Inactive


def run(args):
    agent_id = args.get('AGENT_ID')
    if is_empty(agent_id):
        return {'error': 'Agent is required.'}

    row = db.query_one(
        'SELECT AGENT_ID, AGENT_NAME, AGENT_STATUS FROM ' + db.t('SUPPORT360_AGENT')
        + ' WHERE AGENT_ID = :a',
        {'a': agent_id})
    if not row:
        return {'error': 'Agent ' + str(agent_id) + ' does not exist.'}

    current = (row.get('AGENT_STATUS') or row.get('agent_status') or '').strip()
    if current == 'Inactive':
        return {'error': 'Agent is already Inactive.'}

    db.update(
        'SUPPORT360_AGENT',
        {'AGENT_STATUS': 'Inactive',
         'AGENT_AVAILABILITY': 'Occupied',
         'CHG_DATE': now()},
        {'AGENT_ID': agent_id})

    return {'updates': {
        'AGENT_STATUS': 'Inactive',
        'AGENT_AVAILABILITY': {'value': 'Occupied', 'protect': '1'},
    }}
