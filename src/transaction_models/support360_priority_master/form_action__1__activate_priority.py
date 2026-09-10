# project: Support360
# object_type: T
# object_name: support360_priority_master
# event_type: form_action
# function_name: activate_priority
# form_no: 1
# action_name: Activate
# language: python
# description: Activate a priority
# functional_specification: Set IS_ACTIVE to 'Y' for the current priority record and return a confirmation message.
# business_logic: Activate a priority


def run(args):
    code = args.get('PRIORITY_CODE')
    if is_empty(code):
        return {'error': 'Priority code is missing - cannot activate.'}

    row = db.query_one(
        'SELECT PRIORITY_CODE, PRIORITY_NAME, IS_ACTIVE FROM '
        + db.t('SUPPORT360_PRIORITY_MASTER') + ' WHERE PRIORITY_CODE = :c',
        {'c': code})
    if not row:
        return {'error': 'Priority ' + str(code) + ' not found.'}

    name = coalesce(row.get('PRIORITY_NAME'), code)

    if str(coalesce(row.get('IS_ACTIVE'), '')).strip() == 'Y':
        return {'prompts': [{'code': 'PRIACT_ALREADY',
                             'field': 'IS_ACTIVE',
                             'message': 'Priority ' + str(name) + ' is already active.'}]}

    db.update(db.t('SUPPORT360_PRIORITY_MASTER'),
              {'IS_ACTIVE': 'Y'},
              {'PRIORITY_CODE': code})

    return {'updates': {'IS_ACTIVE': 'Y'},
            'prompts': [{'code': 'PRIACT_OK',
                         'field': 'IS_ACTIVE',
                         'message': 'Priority ' + str(name) + ' has been activated.'}]}
