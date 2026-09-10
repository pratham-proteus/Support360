# project: Support360
# object_type: T
# object_name: support360_create_ticket
# event_type: followup_action
# function_name: log_ticket_created
# action_name: log_ticket_created
# condition: on-add
# language: python
# description: Write a Created entry to the ticket Activity/History Log
# functional_specification: After a new SUPPORT360_TICKET row is added, insert one entry into the ticket's Activity/History Log (the Ticket Activity Log object's underlying table — table name to be confirmed once that object is designed) with TICKET_NO = the new ticket's ticket number, ACTION_TYPE = 'Created', FIELD_CHANGED = null, OLD_VALUE = null, NEW_VALUE = null, CHANGED_BY = the current logged-in user, and CHANGE_DATE = the current timestamp. This is a notification/audit write only and must never block or roll back the ticket save.
# business_logic: Write a Created entry to the ticket Activity/History Log

# The Ticket Activity Log object has not been designed yet, so its physical table
# is not part of the authoritative table structures. The insert is therefore made
# defensively: any failure (table not deployed yet, column mismatch) is swallowed
# so this audit-only write can never block or roll back the ticket save.
ACTIVITY_LOG_TABLE = 'SUPPORT360_TICKET_ACTIVITY_LOG'


def run(args):
    try:
        ticket_no = args.get('TICKET_NO')
        if is_empty(ticket_no):
            return None

        # Guard: log only on creation of a new ticket.
        act = str(coalesce(args.get('action'), args.get('_action'), 'add')).lower()
        if act not in ('add', 'insert'):
            return None

        # Current logged-in user as stamped by the engine on the saved row.
        changed_by = coalesce(args.get('ADD_USER'), args.get('CHG_USER'), args.get('RAISED_BY'))

        db.insert(ACTIVITY_LOG_TABLE, {
            'TICKET_NO': ticket_no,
            'ACTION_TYPE': 'Created',
            'FIELD_CHANGED': None,
            'OLD_VALUE': None,
            'NEW_VALUE': None,
            'CHANGED_BY': changed_by,
            'CHANGE_DATE': now(),
        })
    except Exception:
        # Notification/audit write only — never block or roll back the save.
        pass

    return None
