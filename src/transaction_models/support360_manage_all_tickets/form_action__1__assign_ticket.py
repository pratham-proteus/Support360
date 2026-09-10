# project: Support360
# object_type: T
# object_name: support360_manage_all_tickets
# event_type: form_action
# function_name: assign_ticket
# form_no: 1
# action_name: Assign
# language: python
# description: Assign an unassigned ticket to the current admin-selected agent
# functional_specification: Given the ticket payload (TICKET_NO, STATUS, ASSIGNED_AGENT, REASSIGN_TO_AGENT), require STATUS = 'Open' and REASSIGN_TO_AGENT non-empty (used here as the target agent to assign). Update SUPPORT360_TICKET setting ASSIGNED_AGENT = REASSIGN_TO_AGENT, STATUS = 'Assigned', CHG_DATE = now(), CHG_USER = current user. Append an entry to ACTIVITY_HISTORY recording action_type 'Assigned', field_changed 'ASSIGNED_AGENT', old_value (blank), new_value (the agent), changed_by (current user) and the timestamp. Return {"message": "Ticket assigned successfully"} on success or {"error": "..."} if STATUS is not Open or no agent was supplied.
# business_logic: Assign an unassigned ticket to the current admin-selected agent


def _txt(v):
    return '' if v is None else str(v).strip()


def run(args):
    ticket_no = _txt(args.get('TICKET_NO'))
    target_agent = _txt(args.get('ASSIGNED_AGENT'))
    user = _txt(args.get('CHG_USER')) or _txt(args.get('ADD_USER')) or 'SYSTEM'

    if not ticket_no:
        return {'error': 'Ticket number is missing'}
    if not target_agent:
        return {'error': 'Select an agent to assign the ticket to'}

    row = db.query_one(
        'SELECT TICKET_NO, STATUS, ASSIGNED_AGENT '
        'FROM ' + db.t('SUPPORT360_TICKET') + ' WHERE TICKET_NO = :t',
        {'t': ticket_no})
    if row is None:
        return {'error': 'Ticket ' + ticket_no + ' not found'}

    # Admin may assign any ticket regardless of current ASSIGNED_AGENT,
    # but the ticket must be Open before assignment.
    status = _txt(row.get('STATUS'))
    if status != 'Open':
        return {'error': 'Only Open tickets can be assigned'}

    old_agent = _txt(row.get('ASSIGNED_AGENT'))
    change_date = now()

    # Persist the update to SUPPORT360_TICKET keyed by TICKET_NO
    db.update(db.t('SUPPORT360_TICKET'), {
        'ASSIGNED_AGENT': target_agent,
        'STATUS': 'Assigned',
        'CHG_DATE': change_date,
        'CHG_USER': user,
    }, {'TICKET_NO': ticket_no})

    # Insert activity log entry
    db.insert(db.t('SUPPORT360_TICKET_ACTLOG'), {
        'TICKET_NO': ticket_no,
        'ACTION_TYPE': 'Assigned',
        'FIELD_CHANGED': 'ASSIGNED_AGENT',
        'OLD_VALUE': old_agent,
        'NEW_VALUE': target_agent,
        'CHANGED_BY': user,
        'CHANGE_DATE': change_date,
    })

    return {'message': 'Ticket assigned successfully'}
