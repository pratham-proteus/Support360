# project: Support360
# object_type: T
# object_name: support360_ticket_assignment
# event_type: form_action
# function_name: assign_agent
# form_no: 1
# action_name: Assign Agent
# language: python
# description: Assign each ticked Pending ticket to the next Active agent (round-robin by AGENT_ID) whose PREFERENCE covers its CATEGORY
# functional_specification: Runs once per ticked row with that row's TICKET_NO. Re-reads the ticket; acts only when STATUS = Pending and ASSIGNED_AGENT is empty (else returns an already-assigned message, no update). Candidates are SUPPORT360_AGENT rows with AGENT_STATUS = Active (availability ignored) whose comma-separated PREFERENCE (trimmed, case-insensitive) contains the ticket CATEGORY, ordered by AGENT_ID ascending. Round-robin: the agent after the one most recently assigned a ticket in that category (read from the DB each call so earlier rows of the same bulk run count), wrapping to the first; first-ever ticket gets the first agent. Writes ASSIGNED_AGENT, STATUS = Assigned, CHG_DATE, CHG_USER and a best-effort SUPPORT360_TICKET_ACTLOG row. No match: no update, message that the ticket is still pending.
# business_logic: Round-robin assign a Pending ticket to an Active agent whose PREFERENCE matches its CATEGORY


def _prefs(raw):
    return [p.strip().upper() for p in str(raw or '').split(',') if p.strip()]


def run(args):
    ticket_no = args.get('ticket_no')
    if is_empty(ticket_no):
        return 'Ticket number is required to assign an agent.'
    ticket_no = str(ticket_no).strip()

    ticket = db.query_one(
        'SELECT STATUS, ASSIGNED_AGENT, CATEGORY FROM ' + db.t('SUPPORT360_TICKET') +
        ' WHERE TICKET_NO = :t', {'t': ticket_no})
    if not ticket:
        return 'Ticket ' + ticket_no + ' could not be found.'

    if str(ticket.get('STATUS') or '').strip() != 'Pending' or str(ticket.get('ASSIGNED_AGENT') or '').strip() != '':
        return {'message': 'Ticket ' + ticket_no + ' is already assigned, unchanged'}

    category = str(ticket.get('CATEGORY') or '').strip()
    cat_key = category.upper()

    agents = db.query(
        'SELECT AGENT_ID, AGENT_NAME, PREFERENCE FROM ' + db.t('SUPPORT360_AGENT') +
        ' WHERE AGENT_STATUS = :s ORDER BY AGENT_ID ASC', {'s': 'Active'})
    cands = [a for a in agents if cat_key and cat_key in _prefs(a.get('PREFERENCE'))]
    if not cands:
        return {'message': 'Ticket ' + ticket_no + ' still pending: no active agent matches category ' + category}

    ids = [str(a['AGENT_ID']).strip() for a in cands]

    # Re-read from the DB every call so tickets assigned earlier in the same bulk run count.
    last_agent = None
    recent = db.query(
        'SELECT ASSIGNED_AGENT FROM ' + db.t('SUPPORT360_TICKET') +
        ' WHERE CATEGORY = :c AND TICKET_NO <> :t AND ASSIGNED_AGENT IS NOT NULL'
        " AND ASSIGNED_AGENT <> ''"
        ' ORDER BY COALESCE(CHG_DATE, CREATED_DATE) DESC, TICKET_NO DESC',
        {'c': category, 't': ticket_no})
    for r in recent:
        aid = str(r['ASSIGNED_AGENT']).strip()
        if aid in ids:
            last_agent = aid
            break

    if last_agent:
        agent_id = next((i for i in ids if i > last_agent), ids[0])
    else:
        agent_id = ids[0]
    agent = cands[ids.index(agent_id)]
    agent_name = agent.get('AGENT_NAME') or agent_id

    user = str(coalesce(args.get('CHG_USER'), args.get('chg_user'), 'System'))
    db.update('SUPPORT360_TICKET',
              {'ASSIGNED_AGENT': agent_id, 'STATUS': 'Assigned',
               'CHG_DATE': now(), 'CHG_USER': user[:10]},
              {'TICKET_NO': ticket_no})

    try:
        db.insert('SUPPORT360_TICKET_ACTLOG', {
            'ID': ('A' + now().strftime('%Y%m%d%H%M%S%f') + ticket_no)[:36],
            'TICKET_NO': ticket_no,
            'ACTION_TYPE': 'Assigned',
            'FIELD_CHANGED': 'ASSIGNED_AGENT',
            'OLD_VALUE': None,
            'NEW_VALUE': agent_id,
            'CHANGED_BY': user[:36],
            'CHANGE_DATE': now(),
        })
    except Exception as exc:
        log('assign_agent: activity log failed for ' + ticket_no + ': ' + str(exc))

    return {'message': 'Ticket ' + ticket_no + ' assigned to ' + str(agent_name)}
