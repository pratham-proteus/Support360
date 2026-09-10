# project: Support360
# object_type: T
# object_name: support360_ticket_assignment
# event_type: pre_commit
# function_name: log_ticket_assignment
# language: python
# description: Write assignment change to ticket activity log
# functional_specification: On save of the support360_ticket_assignment transaction, compare the incoming ASSIGNED_AGENT to the ticket's prior ASSIGNED_AGENT value on SUPPORT360_TICKET for this TICKET_NO. If it changed, insert a row into SUPPORT360_TICKET_ACTLOG with a generated ID (uuid), TICKET_NO, ACTION_TYPE = 'Reassigned' (or 'Assigned' if the prior value was blank/null), FIELD_CHANGED = 'ASSIGNED_AGENT', OLD_VALUE = prior assigned agent (or blank), NEW_VALUE = new assigned agent, CHANGED_BY = the current logged-in user, and CHANGE_DATE = current timestamp. If the value did not change, do nothing. Return an error to roll back the save only if the log insert fails.
# business_logic: Write assignment change to ticket activity log


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
    header = args.get('header') or {}

    ticket_no = _txt(_pick(header, 'TICKET_NO'))
    if ticket_no == '':
        return None

    new_agent = _txt(_pick(header, 'ASSIGNED_AGENT'))

    prior = db.query_one(
        'SELECT ASSIGNED_AGENT FROM ' + db.t('SUPPORT360_TICKET') +
        ' WHERE TICKET_NO = :t',
        {'t': ticket_no}
    )
    if prior is None:
        # Nothing on file to compare against - nothing to log.
        return None

    old_agent = _txt(_pick(prior, 'ASSIGNED_AGENT'))

    if old_agent == new_agent:
        return None

    changed_by = _txt(coalesce(
        _pick(header, 'CHG_USER'),
        _pick(header, 'ADD_USER'),
        _pick(header, 'RAISED_BY'),
        'SYSTEM'
    )) or 'SYSTEM'

    try:
        db.insert('SUPPORT360_TICKET_ACTLOG', {
            'ID': _new_uuid(),
            'TICKET_NO': ticket_no,
            'ACTION_TYPE': iif(old_agent == '', 'Assigned', 'Reassigned'),
            'FIELD_CHANGED': 'ASSIGNED_AGENT',
            'OLD_VALUE': old_agent,
            'NEW_VALUE': new_agent,
            'CHANGED_BY': changed_by,
            'CHANGE_DATE': now(),
        })
    except Exception as exc:
        return {'error': 'Failed to write ticket assignment activity log: ' + str(exc)}

    return None
