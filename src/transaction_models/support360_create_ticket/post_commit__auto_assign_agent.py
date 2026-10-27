# project: Support360
# object_type: T
# object_name: support360_create_ticket
# event_type: post_commit
# function_name: auto_assign_agent
# language: python
# description: Auto-assign a new ticket to the Active agent whose PREFERENCE matches its CATEGORY
# functional_specification: After a new SUPPORT360_TICKET row is committed (action = add), if the ticket has no ASSIGNED_AGENT yet (the CATEGORY item_change normally assigns it on the form; this covers imports, the API and the Assistant), select from SUPPORT360_AGENT the Active agents whose PREFERENCE equals the ticket's CATEGORY (case/space insensitive), preferring AGENT_AVAILABILITY = 'Available', then the lowest AGENT_ID. An Available agent sets ASSIGNED_AGENT + STATUS = 'Assigned'; an Occupied one sets ASSIGNED_AGENT + STATUS = 'Queued'; no match leaves STATUS = 'Pending'. An assignment is recorded in SUPPORT360_TICKET_ACTLOG. Runs after the save has committed and must never block it.
# business_logic: Auto-assign a new ticket to the Active agent whose PREFERENCE matches its CATEGORY

ACTIVITY_LOG_TABLE = 'SUPPORT360_TICKET_ACTLOG'


def _get(row, name):
    return coalesce(row.get(name.upper()), row.get(name.lower()))


def run(args):
    ticket_no = None
    try:
        if str(args.get('action') or '').lower() != 'add':
            return None
        header = args.get('header') or {}
        ticket_no = _get(header, 'TICKET_NO')
        if is_empty(ticket_no) or not_empty(_get(header, 'ASSIGNED_AGENT')):
            # Nothing to key on, or already assigned on the form.
            return None
        ticket_no = str(ticket_no).strip()
        category = _get(header, 'CATEGORY')
        if is_empty(category):
            return None
        category = str(category).strip().upper()

        chosen = db.query_one(
            'SELECT AGENT_ID, AGENT_AVAILABILITY FROM ' + db.t('SUPPORT360_AGENT') +
            ' WHERE AGENT_STATUS = :status'
            ' AND TRIM(UPPER(PREFERENCE)) = :pref'
            ' AND AGENT_ID IS NOT NULL'
            ' ORDER BY CASE WHEN AGENT_AVAILABILITY = :available THEN 0 ELSE 1 END, AGENT_ID',
            {'pref': category, 'status': 'Active', 'available': 'Available'})
        if not chosen:
            return None

        agent_id = str(chosen['AGENT_ID']).strip()
        available = str(chosen['AGENT_AVAILABILITY'] or '').strip() == 'Available'
        status = 'Assigned' if available else 'Queued'

        db.update('SUPPORT360_TICKET',
                  {'ASSIGNED_AGENT': agent_id, 'STATUS': status},
                  {'TICKET_NO': ticket_no})

        try:
            db.insert(ACTIVITY_LOG_TABLE, {
                'ID': ('A' + now().strftime('%Y%m%d%H%M%S%f') + ticket_no)[:36],
                'TICKET_NO': ticket_no,
                'ACTION_TYPE': status,
                'FIELD_CHANGED': 'ASSIGNED_AGENT',
                'OLD_VALUE': None,
                'NEW_VALUE': agent_id,
                'CHANGED_BY': coalesce(_get(header, 'ADD_USER'), 'System'),
                'CHANGE_DATE': now(),
            })
        except Exception as exc:
            # The log line is best-effort; the assignment above stands.
            log('auto_assign_agent: activity log failed for ' + ticket_no + ': ' + str(exc))
    except Exception as exc:
        log('auto_assign_agent failed for ' + str(ticket_no) + ': ' + str(exc))
    return None
