# project: Support360
# object_type: T
# object_name: support360_category_master
# event_type: form_validation
# function_name: check_category_unused_for_delete
# form_no: 1
# language: python
# description: Prevent delete of a category referenced by tickets
# functional_specification: On delete action of a SUPPORT360_CATEGORY_MASTER row, check whether any row exists in the tickets table (SUPPORT360_TICKET or equivalent) with CATEGORY_CODE equal to this record's CATEGORY_CODE. If any such row exists, return an error blocking the delete so the record cannot be removed; the admin must deactivate (IS_ACTIVE='N') the category instead. If no ticket references it, allow the delete to proceed. Only applies when _action indicates a delete; for add/edit actions return no error.
# business_logic: Prevent delete of a category referenced by tickets


def run(args):
    action = (args.get('_action') or '').strip().lower()
    if action not in ('delete', 'del', 'remove'):
        # add / edit -> this rule does not apply
        return None

    code = args.get('CATEGORY_CODE')
    if is_empty(code):
        return None
    code = str(code).strip()

    # The tickets table is not part of this object's own structure; probe the
    # candidate names this deployment may use and stop at the first one that
    # actually resolves with a CATEGORY_CODE column.
    used = 0
    for tbl in ('support360_ticket', 'support360_tickets', 'support360_ticket_master'):
        try:
            cnt = db.scalar(
                'SELECT COUNT(*) FROM ' + db.t(tbl) + ' WHERE CATEGORY_CODE = :c',
                {'c': code})
        except Exception:
            continue
        used = to_number(cnt) or 0
        break

    if used > 0:
        msg = ('Category ' + code + ' is referenced by ' + str(int(used)) +
               ' ticket(s) and cannot be deleted. Deactivate it '
               "(Active = 'N') instead.")
        return {'error': msg,
                'errors': [{'code': 'CATDEL1', 'field': 'category_code',
                            'type': 'E', 'message': msg}]}

    return None
