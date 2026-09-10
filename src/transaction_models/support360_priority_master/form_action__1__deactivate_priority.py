# project: Support360
# object_type: T
# object_name: support360_priority_master
# event_type: form_action
# function_name: deactivate_priority
# form_no: 1
# action_name: Deactivate
# language: python
# description: Deactivate a priority
# functional_specification: Set IS_ACTIVE to 'N' for the current priority record and return a confirmation message. Allowed regardless of whether the priority is referenced by tickets, since deactivation (not deletion) is always permitted.
# business_logic: Deactivate a priority


def run(args):
    code = args.get('PRIORITY_CODE')
    if is_empty(code):
        return {'error': 'Priority code is missing - cannot deactivate.'}

    row = db.query_one(
        'SELECT PRIORITY_CODE, PRIORITY_NAME, IS_ACTIVE FROM '
        + db.t('SUPPORT360_PRIORITY_MASTER') + ' WHERE PRIORITY_CODE = :c',
        {'c': code})
    if not row:
        return {'error': 'Priority ' + str(code) + ' not found.'}

    name = coalesce(row.get('PRIORITY_NAME'), code)

    # Already inactive - nothing to do, just inform the user (never blocking).
    if str(coalesce(row.get('IS_ACTIVE'), '')).strip() == 'N':
        return {'prompts': [{'code': 'PRIDEACT_ALREADY',
                             'field': 'IS_ACTIVE',
                             'message': 'Priority ' + str(name) + ' is already inactive.'}]}

    # Deactivation is always permitted, even when tickets reference this priority.
    db.update(db.t('SUPPORT360_PRIORITY_MASTER'),
              {'IS_ACTIVE': 'N'},
              {'PRIORITY_CODE': code})

    return {'updates': {'IS_ACTIVE': 'N'},
            'prompts': [{'code': 'PRIDEACT_OK',
                         'field': 'IS_ACTIVE',
                         'message': 'Priority ' + str(name) + ' has been deactivated.'}]}
