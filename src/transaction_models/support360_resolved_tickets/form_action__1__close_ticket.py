# project: Support360
# object_type: T
# object_name: support360_resolved_tickets
# event_type: form_action
# function_name: close_ticket
# form_no: 1
# action_name: Close Ticket
# language: python
# description: Close a resolved ticket
# functional_specification: Payload carries the current row's columns flat, including TICKET_NO/ticket_no and STATUS/status. Update the SUPPORT360_TICKET row for this TICKET_NO: set STATUS = 'Closed', CLOSED_DATE = the current timestamp, and CLOSED_BY = the current logged-in user's id, only if STATUS is currently 'Resolved' (otherwise raise a validation error 'Only Resolved tickets can be closed'). Insert an entry into SUPPORT360_TICKET_ACTLOG for this TICKET_NO recording ACTION_TYPE = 'Status-Changed', FIELD_CHANGED = 'STATUS', OLD_VALUE = 'Resolved', NEW_VALUE = 'Closed', following the same activity-log population pattern used by support360_ticket_assignment's pre_commit log entries and support360_resolved_tickets' reopen_ticket action. Return a confirmation message on success, or {"error": "..."} to abort if the ticket cannot be closed.
# business_logic: Close a resolved ticket


def _current_user(args):
    return str(coalesce(args.get('CHG_USER'), args.get('ADD_USER'),
                        args.get('RAISED_BY'), '')).strip()


def _log_id(ticket_no):
    # Deterministic-but-unique 36 char id (no uuid module in the sandbox).
    raw = 'LOG-%s-%s' % (now().strftime('%Y%m%d%H%M%S%f'), str(ticket_no))
    return raw[:36]


def run(args):
    ticket_no = args.get('TICKET_NO')
    if is_empty(ticket_no):
        return {'error': 'No ticket selected.'}

    row = db.query_one(
        'SELECT TICKET_NO, STATUS, ACTIVITY_HISTORY FROM ' + db.t('SUPPORT360_TICKET') +
        ' WHERE TICKET_NO = :t', {'t': ticket_no})
    if not row:
        return {'error': 'Ticket %s not found.' % ticket_no}

    old_status = str(coalesce(row.get('STATUS'), '')).strip()
    if old_status != 'Resolved':
        return {'error': 'Only Resolved tickets can be closed'}

    user = _current_user(args)
    stamp = now().strftime('%Y-%m-%d %H:%M:%S')

    entry = '%s | Status-Changed | STATUS | Resolved -> Closed | %s' % (stamp, user)
    history = coalesce(row.get('ACTIVITY_HISTORY'))
    history = entry if is_empty(history) else str(history).rstrip() + '\n' + entry

    db.update('SUPPORT360_TICKET', {
        'STATUS': 'Closed',
        'CLOSED_DATE': stamp,
        'CLOSED_BY': user,
        'ACTIVITY_HISTORY': history,
        'CHG_DATE': stamp,
        'CHG_USER': user,
    }, {'TICKET_NO': ticket_no})

    db.insert('SUPPORT360_TICKET_ACTLOG', {
        'ID': _log_id(ticket_no),
        'TICKET_NO': ticket_no,
        'ACTION_TYPE': 'Status-Changed',
        'FIELD_CHANGED': 'STATUS',
        'OLD_VALUE': 'Resolved',
        'NEW_VALUE': 'Closed',
        'CHANGED_BY': user,
        'CHANGE_DATE': stamp,
        'ADD_DATE': stamp,
        'ADD_USER': user,
    })

    return {'prompts': [{'code': 'RTCLOSE1', 'field': 'status',
                         'message': 'Ticket %s closed successfully.' % ticket_no}]}
