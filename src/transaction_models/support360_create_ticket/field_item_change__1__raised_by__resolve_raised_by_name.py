# project: Support360
# object_type: T
# object_name: support360_create_ticket
# event_type: field_item_change
# function_name: resolve_raised_by_name
# form_no: 1
# field_name: raised_by
# language: python
# description: Resolve the ticket-raiser's display name from their user id
# functional_specification: When RAISED_BY is set (auto-filled with the current logged-in user's id at ticket creation), look up that user's display name via the platform's current user/session directory and set RAISED_BY_NAME to the resolved name on this SUPPORT360_TICKET row. Return {"updates": {"raised_by_name": <resolved display name>}}. If no display name can be resolved, fall back to the raw user id so the field is never blank. Never raise or block ticket creation.
# business_logic: Resolve the ticket-raiser's display name from their user id


def run(args):
    raised_by = args.get('RAISED_BY')

    # No raiser id yet - nothing to resolve.
    if is_empty(raised_by):
        return {'updates': {'raised_by_name': ''}}

    raised_by = str(raised_by).strip()
    resolved = None

    try:
        # 1) The raiser may themselves be a support agent - the agent master
        #    is the platform's user directory for support staff and carries
        #    the current logged-in user's display name.
        row = db.query_one(
            'SELECT AGENT_NAME FROM ' + db.t('SUPPORT360_AGENT') + ' WHERE AGENT_ID = :u',
            {'u': raised_by}
        )
        if row and not_empty(row.get('AGENT_NAME')):
            resolved = str(row['AGENT_NAME']).strip()

        # 2) Otherwise reuse the display name already recorded for this same
        #    user id on an earlier ticket (same directory identity, just
        #    resolved previously).
        if is_empty(resolved):
            row = db.query_one(
                'SELECT RAISED_BY_NAME FROM ' + db.t('SUPPORT360_TICKET') +
                ' WHERE RAISED_BY = :u AND RAISED_BY_NAME IS NOT NULL'
                ' ORDER BY CREATED_DATE DESC',
                {'u': raised_by}
            )
            if row and not_empty(row.get('RAISED_BY_NAME')):
                resolved = str(row['RAISED_BY_NAME']).strip()
    except Exception:
        # Directory lookup must never block ticket creation.
        resolved = None

    # 3) Fall back to the raw user id so the field is never blank.
    if is_empty(resolved):
        resolved = raised_by

    return {'updates': {'raised_by_name': resolved}}
