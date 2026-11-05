# project: Support360
# object_type: T
# object_name: support360_create_ticket
# event_type: post_commit
# function_name: auto_assign_agent
# language: python
# description: Auto-assign a new ticket to the Active agent whose PREFERENCE matches its CATEGORY
# functional_specification: After a new SUPPORT360_TICKET row is committed (action = add), if the ticket has no ASSIGNED_AGENT yet (the CATEGORY item_change normally assigns it on the form; this covers imports, the API and the Assistant), select from SUPPORT360_AGENT the Active agents whose PREFERENCE equals the ticket's CATEGORY (case/space insensitive), ignoring AGENT_AVAILABILITY entirely. Assign round-robin by ascending AGENT_ID: the agent after whoever most recently received a ticket in that category, wrapping to the lowest AGENT_ID. Always sets ASSIGNED_AGENT + STATUS = 'Assigned'; no match leaves STATUS = 'Pending'. An assignment is recorded in SUPPORT360_TICKET_ACTLOG. Runs after the save has committed and must never block it.
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

        active_agents = db.query(
            'SELECT AGENT_ID, AGENT_NAME, PREFERENCE FROM ' + db.t('SUPPORT360_AGENT') +
            ' WHERE AGENT_STATUS = :status'
            ' AND AGENT_ID IS NOT NULL'
            ' ORDER BY AGENT_ID ASC',
            {'status': 'Active'})
        if not active_agents:
            return None

        def _preferences(raw):
            # PREFERENCE stores a delimited list from the Agent Master multi-select.
            raw = str(raw or '')
            for sep in (',', ';', '|'):
                raw = raw.replace(sep, ',')
            return [p.strip().upper() for p in raw.split(',') if p.strip()]

        agent_ids = [str(a['AGENT_ID']).strip() for a in active_agents
                     if category in _preferences(a.get('PREFERENCE'))]
        if not agent_ids:
            return None

        last_ticket = db.query_one(
            'SELECT ASSIGNED_AGENT FROM ' + db.t('SUPPORT360_TICKET') +
            ' WHERE CATEGORY = :category'
            ' AND TICKET_NO != :ticket_no'
            ' AND ASSIGNED_AGENT IS NOT NULL'
            " AND ASSIGNED_AGENT <> ''"
            ' ORDER BY CREATED_DATE DESC, TICKET_NO DESC',
            {'category': category, 'ticket_no': ticket_no})

        last_agent_id = str(last_ticket['ASSIGNED_AGENT']).strip() if last_ticket else None
        if last_agent_id:
            # Round-robin: first matching agent past the last one assigned, wrapping to the lowest.
            agent_id = next((a for a in agent_ids if a > last_agent_id), agent_ids[0])
        else:
            agent_id = agent_ids[0]

        status = 'Assigned'

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
