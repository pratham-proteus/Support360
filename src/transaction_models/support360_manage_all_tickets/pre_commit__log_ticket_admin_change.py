# project: Support360
# object_type: T
# object_name: support360_manage_all_tickets
# event_type: pre_commit
# function_name: log_ticket_admin_change
# language: python
# description: Write an Activity/History Log entry for every Admin change to a ticket
# functional_specification: For the header form (SUPPORT360_TICKET), on both add and edit: build a log entry line with the current timestamp, the changed-by user (current logged in user), the action_type ('Created' on add, else 'Edited' or 'Status-Changed' when STATUS differs from the previous stored value, or 'Assigned' when ASSIGNED_AGENT differs, or 'Commented' when NEW_COMMENT is non-empty, or 'Attachment-Added' when ATTACHMENT differs, or 'Closed' when STATUS becomes 'Closed'), and for each changed field the field name, old value and new value. Append the formatted entry (or entries, one per changed field) to the ACTIVITY_HISTORY text column of the header row before commit. When NEW_COMMENT is non-empty, also append a formatted 'commented-by / commented-date / text' block to AGENT_COMMENTS and clear NEW_COMMENT. When STATUS is being set to 'Closed', stamp CLOSED_DATE = now() and CLOSED_BY = current user if not already set. Return null on success; return {"error": "..."} only on an unrecoverable failure (never block a normal save for logging).
# business_logic: Write an Activity/History Log entry for every Admin change to a ticket

# Fields that are tracked field-by-field in the activity history.
_TRACKED_FIELDS = [
    'TITLE',
    'DESCRIPTION',
    'CATEGORY_CODE',
    'PRIORITY_CODE',
    'STATUS',
    'ASSIGNED_AGENT',
    'ATTACHMENT',
    'RESOLUTION_NOTES',
]


def _pick(row, name):
    """Read a value case-insensitively from a payload / result-row dict."""
    if not row:
        return None
    for key in (name, name.lower(), name.upper()):
        if key in row:
            return row[key]
    return None


def _has(row, name):
    """True when the payload actually carries the column (present, even if blank)."""
    if not row:
        return False
    for key in (name, name.lower(), name.upper()):
        if key in row:
            return True
    return False


def _txt(v):
    """Normalise a value to a trimmed string ('' when null/blank)."""
    if v is None:
        return ''
    return str(v).strip()


def _stamp():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def run(args):
    header = args.get('header') or {}

    ticket_no = _txt(_pick(header, 'TICKET_NO'))
    if ticket_no == '':
        return None

    changed_by = _txt(coalesce(
        _pick(header, 'CHG_USER'),
        _pick(header, 'ADD_USER'),
        _pick(header, 'RAISED_BY'),
        'SYSTEM'
    )) or 'SYSTEM'

    try:
        prior = db.query_one(
            'SELECT TITLE, DESCRIPTION, CATEGORY_CODE, PRIORITY_CODE, STATUS,'
            ' ASSIGNED_AGENT, ATTACHMENT, RESOLUTION_NOTES, AGENT_COMMENTS,'
            ' ACTIVITY_HISTORY, CLOSED_DATE, CLOSED_BY'
            ' FROM ' + db.t('SUPPORT360_TICKET') +
            ' WHERE TICKET_NO = :t',
            {'t': ticket_no}
        )

        is_add = prior is None
        now_txt = _stamp()
        lines = []

        if is_add:
            lines.append('[%s] %s - Created - Ticket %s raised'
                         % (now_txt, changed_by, ticket_no))
        else:
            for field in _TRACKED_FIELDS:
                if not _has(header, field):
                    continue

                new_val = _txt(_pick(header, field))
                old_val = _txt(_pick(prior, field))
                if new_val == old_val:
                    continue

                # Decide the action type this particular field change represents.
                if field == 'STATUS':
                    action = iif(new_val == 'Closed', 'Closed', 'Status-Changed')
                elif field == 'ASSIGNED_AGENT':
                    # Agent changes made through the normal ASSIGNED_AGENT field.
                    action = 'Assigned'
                elif field == 'ATTACHMENT':
                    action = 'Attachment-Added'
                else:
                    action = 'Edited'

                lines.append('[%s] %s - %s - %s: "%s" -> "%s"'
                             % (now_txt, changed_by, action, field, old_val, new_val))

        updates = {}

        # A new comment is logged and folded into the running AGENT_COMMENTS block.
        new_comment = _txt(_pick(header, 'NEW_COMMENT'))
        if new_comment != '':
            lines.append('[%s] %s - Commented' % (now_txt, changed_by))

            old_comments = '' if is_add else _txt(_pick(prior, 'AGENT_COMMENTS'))
            block = ('Commented By : %s\nCommented Date : %s\n%s'
                     % (changed_by, now_txt, new_comment))
            updates['AGENT_COMMENTS'] = iif(
                old_comments == '', block, old_comments + '\n\n' + block)
            updates['NEW_COMMENT'] = ''

        # Stamp closure details the first time the ticket moves to Closed.
        if _txt(_pick(header, 'STATUS')) == 'Closed':
            if is_empty(_pick(header, 'CLOSED_DATE')) and (
                    is_add or is_empty(_pick(prior, 'CLOSED_DATE'))):
                updates['CLOSED_DATE'] = datetime.datetime.now()
            if is_empty(_pick(header, 'CLOSED_BY')) and (
                    is_add or is_empty(_pick(prior, 'CLOSED_BY'))):
                updates['CLOSED_BY'] = changed_by

        if lines:
            old_history = _txt(_pick(header, 'ACTIVITY_HISTORY'))
            if old_history == '' and not is_add:
                old_history = _txt(_pick(prior, 'ACTIVITY_HISTORY'))
            entry = '\n'.join(lines)
            updates['ACTIVITY_HISTORY'] = iif(
                old_history == '', entry, old_history + '\n' + entry)

        if not updates:
            return None

        return {'updates': updates}
    except Exception as exc:
        # Logging must never block a normal save unless the failure is unrecoverable.
        return {'error': 'Failed to write ticket activity log: ' + str(exc)}
