# project: Support360
# object_type: T
# object_name: support360_resolved_tickets
# event_type: form_action
# function_name: reopen_resolved_ticket
# form_no: 1
# action_name: Reopen Ticket
# language: python
# description: Reopen a Resolved ticket back to In Progress
# functional_specification: Given the current ticket's TICKET_NO, UPDATE SUPPORT360_TICKET SET STATUS = 'In Progress' WHERE TICKET_NO = the current ticket's TICKET_NO AND STATUS = 'Resolved'. If no row was updated (status is no longer Resolved), return an error. Insert an entry into SUPPORT360_TICKET_ACTLOG with a new ID, TICKET_NO = the ticket's TICKET_NO, ACTION_TYPE = 'Status-Changed', FIELD_CHANGED = 'STATUS', OLD_VALUE = 'Resolved', NEW_VALUE = 'In Progress', CHANGED_BY = the current user id, CHANGE_DATE = current timestamp. Return a confirmation message such as 'Ticket <TICKET_NO> reopened and sent back to In Progress.'
# business_logic: Reopen a Resolved ticket back to In Progress


def run(args):
    ticket_no = args.get('TICKET_NO')
    if is_empty(ticket_no):
        return {'error': 'Ticket number is missing.'}

    user_id = coalesce(args.get('CHG_USER'), args.get('ADD_USER'), 'SYSTEM')
    ts = now()

    # Guarded update: only a ticket still in Resolved status may be reopened.
    db.execute(
        'UPDATE ' + db.t('SUPPORT360_TICKET') +
        ' SET STATUS = :new_status'
        ' WHERE TICKET_NO = :tno AND STATUS = :old_status',
        {'new_status': 'In Progress', 'tno': ticket_no, 'old_status': 'Resolved'})

    current = db.query_one(
        'SELECT STATUS FROM ' + db.t('SUPPORT360_TICKET') + ' WHERE TICKET_NO = :tno',
        {'tno': ticket_no})
    if current is None:
        return {'error': 'Ticket ' + str(ticket_no) + ' no longer exists.'}
    if (current['STATUS'] or '').strip() != 'In Progress':
        return {'error': 'Ticket ' + str(ticket_no) +
                ' is no longer in Resolved status and cannot be reopened.'}

    # Unique 36-char activity-log id (no uuid module is bound in the sandbox).
    log_id = (datetime.datetime.now().strftime('%Y%m%d%H%M%S%f') + '-' +
              str(ticket_no))[:36]

    db.insert(db.t('SUPPORT360_TICKET_ACTLOG'), {
        'ID': log_id,
        'TICKET_NO': ticket_no,
        'ACTION_TYPE': 'Status-Changed',
        'FIELD_CHANGED': 'STATUS',
        'OLD_VALUE': 'Resolved',
        'NEW_VALUE': 'In Progress',
        'CHANGED_BY': user_id,
        'CHANGE_DATE': ts,
        'ADD_DATE': ts,
        'ADD_USER': user_id,
    })

    return {'prompts': [{'code': 'ACREOPEN1', 'type': 'P',
                         'message': 'Ticket ' + str(ticket_no) +
                                    ' reopened and sent back to In Progress.'}]}
