# project: Support360
# object_type: T
# object_name: support360_create_ticket
# event_type: pre_commit
# function_name: resolve_raised_by_name
# language: python
# description: Resolve the ticket-raiser's email from their user id
# functional_specification: Before a new SUPPORT360_TICKET row is committed, take the RAISED_BY value already set on the row (the current logged-in user's id) and look up that user's EMAIL via the platform's user/session login directory (never SUPPORT360_AGENT). Set RAISED_BY_NAME to the resolved email on this row. If no email can be resolved, fall back to the raw RAISED_BY id so the field is never blank. Return {"updates": {"raised_by_name": <resolved value>}}. Must run unconditionally on every ticket save and must never block or roll back the save.
# business_logic: Resolve the ticket-raiser's email from their user id


def _resolve_email(raised_by):
    # Look up the raiser's email via the platform's user/session login
    # directory (never SUPPORT360_AGENT). Defensive: never let a lookup
    # failure abort the ticket save.
    try:
        row = db.query_one(
            'SELECT EMAIL FROM ' + db.t('users') + ' WHERE ID = :u',
            {'u': raised_by}
        )
        if row and not_empty(row.get('EMAIL')):
            return str(row['EMAIL']).strip()
    except Exception:
        pass
    return None


def run(args):
    try:
        header = args.get('header') or {}
        raised_by = str(coalesce(header.get('RAISED_BY'), args.get('RAISED_BY'), '') or '').strip()
        if not raised_by:
            return None

        # Fall back to the raw id so RAISED_BY_NAME is never blank (VARCHAR(100)).
        resolved = (_resolve_email(raised_by) or raised_by)[:100]
        header['RAISED_BY_NAME'] = resolved

        # Persist on the save's own transaction.
        ticket_no = header.get('TICKET_NO')
        if not_empty(ticket_no):
            db.update('SUPPORT360_TICKET', {'RAISED_BY_NAME': resolved},
                      {'TICKET_NO': ticket_no})

        return {'updates': {'raised_by_name': resolved}}
    except Exception:
        # Must never block or roll back the ticket save.
        return None
