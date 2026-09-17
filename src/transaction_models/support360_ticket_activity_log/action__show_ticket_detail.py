# project: Support360
# object_type: T
# object_name: support360_ticket_activity_log
# event_type: action
# function_name: show_ticket_detail
# action_name: View Ticket
# language: python
# description: Show the parent ticket detail
# functional_specification: Given the activity log row payload (flat, containing TICKET_NO), SELECT TICKET_NO, TITLE, DESCRIPTION, CATEGORY_CODE, PRIORITY_CODE, STATUS, RAISED_BY, ASSIGNED_AGENT, CREATED_DATE, CLOSED_DATE, CLOSED_BY, RESOLUTION_NOTES from SUPPORT360_TICKET where TICKET_NO = the payload TICKET_NO. Render the values as a simple read-only HTML definition list and return {"html": "..."}. If no ticket row is found, return {"error": "Ticket <no> no longer exists."}. Perform no writes.
# business_logic: Show the parent ticket detail


def _esc(v):
    """Render a value as HTML-safe text ('-' when empty)."""
    if is_empty(v):
        return '-'
    s = v if isinstance(v, str) else str(v)
    s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    s = s.replace('"', '&quot;').replace("'", '&#39;')
    return s.replace('\n', '<br/>')


def run(args):
    ticket_no = args.get('TICKET_NO')
    if is_empty(ticket_no):
        return 'Ticket number is missing on this activity log row.'

    if isinstance(ticket_no, str):
        ticket_no = ticket_no.strip()

    row = db.query_one(
        'SELECT TICKET_NO, TITLE, DESCRIPTION, CATEGORY_CODE, PRIORITY_CODE, STATUS, '
        'RAISED_BY, ASSIGNED_AGENT, CREATED_DATE, CLOSED_DATE, CLOSED_BY, RESOLUTION_NOTES '
        'FROM ' + db.t('SUPPORT360_TICKET') + ' WHERE TICKET_NO = :tno',
        {'tno': ticket_no})

    if not row:
        return {'error': 'Ticket ' + str(ticket_no) + ' no longer exists.'}

    def val(col):
        v = row.get(col)
        if v is None:
            v = row.get(col.lower())
        if isinstance(v, str):
            v = v.rstrip()
        return v

    fields = [
        ('Ticket No', 'TICKET_NO'),
        ('Title', 'TITLE'),
        ('Description', 'DESCRIPTION'),
        ('Category', 'CATEGORY_CODE'),
        ('Priority', 'PRIORITY_CODE'),
        ('Status', 'STATUS'),
        ('Raised By', 'RAISED_BY'),
        ('Assigned Agent', 'ASSIGNED_AGENT'),
        ('Created Date', 'CREATED_DATE'),
        ('Closed Date', 'CLOSED_DATE'),
        ('Closed By', 'CLOSED_BY'),
        ('Resolution Notes', 'RESOLUTION_NOTES'),
    ]

    parts = [
        '<div class="ticket-detail">',
        '<h3>Ticket ' + _esc(val('TICKET_NO')) + '</h3>',
        '<dl>',
    ]
    for label, col in fields:
        parts.append('<dt style="font-weight:bold;">' + label + '</dt>')
        parts.append('<dd style="margin:0 0 8px 0;">' + _esc(val(col)) + '</dd>')
    parts.append('</dl></div>')

    return {'html': ''.join(parts)}
