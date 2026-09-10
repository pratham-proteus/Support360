# project: Support360
# object_type: T
# object_name: support360_priority_master
# event_type: form_validation
# function_name: check_priority_unused_for_delete
# form_no: 1
# language: python
# description: Prevent delete of a priority referenced by tickets
# functional_specification: On delete action of a SUPPORT360_PRIORITY_MASTER row, check whether any row exists in the tickets table (SUPPORT360_TICKET or equivalent) with PRIORITY_CODE equal to this record's PRIORITY_CODE. If any such row exists, return an error blocking the delete so the record cannot be removed; the admin must deactivate (IS_ACTIVE='N') the priority instead. If no ticket references it, allow the delete to proceed. Only applies when _action indicates a delete; for add/edit actions return no error.
# business_logic: Prevent delete of a priority referenced by tickets

# The ticket object is not part of this model's authoritative structure, so the
# actual table name is resolved from the catalog at runtime; only a table that
# really exists AND really carries PRIORITY_CODE is queried.
_TICKET_TABLES = ('SUPPORT360_TICKET', 'SUPPORT360_TICKET_MASTER', 'SUPPORT360_TICKETS')


def _resolve_ticket_table():
    for tbl in _TICKET_TABLES:
        found = db.scalar(
            'SELECT COUNT(*) FROM information_schema.columns '
            'WHERE upper(table_name) = :t AND upper(column_name) = :c',
            {'t': tbl.upper(), 'c': 'PRIORITY_CODE'})
        if to_number(found) > 0:
            return tbl
    return None


def run(args):
    # Only guard the delete action; add / edit pass straight through.
    if str(coalesce(args.get('_action'), '')).strip().lower() != 'delete':
        return None

    code = args.get('PRIORITY_CODE')
    if is_empty(code):
        return None

    tbl = _resolve_ticket_table()
    if not tbl:
        # No ticket table deployed - nothing can reference this priority.
        return None

    used = db.scalar(
        'SELECT COUNT(*) FROM ' + db.t(tbl) + ' WHERE PRIORITY_CODE = :c',
        {'c': code})

    if to_number(used) > 0:
        msg = ('Priority ' + str(code) + ' is referenced by '
               + str(int(to_number(used))) + ' ticket(s) and cannot be deleted. '
               'Deactivate it (Is Active = N) instead.')
        # Hard, non-overridable referential rule.
        return {'error': msg,
                'errors': [{'code': 'PRIDEL_INUSE',
                            'field': 'PRIORITY_CODE',
                            'type': 'E',
                            'message': msg}]}

    return None
