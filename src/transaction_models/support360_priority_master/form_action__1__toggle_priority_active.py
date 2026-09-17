# project: Support360
# object_type: T
# object_name: support360_priority_master
# event_type: form_action
# function_name: toggle_priority_active
# form_no: 1
# action_name: Activate / Deactivate
# language: python
# description: Toggle the active flag of the priority
# functional_specification: Payload is the flat priority row. If IS_ACTIVE is 'Y', the priority is being DEACTIVATED: set IS_ACTIVE = 'N' on SUPPORT360_PRIORITY_MASTER for this PRIORITY_CODE (deactivation is always permitted, even when tickets reference it). If IS_ACTIVE is 'N', set it back to 'Y'. Return {"updates": {"IS_ACTIVE": "<new value>"}} so the form reflects the new state. Return {"error": "..."} if the PRIORITY_CODE does not exist.
# business_logic: Toggle the active flag of the priority


def run(args):
    code = args.get('PRIORITY_CODE')
    if is_empty(code):
        return {'error': 'Priority Code is required'}
    code = str(code).strip()

    row = db.query_one(
        'SELECT PRIORITY_CODE, IS_ACTIVE FROM ' + db.t('SUPPORT360_PRIORITY_MASTER') +
        ' WHERE PRIORITY_CODE = :c', {'c': code})
    if not row:
        return {'error': 'Priority Code ' + code + ' does not exist'}

    current = coalesce(row.get('IS_ACTIVE'), row.get('is_active'), 'N')
    current = str(current).strip().upper()

    # 'Y' -> deactivate (always permitted, even when tickets reference it); 'N' -> reactivate
    new_value = 'N' if current == 'Y' else 'Y'

    db.update(db.t('SUPPORT360_PRIORITY_MASTER'),
              {'IS_ACTIVE': new_value},
              {'PRIORITY_CODE': code})

    return {'updates': {'IS_ACTIVE': new_value}}
