# project: Support360
# object_type: T
# object_name: support360_resolved_tickets
# event_type: form_action
# function_name: reopen_ticket
# form_no: 1
# action_name: Reopen Ticket
# language: python
# description: Reopen a resolved ticket
# functional_specification: Payload carries the current row's columns flat, including TICKET_NO/ticket_no and STATUS/status. Update the SUPPORT360_TICKET row for this TICKET_NO: set STATUS = 'In Progress', but only if the ticket's current STATUS is 'Resolved' (otherwise return a validation error 'Only Resolved tickets can be reopened'). Insert an entry into SUPPORT360_TICKET_ACTLOG for this TICKET_NO recording ACTION_TYPE = 'Status-Changed', FIELD_CHANGED = 'STATUS', OLD_VALUE = 'Resolved', NEW_VALUE = 'In Progress', CHANGED_BY = current user, CHANGE_DATE = now, following the same activity-log population pattern used by support360_ticket_assignment's pre_commit log entries. Return a confirmation message on success, or {"error": "..."} to abort if the ticket cannot be reopened.
# business_logic: Reopen a resolved ticket


def _pick(row, name):
    """Read a value case-insensitively from a payload / result-row dict."""
    if not row:
        return None
    for key in (name, name.lower(), name.upper()):
        if key in row:
            return row[key]
    return None


def _txt(v):
    """Normalise a value to a trimmed string ('' when null/blank)."""
    if v is None:
        return ''
    return str(v).strip()


def _current_user(args):
    return _txt(coalesce(
        _pick(args, 'CHG_USER'),
        _pick(args, 'ADD_USER'),
        _pick(args, 'RAISED_BY'),
        'SYSTEM'
    )) or 'SYSTEM'


def _new_uuid():
    """Generate a uuid string (no uuid module in the sandbox -> ask the DB)."""
    try:
        val = db.scalar('SELECT gen_random_uuid()', {})
        if not_empty(val):
            return _txt(val)
    except Exception:
        pass
    # Fallback: build a uuid-shaped id from the current timestamp + randomness.
    stamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    rand = str(int(math.floor(math.fabs(math.sin(float(stamp[-9:])) * 1000000000))))
    raw = (stamp + rand + '0' * 32)[:32]
    return '%s-%s-%s-%s-%s' % (raw[0:8], raw[8:12], raw[12:16], raw[16:20], raw[20:32])


def run(args):
    ticket_no = _txt(_pick(args, 'TICKET_NO'))
    if ticket_no == '':
        return {'error': 'No ticket selected.'}

    row = db.query_one(
        'SELECT TICKET_NO, STATUS FROM ' + db.t('SUPPORT360_TICKET') +
        ' WHERE TICKET_NO = :t', {'t': ticket_no})
    if not row:
        return {'error': 'Ticket %s not found.' % ticket_no}

    old_status = _txt(_pick(row, 'STATUS'))
    if old_status != 'Resolved':
        return {'error': 'Only Resolved tickets can be reopened'}

    changed_by = _current_user(args)
    stamp = now()

    db.update('SUPPORT360_TICKET', {
        'STATUS': 'In Progress',
        'CHG_DATE': stamp,
        'CHG_USER': changed_by,
    }, {'TICKET_NO': ticket_no})

    try:
        db.insert('SUPPORT360_TICKET_ACTLOG', {
            'ID': _new_uuid(),
            'TICKET_NO': ticket_no,
            'ACTION_TYPE': 'Status-Changed',
            'FIELD_CHANGED': 'STATUS',
            'OLD_VALUE': 'Resolved',
            'NEW_VALUE': 'In Progress',
            'CHANGED_BY': changed_by,
            'CHANGE_DATE': stamp,
        })
    except Exception as exc:
        return {'error': 'Failed to write ticket activity log: ' + str(exc)}

    return {'prompts': [{'code': 'RTREOPEN1', 'field': 'status',
                         'message': 'Ticket %s reopened and set to In Progress.' % ticket_no}]}
