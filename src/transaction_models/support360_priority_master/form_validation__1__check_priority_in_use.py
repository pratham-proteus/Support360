# project: Support360
# object_type: T
# object_name: support360_priority_master
# event_type: form_validation
# function_name: check_priority_in_use
# form_no: 1
# language: python
# description: Prevent deleting a priority referenced by tickets
# functional_specification: On delete action only (_action indicates delete/edit context is not applicable — this rule runs specifically for the delete operation): check whether SUPPORT360_TICKET has any row with PRIORITY_CODE equal to this record's PRIORITY_CODE. If it does, return an error instructing the user that the priority cannot be deleted and should be deactivated instead. If no ticket references it, allow the delete to proceed (return no error).
# business_logic: Prevent deleting a priority referenced by tickets


def run(args):
    priority_code = args.get('PRIORITY_CODE')
    if is_empty(priority_code):
        return None

    used = to_number(db.scalar(
        'SELECT COUNT(*) FROM ' + db.t('SUPPORT360_TICKET') +
        ' WHERE PRIORITY_CODE = :pc',
        {'pc': str(priority_code).strip()}
    ))

    if used and used > 0:
        msg = ('Priority "%s" is referenced by %d ticket(s) and cannot be deleted. '
               'Set Is Active to N to deactivate it instead.'
               % (str(priority_code).strip(), int(used)))
        return {
            'error': msg,
            'errors': [{
                'code': 'PRMDEL1',
                'field': 'PRIORITY_CODE',
                'type': 'E',
                'message': msg,
            }],
        }

    return None
