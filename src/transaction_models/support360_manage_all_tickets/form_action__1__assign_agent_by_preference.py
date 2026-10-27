# project: Support360
# object_type: T
# object_name: support360_manage_all_tickets
# event_type: form_action
# function_name: assign_agent_by_preference
# form_no: 1
# action_name: Assign Agent
# language: python
# description: Auto-match and assign this Pending ticket to the agent whose PREFERENCE equals the ticket's CATEGORY_NAME
# functional_specification: Given the current record's TICKET_NO and CATEGORY_NAME, require STATUS = 'Pending' (otherwise return {"error": "Ticket is no longer Pending."}). Look up SUPPORT360_AGENT for an agent where PREFERENCE = the ticket's CATEGORY_NAME and AGENT_STATUS = 'Active'. If found and AGENT_AVAILABILITY = 'Available': update SUPPORT360_TICKET setting ASSIGNED_AGENT = that agent's AGENT_ID, STATUS = 'Assigned', CHG_DATE = now(), CHG_USER = current user; append an ACTIVITY_HISTORY entry (action_type 'Assigned', field_changed 'ASSIGNED_AGENT', old_value blank, new_value the agent, changed_by current user, timestamp now); return {"message": "Ticket assigned to " + AGENT_ID}. If found but AGENT_AVAILABILITY != 'Available' (Occupied): update SUPPORT360_TICKET setting ASSIGNED_AGENT = that agent's AGENT_ID, STATUS = 'Queued', CHG_DATE = now(), CHG_USER = current user; append the same kind of ACTIVITY_HISTORY entry with action_type 'Queued'; return {"message": "Matching agent is occupied; ticket queued to " + AGENT_ID}. If no agent has a matching PREFERENCE at all: make no changes and return {"message": "No agent matches this ticket's category preference; ticket remains Pending."}. Never raise a raw database/SQL error; return {"error": "..."} on any unexpected failure.
# business_logic: Auto-match and assign this Pending ticket to the agent whose PREFERENCE equals the ticket's CATEGORY_NAME


def run(args):
    try:
        ticket_no = (args.get('TICKET_NO') or '').strip()
        if is_empty(ticket_no):
            return {'error': 'Ticket number is required.'}

        ticket = db.query_one(
            'SELECT TICKET_NO, STATUS, CATEGORY_NAME, ASSIGNED_AGENT, ACTIVITY_HISTORY FROM '
            + db.t('SUPPORT360_TICKET') + ' WHERE TICKET_NO = :t',
            {'t': ticket_no})
        if not ticket:
            return {'error': 'Ticket ' + ticket_no + ' not found.'}

        status = (ticket['STATUS'] or args.get('STATUS') or '').strip()
        if status != 'Pending':
            return {'error': 'Ticket is no longer Pending.'}

        category = (ticket['CATEGORY_NAME'] or args.get('CATEGORY_NAME') or '').strip()
        if is_empty(category):
            return {'message': "No agent matches this ticket's category preference; ticket remains Pending."}

        agent = db.query_one(
            'SELECT AGENT_ID, AGENT_AVAILABILITY FROM ' + db.t('SUPPORT360_AGENT')
            + " WHERE PREFERENCE = :p AND AGENT_STATUS = 'Active'"
            + " ORDER BY CASE WHEN AGENT_AVAILABILITY = 'Available' THEN 0 ELSE 1 END, AGENT_ID",
            {'p': category})
        if not agent:
            return {'message': "No agent matches this ticket's category preference; ticket remains Pending."}

        agent_id = (agent['AGENT_ID'] or '').strip()
        available = (agent['AGENT_AVAILABILITY'] or '').strip() == 'Available'
        new_status = 'Assigned' if available else 'Queued'

        user = coalesce(args.get('CHG_USER'), args.get('ADD_USER'), 'system')
        user = str(user)[:10]
        ts = now()
        ts_str = ts.strftime('%Y-%m-%d %H:%M:%S')

        entry = {
            'action_type': new_status,
            'field_changed': 'ASSIGNED_AGENT',
            'old_value': '',
            'new_value': agent_id,
            'changed_by': user,
            'timestamp': ts_str,
        }
        history = ticket['ACTIVITY_HISTORY'] or ''
        history = (history + '\n' if history.strip() else '') + json.dumps(entry)

        db.update('SUPPORT360_TICKET',
                  {'ASSIGNED_AGENT': agent_id,
                   'STATUS': new_status,
                   'CHG_DATE': ts,
                   'CHG_USER': user,
                   'ACTIVITY_HISTORY': history},
                  {'TICKET_NO': ticket_no})

        if available:
            return {'message': 'Ticket assigned to ' + agent_id}
        return {'message': 'Matching agent is occupied; ticket queued to ' + agent_id}
    except Exception:
        return {'error': 'Unable to process agent assignment for this ticket.'}
