# project: Support360
# object_type: T
# object_name: support360_manage_all_tickets
# event_type: pre_commit
# function_name: log_ticket_admin_change
# language: python
# description: Write an Activity/History Log entry for every Admin change to a ticket
# functional_specification: For the header form (SUPPORT360_TICKET), on both add and edit: build a log entry line with the current timestamp, the changed-by user (current logged in user), the action_type ('Created' on add, else 'Edited' or 'Status-Changed' when STATUS differs from the previous stored value, or 'Assigned'/'Reassigned' when ASSIGNED_AGENT differs, or 'Commented' when NEW_COMMENT is non-empty, or 'Attachment-Added' when ATTACHMENT differs, or 'Closed' when STATUS becomes 'Closed'), and for each changed field the field name, old value and new value. Append the formatted entry (or entries, one per changed field) to the ACTIVITY_HISTORY text column of the header row before commit. When NEW_COMMENT is non-empty, also append a formatted 'commented-by / commented-date / text' block to AGENT_COMMENTS and clear NEW_COMMENT. When STATUS is being set to 'Closed', stamp CLOSED_DATE = now() and CLOSED_BY = current user if not already set. Return null on success; return {"error": "..."} only on an unrecoverable failure (never block a normal save for logging).
# business_logic: Write an Activity/History Log entry for every Admin change to a ticket

TRACKED = [
    'TITLE', 'DESCRIPTION', 'CATEGORY_CODE', 'PRIORITY_CODE', 'STATUS',
    'ASSIGNED_AGENT', 'REASSIGN_TO_AGENT', 'ATTACHMENT', 'RESOLUTION_NOTES',
]


def _get(row, name):
    """Case-insensitive column read from a row dict."""
    if not isinstance(row, dict):
        return None
    if name in row:
        return row[name]
    low = name.lower()
    for k, v in row.items():
        if str(k).lower() == low:
            return v
    return None


def _txt(v):
    return '' if v is None else str(v).strip()


def run(args):
    try:
        header = args.get('header') or {}
        action = (args.get('action') or 'add').lower()
        txn_id = args.get('txn_id')

        ticket_no = _txt(_get(header, 'TICKET_NO'))
        if not ticket_no and not txn_id:
            return None

        user = (_txt(_get(header, 'CHG_USER'))
                or _txt(_get(header, 'ADD_USER'))
                or 'SYSTEM')
        stamp = now().strftime('%Y-%m-%d %H:%M:%S')

        # ---- previous stored row (edit only) -------------------------------
        old = None
        if action == 'update':
            if txn_id:
                old = db.query_one(
                    'SELECT * FROM ' + db.t('SUPPORT360_TICKET') + ' WHERE ID = :i',
                    {'i': txn_id})
            if old is None and ticket_no:
                old = db.query_one(
                    'SELECT * FROM ' + db.t('SUPPORT360_TICKET') + ' WHERE TICKET_NO = :t',
                    {'t': ticket_no})

        new_status = _txt(_get(header, 'STATUS'))
        new_agent = _txt(_get(header, 'ASSIGNED_AGENT'))
        new_attach = _txt(_get(header, 'ATTACHMENT'))
        comment = _txt(_get(header, 'NEW_COMMENT'))

        # If the Admin typed a name into REASSIGN_TO_AGENT (instead of using the
        # dedicated Assign/Reassign form_action buttons) while moving the ticket to
        # 'Assigned'/'In Progress' and left ASSIGNED_AGENT blank, treat that typed
        # name as the real new agent so it actually gets recorded on the ticket.
        reassign_to_agent = _txt(_get(header, 'REASSIGN_TO_AGENT'))
        resolved_agent = new_agent
        apply_reassign = (new_status in ('Assigned', 'In Progress')
                           and not new_agent and reassign_to_agent)
        if apply_reassign:
            resolved_agent = reassign_to_agent

        old_status = _txt(_get(old, 'STATUS')) if old else ''
        old_agent = _txt(_get(old, 'ASSIGNED_AGENT')) if old else ''
        old_attach = _txt(_get(old, 'ATTACHMENT')) if old else ''

        # ---- decide the action_type ----------------------------------------
        if action == 'add' or old is None:
            action_type = 'Created'
        elif new_status == 'Closed' and old_status != 'Closed':
            action_type = 'Closed'
        elif new_status != old_status:
            action_type = 'Status-Changed'
        elif resolved_agent != old_agent:
            action_type = 'Assigned' if not old_agent else 'Reassigned'
        elif comment:
            action_type = 'Commented'
        elif new_attach != old_attach:
            action_type = 'Attachment-Added'
        else:
            action_type = 'Edited'

        # ---- build one log line per changed field --------------------------
        lines = []
        if action == 'add' or old is None:
            lines.append('[%s] %s | by %s | Ticket %s created (STATUS=%s)'
                         % (stamp, action_type, user, ticket_no,
                            new_status or 'Open'))
        else:
            for col in TRACKED:
                ov = _txt(_get(old, col))
                nv = resolved_agent if col == 'ASSIGNED_AGENT' else _txt(_get(header, col))
                if ov != nv:
                    lines.append('[%s] %s | by %s | field=%s | old=%s | new=%s'
                                 % (stamp, action_type, user, col,
                                    ov or '(blank)', nv or '(blank)'))
            if comment:
                lines.append('[%s] Commented | by %s | field=NEW_COMMENT | '
                             'old=(blank) | new=%s' % (stamp, user, comment))
            if not lines:
                lines.append('[%s] %s | by %s | no tracked field changed'
                             % (stamp, action_type, user))

        sets = {}

        if apply_reassign:
            sets['ASSIGNED_AGENT'] = resolved_agent
            sets['REASSIGN_TO_AGENT'] = None

        prev_hist = (_txt(_get(old, 'ACTIVITY_HISTORY')) if old
                     else _txt(_get(header, 'ACTIVITY_HISTORY')))
        sets['ACTIVITY_HISTORY'] = ((prev_hist + '\n') if prev_hist else '') + '\n'.join(lines)

        # ---- agent comment block -------------------------------------------
        if comment:
            prev_cmt = (_txt(_get(old, 'AGENT_COMMENTS')) if old
                        else _txt(_get(header, 'AGENT_COMMENTS')))
            block = ('commented-by: %s\ncommented-date: %s\ntext: %s\n---'
                     % (user, stamp, comment))
            sets['AGENT_COMMENTS'] = ((prev_cmt + '\n') if prev_cmt else '') + block
            sets['NEW_COMMENT'] = None

        # ---- closure stamps --------------------------------------------------
        if new_status == 'Closed':
            closed_date = _get(header, 'CLOSED_DATE') or (_get(old, 'CLOSED_DATE') if old else None)
            closed_by = (_txt(_get(header, 'CLOSED_BY'))
                         or (_txt(_get(old, 'CLOSED_BY')) if old else ''))
            if is_empty(closed_date):
                sets['CLOSED_DATE'] = now()
            if not closed_by:
                sets['CLOSED_BY'] = user

        if txn_id:
            db.update(db.t('SUPPORT360_TICKET'), sets, {'ID': txn_id})
        else:
            db.update(db.t('SUPPORT360_TICKET'), sets, {'TICKET_NO': ticket_no})

        return None
    except Exception:
        # Logging must never block a normal save.
        return None
