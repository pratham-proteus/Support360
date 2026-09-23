# project: Support360
# object_type: T
# object_name: support360_resolved_tickets
# event_type: form_action
# function_name: close_resolved_ticket
# form_no: 1
# action_name: Close Ticket
# language: python
# description: Close a Resolved ticket
# functional_specification: Given the current ticket's TICKET_NO, UPDATE SUPPORT360_TICKET SET STATUS = 'Closed', CLOSED_DATE = current timestamp, CLOSED_BY = the id of the currently logged-in user WHERE TICKET_NO = the current ticket's TICKET_NO AND STATUS = 'Resolved'. If no row was updated (status is no longer Resolved), return an error. Insert an entry into SUPPORT360_TICKET_ACTLOG with a new ID, TICKET_NO = the ticket's TICKET_NO, ACTION_TYPE = 'Closed', FIELD_CHANGED = 'STATUS', OLD_VALUE = 'Resolved', NEW_VALUE = 'Closed', CHANGED_BY = the current user id, CHANGE_DATE = current timestamp. Return a confirmation message such as 'Ticket <TICKET_NO> closed successfully.'
# business_logic: Close a Resolved ticket


def run(args):
    ticket_no = args.get('TICKET_NO')
    if is_empty(ticket_no):
        return {'error': 'Ticket number is missing.'}

    user_id = coalesce(args.get('CHG_USER'), args.get('ADD_USER'), 'SYSTEM')
    ts = now()

    # Guarded update: only a ticket still in Resolved status may be closed.
    db.execute(
        'UPDATE ' + db.t('SUPPORT360_TICKET') +
        ' SET STATUS = :new_status, CLOSED_DATE = :closed_date, CLOSED_BY = :closed_by'
        ' WHERE TICKET_NO = :tno AND STATUS = :old_status',
        {'new_status': 'Closed', 'closed_date': ts, 'closed_by': user_id,
         'tno': ticket_no, 'old_status': 'Resolved'})

    current = db.query_one(
        'SELECT STATUS FROM ' + db.t('SUPPORT360_TICKET') + ' WHERE TICKET_NO = :tno',
        {'tno': ticket_no})
    if current is None:
        return {'error': 'Ticket ' + str(ticket_no) + ' no longer exists.'}
    if (current['STATUS'] or '').strip() != 'Closed':
        return {'error': 'Ticket ' + str(ticket_no) +
                ' is no longer in Resolved status and cannot be closed.'}

    # Unique 36-char activity-log id (no uuid module is bound in the sandbox).
    log_id = (datetime.datetime.now().strftime('%Y%m%d%H%M%S%f') + '-' +
              str(ticket_no))[:36]

    db.insert(db.t('SUPPORT360_TICKET_ACTLOG'), {
        'ID': log_id,
        'TICKET_NO': ticket_no,
        'ACTION_TYPE': 'Closed',
        'FIELD_CHANGED': 'STATUS',
        'OLD_VALUE': 'Resolved',
        'NEW_VALUE': 'Closed',
        'CHANGED_BY': user_id,
        'CHANGE_DATE': ts,
        'ADD_DATE': ts,
        'ADD_USER': user_id,
    })

    return {'prompts': [{'code': 'ACCLOSE1', 'type': 'P',
                         'message': 'Ticket ' + str(ticket_no) + ' closed successfully.'}]}
