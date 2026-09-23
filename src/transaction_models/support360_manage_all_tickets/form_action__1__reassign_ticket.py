# event: action
# object: support360_manage_all_tickets
# form: 1
# method: reassign_ticket
# description: Re-assign the current ticket from its current agent to the agent chosen in REASSIGN_TO_AGENT.
# functional_specification:
#   Validates that the ticket exists, is not Resolved, is currently assigned, and
#   that REASSIGN_TO_AGENT holds a different, Active and Available agent. On success
#   ASSIGNED_AGENT is switched to the new agent, the previous agent is released to
#   Available, the new agent is marked Occupied, ACTIVITY_HISTORY / CHG_DATE are
#   updated, REASSIGN_TO_AGENT is cleared and an 'Assigned' row is written to
#   SUPPORT360_TICKET_ACTLOG.


def _new_id():
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S%f') + str(math.floor(now().timestamp() * 1000) % 100000)


def _who(args):
    return coalesce(args.get('CHG_USER'), args.get('ADD_USER'), 'SYSTEM')


def run(args):
    out = {'errors': []}
    ignored = set(args.get('_ignore_warnings') or [])

    ticket_no = args.get('TICKET_NO')
    new_agent_id = args.get('REASSIGN_TO_AGENT')

    if is_empty(ticket_no):
        return 'Ticket number is required to re-assign a ticket.'

    ticket = db.query_one(
        'SELECT TICKET_NO, STATUS, ASSIGNED_AGENT, ACTIVITY_HISTORY '
        'FROM ' + db.t('SUPPORT360_TICKET') + ' WHERE TICKET_NO = :t',
        {'t': ticket_no})
    if not ticket:
        return 'Ticket ' + str(ticket_no) + ' does not exist.'

    cur_status = coalesce(ticket.get('STATUS'), '')
    prev_agent = coalesce(ticket.get('ASSIGNED_AGENT'), '')

    if is_empty(new_agent_id):
        out['errors'].append({'code': 'REASG1', 'field': 'reassign_to_agent', 'type': 'E',
                              'message': 'Select the agent to re-assign this ticket to.'})
        out['error'] = out['errors'][0]['message']
        return out

    if cur_status == 'Resolved':
        return 'Ticket ' + str(ticket_no) + ' is Resolved and cannot be re-assigned.'

    if is_empty(prev_agent):
        out['errors'].append({'code': 'REASG2', 'field': 'reassign_to_agent', 'type': 'E',
                              'message': 'Ticket is not assigned yet. Use Assign Ticket instead of Re-assign.'})

    if not_empty(prev_agent) and prev_agent == new_agent_id:
        out['errors'].append({'code': 'REASG3', 'field': 'reassign_to_agent', 'type': 'E',
                              'message': 'Ticket is already assigned to ' + str(new_agent_id) +
                                         '. Choose a different agent.'})

    new_agent = db.query_one(
        'SELECT AGENT_ID, AGENT_NAME, AGENT_STATUS, AGENT_AVAILABILITY '
        'FROM ' + db.t('SUPPORT360_AGENT') + ' WHERE AGENT_ID = :a',
        {'a': new_agent_id})
    if not new_agent:
        out['errors'].append({'code': 'REASG4', 'field': 'reassign_to_agent', 'type': 'E',
                              'message': 'Agent ' + str(new_agent_id) + ' does not exist.'})
    else:
        if coalesce(new_agent.get('AGENT_STATUS'), '') != 'Active':
            out['errors'].append({'code': 'REASG5', 'field': 'reassign_to_agent', 'type': 'E',
                                  'message': 'Agent ' + str(new_agent_id) + ' is not Active.'})
        elif coalesce(new_agent.get('AGENT_AVAILABILITY'), '') != 'Available':
            if 'REASG6' not in ignored:
                out['errors'].append({'code': 'REASG6', 'field': 'reassign_to_agent', 'type': 'W',
                                      'message': 'Agent ' + str(new_agent_id) +
                                                 ' is currently Occupied with other work.'})

    blocking = [e for e in out['errors'] if coalesce(e.get('type'), 'E') == 'E']
    if blocking:
        out['error'] = blocking[0]['message']
        return out
    if [e for e in out['errors'] if e.get('type') == 'W']:
        return out

    stamp = now()
    user = _who(args)
    new_name = coalesce(new_agent.get('AGENT_NAME'), new_agent_id)

    history = coalesce(ticket.get('ACTIVITY_HISTORY'), '')
    entry = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' | Re-assigned from ' + \
        str(prev_agent) + ' to ' + str(new_name) + ' (' + str(new_agent_id) + ') by ' + str(user)
    history = entry if is_empty(history) else history + '\n' + entry

    db.update(db.t('SUPPORT360_TICKET'),
              {'ASSIGNED_AGENT': new_agent_id,
               'REASSIGN_TO_AGENT': None,
               'STATUS': 'In Progress',
               'ACTIVITY_HISTORY': history,
               'CHG_DATE': stamp,
               'CHG_USER': user},
              {'TICKET_NO': ticket_no})

    db.update(db.t('SUPPORT360_AGENT'),
              {'AGENT_AVAILABILITY': 'Occupied', 'CHG_DATE': stamp, 'CHG_USER': user},
              {'AGENT_ID': new_agent_id})

    db.update(db.t('SUPPORT360_AGENT'),
              {'AGENT_AVAILABILITY': 'Available', 'CHG_DATE': stamp, 'CHG_USER': user},
              {'AGENT_ID': prev_agent})

    db.insert(db.t('SUPPORT360_TICKET_ACTLOG'), {
        'ID': _new_id(),
        'TICKET_NO': ticket_no,
        'ACTION_TYPE': 'Assigned',
        'FIELD_CHANGED': 'ASSIGNED_AGENT',
        'OLD_VALUE': prev_agent,
        'NEW_VALUE': new_agent_id,
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

    return {'prompts': [{'code': 'REASG9', 'type': 'P',
                         'message': 'Ticket ' + str(ticket_no) + ' re-assigned from ' + str(prev_agent) +
                                    ' to ' + str(new_name) + '.'}]}
