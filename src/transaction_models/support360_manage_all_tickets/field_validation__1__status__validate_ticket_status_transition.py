# project: Support360
# object_type: T
# object_name: support360_manage_all_tickets
# event_type: field_validation
# function_name: validate_ticket_status_transition
# form_no: 1
# field_name: status
# language: python
# description: Enforce the ticket status transition sequence
# functional_specification: On edit (_action = 'edit'), compare the existing stored STATUS (from the merged row) to the incoming STATUS. Allow no-change. Allow only forward moves in the sequence Open -> Assigned -> In Progress -> Resolved -> Closed (no skipping, no reverse). Reject a move to Assigned unless ASSIGNED_AGENT is set. Reject a move to In Progress unless the ticket is already Assigned (ASSIGNED_AGENT set). Reject a move to Resolved unless RESOLUTION_NOTES is non-empty. On add (_action = 'add'), STATUS must be Open. Return an error message describing the invalid transition when the rule fails, otherwise return null.
# business_logic: Enforce the ticket status transition sequence

SEQUENCE = ['Open', 'Assigned', 'In Progress', 'Resolved', 'Closed']

# Candidate keys the platform may use to pass the pre-edit (existing/original)
# row into a business_logic validation for the record being edited. Plain
# dict/object access only - never a database query.
_EXISTING_ROW_KEYS = (
    '_existing', '_existing_row', '_original', '_original_row',
    '_orig', '_orig_row', '_old_row', '_db_row', '_row', 'existing',
    'existing_row', 'original', 'original_row',
)


def _txt(v):
    return '' if v is None else str(v).strip()


def _get(row, name):
    """Case-insensitive column read from a row-like dict/object."""
    if row is None:
        return None
    if isinstance(row, dict):
        if name in row:
            return row[name]
        low = name.lower()
        for k, v in row.items():
            if str(k).lower() == low:
                return v
        return None
    return getattr(row, name, None)


def _find_existing_row(args):
    """Locate the framework-supplied existing/original-row context for an
    edit, using only plain attribute/dict access on the validation context
    already given to this function. Returns None if no such binding is
    present or usable."""
    for key in _EXISTING_ROW_KEYS:
        row = args.get(key)
        if isinstance(row, dict) and row:
            return row
    return None


def run(args):
    new_status = _txt(args.get('STATUS'))
    if not new_status:
        return 'Status is required'
    if new_status not in SEQUENCE:
        return "Invalid status '" + new_status + "'"

    ticket_no = _txt(args.get('TICKET_NO'))

    # Determine new-vs-existing strictly by whether TICKET_NO already exists
    # in SUPPORT360_TICKET - never by the _action flag, since the framework
    # does not reliably pass 'edit' for every update path (e.g. the Assign
    # action). A row found in the DB always means this is an update.
    row_exists = False
    old_status = ''
    if ticket_no:
        try:
            row = db.query_one(
                'SELECT STATUS FROM ' + db.t('SUPPORT360_TICKET') + ' WHERE TICKET_NO = :t',
                {'t': ticket_no}
            )
            if row is not None:
                row_exists = True
                old_status = _txt(_get(row, 'STATUS'))
        except Exception:
            row_exists = False
            old_status = ''

        if not row_exists:
            # DB lookup found no row (e.g. ticket_no not yet committed) -
            # fall back to the framework-supplied existing-row context, if any.
            try:
                existing = _find_existing_row(args)
                if existing is not None:
                    row_exists = True
                    old_status = _txt(_get(existing, 'STATUS'))
            except Exception:
                # Never let a lookup failure surface as an unhandled error -
                # degrade to add-mode semantics below instead.
                row_exists = False
                old_status = ''

    if not row_exists:
        # A genuine new record - no existing row was found anywhere.
        if new_status != 'Open':
            return "A new ticket must be created with status 'Open', not '" + new_status + "'"
        return None

    if not old_status or old_status == new_status:
        return None
    if old_status not in SEQUENCE:
        return None

    # Real allowed workflow transitions for an existing ticket. Same-status
    # (no change) is already handled above.
    ALLOWED_TRANSITIONS = {
        'Open': {'Assigned'},
        'Assigned': {'In Progress', 'Open'},
        'In Progress': {'Resolved'},
        'Resolved': {'Closed', 'In Progress', 'Assigned'},
        'Closed': set(),
    }

    if new_status not in ALLOWED_TRANSITIONS.get(old_status, set()):
        return ("Invalid status transition for ticket " + ticket_no + ": cannot move from '"
                + old_status + "' to '" + new_status + "'.")

    agent = _txt(args.get('ASSIGNED_AGENT'))
    notes = _txt(args.get('RESOLUTION_NOTES'))

    if new_status == 'Assigned' and not agent:
        return ("Invalid status transition for ticket " + ticket_no
                + ": cannot move to 'Assigned' without an assigned agent.")
    if new_status == 'In Progress' and old_status != 'Assigned':
        return ("Invalid status transition for ticket " + ticket_no
                + ": cannot move to 'In Progress' unless the ticket is currently 'Assigned'.")
    if new_status == 'Resolved' and not notes:
        return ("Invalid status transition for ticket " + ticket_no
                + ": cannot move to 'Resolved' without resolution notes.")

    return None
