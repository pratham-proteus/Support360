# event: action
# object: support360_manage_all_tickets
# form: 1
# method: assign_ticket
# description: Assign the current ticket to the selected agent.
# functional_specification:
#   Validates that the ticket exists, is not already Resolved/closed, and that an
#   agent has been selected in ASSIGNED_AGENT. The agent must exist, be Active and
#   Available. Warns (override-able) when the ticket is already assigned to another
#   agent. On success the ticket's ASSIGNED_AGENT, STATUS ('In Progress'),
#   CHG_DATE and ACTIVITY_HISTORY are updated, the agent is marked Occupied and an
#   'Assigned' row is written to SUPPORT360_TICKET_ACTLOG.


def _new_id():
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S%f') + str(math.floor(now().timestamp() * 1000) % 100000)


def _who(args):
    return coalesce(args.get('CHG_USER'), args.get('ADD_USER'), 'SYSTEM')


def run(args):
    out = {'errors': []}
    ignored = set(args.get('_ignore_warnings') or [])

    ticket_no = args.get('TICKET_NO')
    agent_id = args.get('ASSIGNED_AGENT')

    if is_empty(ticket_no):
        return 'Ticket number is required to assign a ticket.'

    ticket = db.query_one(
        'SELECT TICKET_NO, STATUS, ASSIGNED_AGENT, ACTIVITY_HISTORY '
        'FROM ' + db.t('SUPPORT360_TICKET') + ' WHERE TICKET_NO = :t',
        {'t': ticket_no})
    if not ticket:
        return 'Ticket ' + str(ticket_no) + ' does not exist.'

    if is_empty(agent_id):
        out['errors'].append({'code': 'ASGAGT1', 'field': 'assigned_agent', 'type': 'E',
                              'message': 'Select an agent before assigning the ticket.'})
        out['error'] = out['errors'][0]['message']
        return out

    cur_status = coalesce(ticket.get('STATUS'), '')
    if cur_status == 'Resolved':
        return 'Ticket ' + str(ticket_no) + ' is already Resolved and cannot be assigned.'

    agent = db.query_one(
        'SELECT AGENT_ID, AGENT_NAME, AGENT_STATUS, AGENT_AVAILABILITY '
        'FROM ' + db.t('SUPPORT360_AGENT') + ' WHERE AGENT_ID = :a',
        {'a': agent_id})
    if not agent:
        out['errors'].append({'code': 'ASGAGT2', 'field': 'assigned_agent', 'type': 'E',
                              'message': 'Agent ' + str(agent_id) + ' does not exist.'})
    else:
        if coalesce(agent.get('AGENT_STATUS'), '') != 'Active':
            out['errors'].append({'code': 'ASGAGT3', 'field': 'assigned_agent', 'type': 'E',
                                  'message': 'Agent ' + str(agent_id) + ' is not Active.'})
        elif coalesce(agent.get('AGENT_AVAILABILITY'), '') != 'Available':
            out['errors'].append({'code': 'ASGAGT4', 'field': 'assigned_agent', 'type': 'E',
                                  'message': 'Agent ' + str(agent_id) + ' is currently Occupied.'})

    prev_agent = coalesce(ticket.get('ASSIGNED_AGENT'), '')
    if not_empty(prev_agent) and prev_agent != agent_id:
        if 'ASGAGT5' not in ignored:
            out['errors'].append({'code': 'ASGAGT5', 'field': 'assigned_agent', 'type': 'W',
                                  'message': 'Ticket is already assigned to ' + str(prev_agent) +
                                             '. Proceeding will re-assign it to ' + str(agent_id) + '.'})

    blocking = [e for e in out['errors'] if coalesce(e.get('type'), 'E') == 'E']
    if blocking:
        out['error'] = blocking[0]['message']
        return out
    if [e for e in out['errors'] if e.get('type') == 'W']:
        return out

    if not_empty(prev_agent) and prev_agent == agent_id and cur_status == 'In Progress':
        return {'prompts': [{'code': 'ASGAGT6', 'type': 'P',
                             'message': 'Ticket is already assigned to ' + str(agent_id) + '. No change made.'}]}

    stamp = now()
    user = _who(args)
    agent_name = coalesce(agent.get('AGENT_NAME'), agent_id)

    history = coalesce(ticket.get('ACTIVITY_HISTORY'), '')
    entry = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' | Assigned to ' + \
        str(agent_name) + ' (' + str(agent_id) + ') by ' + str(user)
    history = entry if is_empty(history) else history + '\n' + entry

    db.update(db.t('SUPPORT360_TICKET'),
              {'ASSIGNED_AGENT': agent_id,
               'STATUS': 'In Progress',
               'ACTIVITY_HISTORY': history,
               'CHG_DATE': stamp,
               'CHG_USER': user},
              {'TICKET_NO': ticket_no})

    db.update(db.t('SUPPORT360_AGENT'),
              {'AGENT_AVAILABILITY': 'Occupied', 'CHG_DATE': stamp, 'CHG_USER': user},
              {'AGENT_ID': agent_id})

    if not_empty(prev_agent) and prev_agent != agent_id:
        db.update(db.t('SUPPORT360_AGENT'),
                  {'AGENT_AVAILABILITY': 'Available', 'CHG_DATE': stamp, 'CHG_USER': user},
                  {'AGENT_ID': prev_agent})

    db.insert(db.t('SUPPORT360_TICKET_ACTLOG'), {
        'ID': _new_id(),
        'TICKET_NO': ticket_no,
        'ACTION_TYPE': 'Assigned',
        'FIELD_CHANGED': 'ASSIGNED_AGENT',
        'OLD_VALUE': prev_agent,
        'NEW_VALUE': agent_id,
        'CHANGED_BY': user,
        'CHANGE_DATE': stamp,
        'ADD_DATE': stamp,
        'ADD_USER': user,
        'ADD_TERM': args.get('ADD_TERM'),
    })

    if cur_status != 'In Progress':
        db.insert(db.t('SUPPORT360_TICKET_ACTLOG'), {
            'ID': _new_id(),
            'TICKET_NO': ticket_no,
            'ACTION_TYPE': 'Status-Changed',
            'FIELD_CHANGED': 'STATUS',
            'OLD_VALUE': cur_status,
            'NEW_VALUE': 'In Progress',
            'CHANGED_BY': user,
            'CHANGE_DATE': stamp,
            'ADD_DATE': stamp,
            'ADD_USER': user,
            'ADD_TERM': args.get('ADD_TERM'),
        })

    return {'prompts': [{'code': 'ASGAGT9', 'type': 'P',
                         'message': 'Ticket ' + str(ticket_no) + ' assigned to ' +
                                    str(agent_name) + ' and moved to In Progress.'}]}
