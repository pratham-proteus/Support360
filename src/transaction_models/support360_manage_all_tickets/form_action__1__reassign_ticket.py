# project: Support360
# object_type: T
# object_name: support360_manage_all_tickets
# event_type: form_action
# function_name: reassign_ticket
# form_no: 1
# action_name: Reassign
# language: python
# description: Reassign a ticket to a different agent, keeping the current status
# functional_specification: Given the ticket payload (TICKET_NO, STATUS, ASSIGNED_AGENT, REASSIGN_TO_AGENT), require STATUS in ('Open','Assigned','In Progress') and REASSIGN_TO_AGENT non-empty. Update SUPPORT360_TICKET setting ASSIGNED_AGENT = REASSIGN_TO_AGENT (STATUS unchanged), CHG_DATE = now(), CHG_USER = current user. Append an entry to ACTIVITY_HISTORY recording action_type 'Reassigned', field_changed 'ASSIGNED_AGENT', old_value (previous ASSIGNED_AGENT), new_value (REASSIGN_TO_AGENT), changed_by (current user) and the timestamp. Return {"message": "Ticket reassigned successfully"} on success or {"error": "..."} if the status does not allow reassignment or no target agent was supplied.
# business_logic: Reassign a ticket to a different agent (admin: no restriction on current holder), keeping/normalizing status

ALLOWED_STATUS = ('Assigned', 'In Progress')


def _txt(v):
    return '' if v is None else str(v).strip()


def run(args):
    ticket_no = _txt(args.get('TICKET_NO'))
    target_agent = _txt(args.get('REASSIGN_TO_AGENT'))
    user = _txt(args.get('CHG_USER')) or _txt(args.get('ADD_USER')) or 'SYSTEM'

    if not ticket_no:
        return {'error': 'Ticket number is missing'}
    if not target_agent:
        return {'error': 'Select the agent to reassign the ticket to'}

    row = db.query_one(
        'SELECT TICKET_NO, STATUS, ASSIGNED_AGENT '
        'FROM ' + db.t('SUPPORT360_TICKET') + ' WHERE TICKET_NO = :t',
        {'t': ticket_no})
    if row is None:
        return {'error': 'Ticket ' + ticket_no + ' not found'}

    status = _txt(row.get('STATUS'))
    if status not in ALLOWED_STATUS:
        return {'error': "Ticket cannot be reassigned: status is '" + status
                         + "', reassignment is allowed only for Assigned "
                           "or In Progress tickets"}

    old_agent = _txt(row.get('ASSIGNED_AGENT'))

    new_status = 'Assigned' if status == 'In Progress' else status
    stamp = now()

    db.update(db.t('SUPPORT360_TICKET'), {
        'ASSIGNED_AGENT': target_agent,
        'STATUS': new_status,
        'REASSIGN_TO_AGENT': None,
    }, {'TICKET_NO': ticket_no})

    db.insert(db.t('SUPPORT360_TICKET_ACTLOG'), {
        'TICKET_NO': ticket_no,
        'ACTION_TYPE': 'Reassigned',
        'FIELD_CHANGED': 'ASSIGNED_AGENT',
        'OLD_VALUE': old_agent or '',
        'NEW_VALUE': target_agent,
        'CHANGED_BY': user,
        'CHANGE_DATE': stamp,
    })

    return {'message': 'Ticket reassigned successfully'}
