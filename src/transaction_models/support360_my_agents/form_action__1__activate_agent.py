# project: Support360
# object_type: T
# object_name: support360_my_agents
# event_type: form_action
# function_name: activate_agent
# form_no: 1
# action_name: Activate Agent
# language: python
# description: Mark the agent Active
# functional_specification: Set AGENT_STATUS to 'Active' and AGENT_AVAILABILITY to 'Available' for the agent in the payload; persist the change on SUPPORT360_AGENT and return {"updates": {"AGENT_STATUS": "Active", "AGENT_AVAILABILITY": {"value": "Available", "protect": "0"}}}. Refuse with {"error": ...} if the agent is already Active.
# business_logic: Mark the agent Active


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
    if current == 'Active':
        return {'error': 'Agent is already Active.'}

    db.update(
        'SUPPORT360_AGENT',
        {'AGENT_STATUS': 'Active',
         'AGENT_AVAILABILITY': 'Available',
         'CHG_DATE': now()},
        {'AGENT_ID': agent_id})

    return {'updates': {
        'AGENT_STATUS': 'Active',
        'AGENT_AVAILABILITY': {'value': 'Available', 'protect': '0'},
    }}
