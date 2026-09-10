# project: Support360
# object_type: T
# object_name: support360_my_tickets
# event_type: form_action
# function_name: confirm_close_ticket
# form_no: 1
# action_name: Confirm and Close
# language: python
# description: Employee confirms resolution and closes the ticket
# functional_specification: On the current SUPPORT360_TICKET row, set STATUS to 'Closed', CLOSED_DATE to the current timestamp, and CLOSED_BY to the current logged-in user. Append one entry to the ticket's Activity/History Log (table to be confirmed once the Ticket Activity Log object is designed) with TICKET_NO = this ticket, ACTION_TYPE = 'Closed', FIELD_CHANGED = 'STATUS', OLD_VALUE = 'Resolved', NEW_VALUE = 'Closed', CHANGED_BY = current user, CHANGE_DATE = now. Return a confirmation message such as 'Ticket {TICKET_NO} closed.'
# business_logic: Employee confirms resolution and closes the ticket


def _current_user(args):
    return coalesce(args.get('CHG_USER'), args.get('ADD_USER'), args.get('RAISED_BY'), '')


def run(args):
    ticket_no = args.get('TICKET_NO')
    if is_empty(ticket_no):
        return 'No ticket selected.'

    row = db.query_one(
        'SELECT TICKET_NO, STATUS, ACTIVITY_HISTORY FROM ' + db.t('SUPPORT360_TICKET') +
        ' WHERE TICKET_NO = :t', {'t': ticket_no})
    if not row:
        return 'Ticket %s not found.' % ticket_no

    old_status = str(coalesce(row.get('STATUS'), row.get('status'), '')).strip()
    if old_status == 'Closed':
        return 'Ticket %s is already closed.' % ticket_no

    user = _current_user(args)
    stamp = now().strftime('%Y-%m-%d %H:%M:%S')

    # Activity / History log entry (kept on ACTIVITY_HISTORY until the dedicated
    # Ticket Activity Log object exists).
    entry = '%s | Closed | STATUS | %s -> Closed | %s' % (
        stamp, coalesce(old_status, 'Resolved'), user)
    history = coalesce(row.get('ACTIVITY_HISTORY'), row.get('activity_history'))
    history = entry if is_empty(history) else str(history).rstrip() + '\n' + entry

    db.update('SUPPORT360_TICKET', {
        'STATUS': 'Closed',
        'CLOSED_DATE': stamp,
        'CLOSED_BY': user,
        'ACTIVITY_HISTORY': history,
        'CHG_DATE': stamp,
        'CHG_USER': user,
    }, {'TICKET_NO': ticket_no})

    return {'prompts': [{'code': 'ACLOSE1', 'field': 'status',
                         'message': 'Ticket %s closed.' % ticket_no}]}
