# project: Support360
# object_type: T
# object_name: support360_manage_ticket_queue
# event_type: form_action
# function_name: add_agent_comment
# form_no: 1
# action_name: Add Comment
# language: python
# description: Agent posts a comment on the ticket for the Employee to see
# functional_specification: On the current SUPPORT360_TICKET row, append the text in NEW_COMMENT to AGENT_COMMENTS (prefixed with the current logged-in user and the current timestamp, on a new line), then clear NEW_COMMENT. Do not change STATUS. Append one entry to the ticket's Activity/History Log (table to be confirmed once the Ticket Activity Log object is designed) with TICKET_NO = this ticket, ACTION_TYPE = 'Commented', CHANGED_BY = current user, CHANGE_DATE = now. Return {"updates": {"agent_comments": <updated thread>, "new_comment": ""}}.
# business_logic: Agent posts a comment on the ticket for the Employee to see


def run(args):
    # This is a form_action event: the payload carries current form values
    # under their lowercase form-field names (see form_action__1__resolve_ticket.py),
    # not the uppercase DB column names.
    ticket_no = args.get('ticket_no')
    comment = args.get('new_comment')
    current_user = args.get('_current_user') or args.get('current_user')

    if is_empty(ticket_no):
        return 'Ticket not identified. Please open a saved ticket before adding a comment.'
    if is_empty(comment) or is_empty(str(comment).strip()):
        return 'Comment cannot be empty'

    comment_text = str(comment).strip()
    stamp = datetime.datetime.now()

    row = db.query_one(
        'SELECT AGENT_COMMENTS FROM SUPPORT360_TICKET WHERE TICKET_NO = :t',
        {'t': ticket_no})
    if not row:
        return 'Ticket %s not found.' % ticket_no

    prior = coalesce(row.get('AGENT_COMMENTS'), '')
    entry = '[%s, %s]: %s\n' % (current_user, stamp.strftime('%Y-%m-%d %H:%M:%S'), comment_text)
    thread = prior + entry

    # STATUS is deliberately left untouched.
    db.update('SUPPORT360_TICKET', {
        'AGENT_COMMENTS': thread,
        'NEW_COMMENT': '',
    }, {'TICKET_NO': ticket_no})

    # Insert activity log entry
    db.insert('SUPPORT360_TICKET_ACTLOG', {
        'TICKET_NO': ticket_no,
        'ACTION_TYPE': 'Commented',
        'FIELD_CHANGED': 'AGENT_COMMENTS',
        'OLD_VALUE': '',
        'NEW_VALUE': comment_text,
        'CHANGED_BY': current_user,
        'CHANGE_DATE': stamp,
    })

    return {'updates': {'agent_comments': thread, 'new_comment': ''}}
