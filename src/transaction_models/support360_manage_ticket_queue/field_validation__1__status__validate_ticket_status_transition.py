# project: Support360
# object_type: T
# object_name: support360_manage_ticket_queue
# event_type: field_validation
# function_name: validate_ticket_status_transition
# form_no: 1
# field_name: status
# language: python
# description: Allow only Assigned -> In Progress and In Progress -> Resolved on SUPPORT360_TICKET.STATUS
# functional_specification: Reject any STATUS change on SUPPORT360_TICKET other than Assigned -> In Progress and In Progress -> Resolved; in particular an Open ticket may never be set directly to In Progress or Resolved.
# business_logic: Allow only Assigned -> In Progress and In Progress -> Resolved on SUPPORT360_TICKET.STATUS

# Canonical stored spellings, keyed by their normalised (lower-case) form.
CANONICAL_STATUS = {
    'open': 'Open',
    'assigned': 'Assigned',
    'in progress': 'In Progress',
    'resolved': 'Resolved',
    'closed': 'Closed',
}

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

    # The only moves Manage Ticket Queue is allowed to make.
    if (old_status, new_status) in (
        ('Assigned', 'In Progress'),
        ('In Progress', 'Resolved'),
        ('Reopen', 'In Progress'),
    ):
        return None

    # Build a message tailored to what the ticket is currently sitting on.
    if old_status == 'Open':
        msg = (
            "Ticket %s is still Open. Assign it first (Ticket Assignment / Assign action) "
            "before moving it to '%s'." % (ticket_no, new_status)
        )
    elif old_status == 'Assigned':
        msg = (
            'Ticket %s is Assigned and can only be moved to Start Progress (In Progress).'
            % ticket_no
        )
    elif old_status == 'In Progress':
        msg = 'Ticket %s is In Progress and can only be moved to Resolved.' % ticket_no
    elif old_status == 'Reopen':
        msg = (
            'Ticket %s is Reopened and can only be moved back to In Progress.'
            % ticket_no
        )
    elif old_status in ('Resolved', 'Closed'):
        msg = (
            'Ticket %s is already %s and its status can no longer be changed from '
            'Manage Ticket Queue.' % (ticket_no, old_status)
        )
    else:
        msg = (
            "Ticket %s cannot be changed from '%s' to '%s'."
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
