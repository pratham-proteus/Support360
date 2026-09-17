# event: action
# object: support360_manage_ticket_queue
# method: reassign_ticket
# description: Reassign the selected ticket to another agent.
# functional_specification:
#   Validates that the ticket exists, is not already Resolved, that a target agent
#   has been chosen, that the target agent is Active and different from the current
#   assignee, then updates SUPPORT360_TICKET.ASSIGNED_AGENT and writes an
#   'Assigned' row into SUPPORT360_TICKET_ACTLOG recording old and new agent.
#   Warns (override-able) when the target agent is currently Occupied.


def run(args):
    out = {'errors': []}
    ignored = set(args.get('_ignore_warnings') or [])

    ticket_no = args.get('TICKET_NO')
    new_agent = args.get('REASSIGN_TO_AGENT')

    if is_empty(ticket_no):
        out['errors'].append({'code': 'RA001', 'field': 'ticket_no', 'type': 'E',
                              'message': 'Ticket number is required.'})
        out['error'] = out['errors'][0]['message']
        return out

    ticket = db.query_one(
        'SELECT TICKET_NO, STATUS, ASSIGNED_AGENT FROM ' + db.t('SUPPORT360_TICKET') +
        ' WHERE TICKET_NO = :t', {'t': ticket_no})

    if not ticket:
        out['errors'].append({'code': 'RA002', 'field': 'ticket_no', 'type': 'E',
                              'message': 'Ticket ' + str(ticket_no) + ' does not exist.'})
        out['error'] = out['errors'][0]['message']
        return out

    cur_agent = (ticket['ASSIGNED_AGENT'] or '').strip()
    status = (ticket['STATUS'] or '').strip()

    if status == 'Resolved':
        out['errors'].append({'code': 'RA003', 'field': 'status', 'type': 'E',
                              'message': 'A Resolved ticket cannot be reassigned.'})

    if is_empty(new_agent):
        out['errors'].append({'code': 'RA004', 'field': 'reassign_to_agent', 'type': 'E',
                              'message': 'Select the agent to reassign this ticket to.'})
    else:
        new_agent = str(new_agent).strip()
        agent = db.query_one(
            'SELECT AGENT_ID, AGENT_NAME, AGENT_STATUS, AGENT_AVAILABILITY FROM ' +
            db.t('SUPPORT360_AGENT') + ' WHERE AGENT_ID = :a', {'a': new_agent})

        if not agent:
            out['errors'].append({'code': 'RA005', 'field': 'reassign_to_agent', 'type': 'E',
                                  'message': 'Agent ' + new_agent + ' does not exist.'})
        else:
            if (agent['AGENT_STATUS'] or '').strip() != 'Active':
                out['errors'].append({'code': 'RA006', 'field': 'reassign_to_agent', 'type': 'E',
                                      'message': 'Agent ' + new_agent + ' is not Active and cannot be assigned tickets.'})
            if new_agent == cur_agent:
                out['errors'].append({'code': 'RA007', 'field': 'reassign_to_agent', 'type': 'E',
                                      'message': 'The ticket is already assigned to this agent.'})
            if (agent['AGENT_AVAILABILITY'] or '').strip() == 'Occupied' and 'RA008' not in ignored:
                out['errors'].append({'code': 'RA008', 'field': 'reassign_to_agent', 'type': 'W',
                                      'message': 'Agent ' + (agent['AGENT_NAME'] or new_agent) +
                                                 ' is currently Occupied. Reassign anyway?'})

    blocking = [e for e in out['errors'] if e.get('type', 'E') == 'E']
    if blocking:
        out['error'] = blocking[0]['message']
        return out
    if [e for e in out['errors'] if e.get('type') == 'W']:
        return out

    stamp = now()
    changed_by = coalesce(args.get('CHG_USER'), args.get('ADD_USER'), 'SYSTEM')

    db.update(db.t('SUPPORT360_TICKET'),
              {'ASSIGNED_AGENT': new_agent,
               'STATUS': iif(status == '', 'Assigned', status),
               'CHG_DATE': stamp,
               'CHG_USER': changed_by,
               'REASSIGN_TO_AGENT': None},
              {'TICKET_NO': ticket_no})

    log_id = (str(ticket_no) + '-' + datetime.datetime.now().strftime('%Y%m%d%H%M%S%f'))[-36:]
    db.insert(db.t('SUPPORT360_TICKET_ACTLOG'), {
        'ID': log_id,
        'TICKET_NO': ticket_no,
        'ACTION_TYPE': 'Assigned',
        'FIELD_CHANGED': 'ASSIGNED_AGENT',
        'OLD_VALUE': cur_agent or None,
        'NEW_VALUE': new_agent,
        'CHANGED_BY': changed_by,
        'CHANGE_DATE': stamp,
        'ADD_DATE': stamp,
        'ADD_USER': changed_by,
    })

    return {'prompts': [{'code': 'RA100', 'type': 'P',
                         'message': 'Ticket ' + str(ticket_no) + ' reassigned to ' + new_agent + '.'}]}
