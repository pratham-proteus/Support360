# project: Support360
# object_type: T
# object_name: support360_my_tickets
# event_type: form_action
# function_name: add_reopen_comment
# form_no: 1
# action_name: Reopen Comment
# language: python
# description: Employee posts a comment on the ticket without changing its status
# functional_specification: On the current SUPPORT360_TICKET row, append the text in NEW_COMMENT to AGENT_COMMENTS (prefixed with the current logged-in user and the current timestamp, on a new line), then clear NEW_COMMENT. Do not change STATUS. Append one entry to the ticket's Activity/History Log (table to be confirmed once the Ticket Activity Log object is designed) with TICKET_NO = this ticket, ACTION_TYPE = 'Commented', CHANGED_BY = current user, CHANGE_DATE = now. Return a confirmation message such as 'Comment added to ticket {TICKET_NO}.' If NEW_COMMENT is blank, return an error asking the user to enter a comment first.
# business_logic: Employee posts a comment on the ticket without changing its status


def _current_user(args):
    return coalesce(args.get('CHG_USER'), args.get('ADD_USER'), args.get('RAISED_BY'), '')


def run(args):
    ticket_no = args.get('TICKET_NO')
    if is_empty(ticket_no):
        return 'No ticket selected.'

    comment = args.get('NEW_COMMENT')
    comment = '' if comment is None else str(comment).strip()
    if not comment:
        return 'Please enter a comment first.'

    row = db.query_one(
        'SELECT TICKET_NO, AGENT_COMMENTS, ACTIVITY_HISTORY FROM ' + db.t('SUPPORT360_TICKET') +
        ' WHERE TICKET_NO = :t', {'t': ticket_no})
    if not row:
        return 'Ticket %s not found.' % ticket_no

    user = _current_user(args)
    stamp = now().strftime('%Y-%m-%d %H:%M:%S')

    existing = coalesce(row.get('AGENT_COMMENTS'), row.get('agent_comments'))
    line = '[%s %s] %s' % (stamp, user, comment)
    comments = line if is_empty(existing) else str(existing).rstrip() + '\n' + line

    entry = '%s | Commented | %s' % (stamp, user)
    history = coalesce(row.get('ACTIVITY_HISTORY'), row.get('activity_history'))
    history = entry if is_empty(history) else str(history).rstrip() + '\n' + entry

    # STATUS is deliberately left untouched.
    db.update('SUPPORT360_TICKET', {
        'AGENT_COMMENTS': comments,
        'NEW_COMMENT': None,
        'ACTIVITY_HISTORY': history,
        'CHG_DATE': stamp,
        'CHG_USER': user,
    }, {'TICKET_NO': ticket_no})

    return {'prompts': [{'code': 'ACMNT1', 'field': 'new_comment',
                         'message': 'Comment added to ticket %s.' % ticket_no}]}
