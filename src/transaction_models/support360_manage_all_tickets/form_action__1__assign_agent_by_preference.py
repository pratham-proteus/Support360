# project: Support360
# object_type: T
# object_name: support360_manage_all_tickets
# event_type: form_action
# function_name: assign_agent_by_preference
# form_no: 1
# action_name: Assign Agent
# language: python
# description: Assign (or queue) this Pending ticket to the agent chosen in the Assigned Agent field
# functional_specification: Read TICKET_NO, STATUS, CATEGORY, ASSIGNED_AGENT from the submitted form. If STATUS != 'Pending', return {"error": "Ticket is no longer Pending."}. If ASSIGNED_AGENT is empty, return {"error": "Please choose an agent in the Assigned Agent field before clicking Assign Agent."}. Look up SUPPORT360_AGENT where AGENT_ID = ASSIGNED_AGENT AND AGENT_STATUS = 'Active' AND PREFERENCE = CATEGORY; if not found, return {"error": "Selected agent " + ASSIGNED_AGENT + " was not found."} and make no update. Otherwise read AGENT_NAME; update SUPPORT360_TICKET setting STATUS = 'Assigned', ASSIGNED_AGENT_NAME = AGENT_NAME, CHG_DATE = now(), CHG_USER = current user; append an ACTIVITY_HISTORY entry (action_type 'Assigned', field_changed 'ASSIGNED_AGENT', old_value blank, new_value ASSIGNED_AGENT, changed_by current user, timestamp now); return {"message": "Assigned to " + AGENT_NAME}. Never raise a raw database/SQL error; return {"error": "..."} on any unexpected failure.
# business_logic: Assign (or queue) this Pending ticket to the agent chosen in the Assigned Agent field


def run(args):
    try:
        ticket_no = (args.get('TICKET_NO') or '').strip()
        if is_empty(ticket_no):
            return {'error': 'Ticket number is required.'}

        status = (args.get('STATUS') or '').strip()
        if status != 'Pending':
            return {'error': 'Ticket is no longer Pending.'}

        assigned_agent = (args.get('ASSIGNED_AGENT') or '').strip()
        if is_empty(assigned_agent):
            return {'error': 'Please choose an agent in the Assigned Agent field before clicking Assign Agent.'}

        category = (args.get('CATEGORY') or '').strip()

        agent = db.get('SUPPORT360_AGENT', {'AGENT_ID': assigned_agent, 'AGENT_STATUS': 'Active', 'PREFERENCE': category})
        if not agent:
            return {'error': 'Selected agent ' + assigned_agent + ' was not found.'}

        agent_name = (agent['AGENT_NAME'] or '').strip()
        new_status = 'Assigned'

        user = coalesce(args.get('CHG_USER'), args.get('ADD_USER'), 'system')
        user = str(user)[:10]
        ts = now()
        ts_str = ts.strftime('%Y-%m-%d %H:%M:%S')

        entry = {
            'action_type': new_status,
            'field_changed': 'ASSIGNED_AGENT',
            'old_value': '',
            'new_value': assigned_agent,
            'changed_by': user,
            'timestamp': ts_str,
        }
        ticket = db.get('SUPPORT360_TICKET', {'TICKET_NO': ticket_no})
        history = (ticket and ticket.get('ACTIVITY_HISTORY')) or ''
        history = (history + '\n' if history.strip() else '') + json.dumps(entry)

        db.update('SUPPORT360_TICKET',
                  {'STATUS': new_status,
                   'ASSIGNED_AGENT_NAME': agent_name,
                   'CHG_DATE': ts,
                   'CHG_USER': user,
                   'ACTIVITY_HISTORY': history},
                  {'TICKET_NO': ticket_no})

        return {'message': 'Assigned to ' + agent_name}
    except Exception as exc:
        return {'error': 'Unable to process agent assignment for this ticket: ' + str(exc)}
