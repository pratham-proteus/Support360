# Form action: Reopen Resolved Ticket
# Sets a Closed ticket back to 'Reopen', clears the closure details and
# records the change in the ticket activity log.


def run(args):
    ticket_no = args.get('TICKET_NO')
    if is_empty(ticket_no):
        return 'Ticket number is required.'

    t = db.t('SUPPORT360_TICKET')
    row = db.query_one(
        'SELECT STATUS FROM ' + t + ' WHERE TICKET_NO = :n', {'n': ticket_no})
    if not row:
        return 'Ticket ' + str(ticket_no) + ' not found.'
    old_status = row['STATUS']
    if old_status != 'Closed':
        return 'Only a Closed ticket can be reopened.'

    stamp = now()
    db.update(
        'SUPPORT360_TICKET',
        {'STATUS': 'Reopen', 'CLOSED_DATE': None, 'CLOSED_BY': None,
         'CHG_DATE': stamp},
        {'TICKET_NO': ticket_no})

    return {'updates': {'STATUS': 'Reopen', 'CLOSED_DATE': None,
                        'CLOSED_BY': None, 'CHG_DATE': str(stamp)}}
