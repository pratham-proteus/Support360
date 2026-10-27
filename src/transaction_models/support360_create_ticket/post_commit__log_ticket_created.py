# project: Support360
# object_type: T
# object_name: support360_create_ticket
# event_type: post_commit
# function_name: log_ticket_created
# language: python
# description: Write a Created entry to the ticket Activity/History Log
# functional_specification: After a new SUPPORT360_TICKET row is committed (action = add), insert one entry into SUPPORT360_TICKET_ACTLOG with TICKET_NO = the new ticket's number, ACTION_TYPE = 'Created', FIELD_CHANGED / OLD_VALUE / NEW_VALUE = null, CHANGED_BY = the user who saved it, and CHANGE_DATE = now. Audit-only: runs after the save has committed and must never block it.
# business_logic: Write a Created entry to the ticket Activity/History Log

ACTIVITY_LOG_TABLE = 'SUPPORT360_TICKET_ACTLOG'


def _get(row, name):
    return coalesce(row.get(name.upper()), row.get(name.lower()))


def run(args):
    try:
        if str(args.get('action') or '').lower() != 'add':
            return None
        header = args.get('header') or {}
        ticket_no = _get(header, 'TICKET_NO')
        if is_empty(ticket_no):
            return None
        ticket_no = str(ticket_no).strip()
        changed_by = coalesce(_get(header, 'ADD_USER'), _get(header, 'RAISED_BY'), 'System')

        db.insert(ACTIVITY_LOG_TABLE, {
            # ID is the log's key (auto_generate() on its own screen, which a
            # direct insert does not run): unique by the clock first.
            'ID': ('C' + now().strftime('%Y%m%d%H%M%S%f') + ticket_no)[:36],
            'TICKET_NO': ticket_no,
            'ACTION_TYPE': 'Created',
            'FIELD_CHANGED': None,
            'OLD_VALUE': None,
            'NEW_VALUE': None,
            'CHANGED_BY': changed_by,
            'CHANGE_DATE': now(),
        })
    except Exception as exc:
        # Audit write only — never report a failure as a save problem.
        log('log_ticket_created failed: ' + str(exc))
    return None
