# project: Support360
# object_type: T
# object_name: support360_manage_ticket_queue
# event_type: field_validation
# function_name: validate_ticket_status_transition
# form_no: 1
# field_name: status
# language: python
# description: Allow only forward moves along Pending -> Assigned -> Queued -> Resolved on SUPPORT360_TICKET.STATUS
# functional_specification: Only Pending, Assigned, Queued and Resolved are valid STATUS values. STATUS may only move forward along Pending -> Assigned -> Queued -> Resolved (skipping ahead is allowed, e.g. Assigned -> Resolved), never backward. Resolved is final and can never be changed once set.
# business_logic: Allow only forward moves along Pending -> Assigned -> Queued -> Resolved on SUPPORT360_TICKET.STATUS; reject any value outside this set and any backward move; Resolved is final.

# Canonical stored spellings, keyed by their normalised (lower-case) form.
CANONICAL_STATUS = {
    'pending': 'Pending',
    'assigned': 'Assigned',
    'queued': 'Queued',
    'resolved': 'Resolved',
    'not resolved': 'Not Resolved',
}

# Forward order of the lifecycle - index determines allowed direction of travel.
STATUS_ORDER = ['Pending', 'Assigned', 'Queued', 'Resolved']

# 'Not Resolved' sits outside the linear forward order above - it may only be
# reached from these statuses (never directly from Pending).
NOT_RESOLVED = 'Not Resolved'
NOT_RESOLVED_ALLOWED_SOURCES = ('Assigned', 'Queued')

ERROR_CODE = 'TQ_STATUS_TRANSITION'


def _canonical(value):
    """Trim the value and map it back to its stored spelling (case-insensitive)."""
    if value is None:
        return ''
    text = str(value).strip()
    return CANONICAL_STATUS.get(text.lower(), text)


def run(args):
    new_status = _canonical(args.get('status'))
    if is_empty(new_status):
        # Nothing picked yet - nothing to validate.
        return None

    ticket_no = args.get('ticket_no')
    if is_empty(ticket_no):
        # Brand new ticket being entered - there is no stored status to move from.
        return None

    ticket_no = str(ticket_no).strip()
    row = db.query_one(
        'SELECT STATUS FROM ' + db.t('SUPPORT360_TICKET') + ' WHERE TICKET_NO = :t',
        {'t': ticket_no},
    )
    if not row:
        # Nothing persisted yet for this ticket number - not this function's concern.
        return None

    old_status = _canonical(row['STATUS'])

    # No change at all is always fine.
    if old_status.lower() == new_status.lower():
        return None

    if old_status == 'Pending' and new_status in ('Resolved', NOT_RESOLVED):
        msg = (
            'This ticket must be assigned to an agent before it can be marked Resolved '
            'or Not Resolved. Please assign the ticket first.'
        )
        return {
            'error': msg,
            'errors': [{
                'code': ERROR_CODE,
                'field': 'status',
                'type': 'E',
                'message': msg,
            }],
        }

    if new_status not in STATUS_ORDER and new_status != NOT_RESOLVED:
        msg = (
            "'%s' is not a valid status for ticket %s. Allowed statuses are: %s."
            % (new_status, ticket_no, ', '.join(STATUS_ORDER + [NOT_RESOLVED]))
        )
        return {
            'error': msg,
            'errors': [{
                'code': ERROR_CODE,
                'field': 'status',
                'type': 'E',
                'message': msg,
            }],
        }

    if old_status not in STATUS_ORDER:
        msg = (
            "Ticket %s has an unrecognised status '%s' and cannot be moved to '%s'."
            % (ticket_no, old_status, new_status)
        )
        return {
            'error': msg,
            'errors': [{
                'code': ERROR_CODE,
                'field': 'status',
                'type': 'E',
                'message': msg,
            }],
        }

    if old_status == 'Resolved':
        msg = (
            'Ticket %s is already Resolved and its status can no longer be changed.'
            % ticket_no
        )
        return {
            'error': msg,
            'errors': [{
                'code': ERROR_CODE,
                'field': 'status',
                'type': 'E',
                'message': msg,
            }],
        }

    if new_status == NOT_RESOLVED:
        if old_status in NOT_RESOLVED_ALLOWED_SOURCES:
            return None
        msg = (
            "Ticket %s cannot move from '%s' to 'Not Resolved'. 'Not Resolved' may only "
            "be set from %s." % (ticket_no, old_status, ' or '.join(NOT_RESOLVED_ALLOWED_SOURCES))
        )
        return {
            'error': msg,
            'errors': [{
                'code': ERROR_CODE,
                'field': 'status',
                'type': 'E',
                'message': msg,
            }],
        }

    old_index = STATUS_ORDER.index(old_status)
    new_index = STATUS_ORDER.index(new_status)

    if new_index > old_index:
        return None

    msg = (
        "Ticket %s cannot move backward from '%s' to '%s'. Status may only advance "
        "along %s." % (ticket_no, old_status, new_status, ' -> '.join(STATUS_ORDER))
    )

    return {
        'error': msg,
        'errors': [{
            'code': ERROR_CODE,
            'field': 'status',
            'type': 'E',
            'message': msg,
        }],
    }
