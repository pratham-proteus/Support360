# project: Support360
# object_type: T
# object_name: support360_category_master
# event_type: form_action
# function_name: activate_category
# form_no: 1
# action_name: Activate
# language: python
# description: Activate a category
# functional_specification: Set IS_ACTIVE to 'Y' for the current category record and return a confirmation message.
# business_logic: Activate a category


def run(args):
    code = args.get('CATEGORY_CODE')
    if is_empty(code):
        return 'Category code is missing; cannot activate.'
    code = str(code).strip()

    row = db.query_one(
        'SELECT CATEGORY_CODE, CATEGORY_NAME, IS_ACTIVE FROM ' +
        db.t('support360_category_master') + ' WHERE CATEGORY_CODE = :c',
        {'c': code})
    if not row:
        return 'Category ' + code + ' not found.'

    if (row.get('IS_ACTIVE') or '').strip() == 'Y':
        return {'prompts': [{'code': 'CATACT0', 'field': 'is_active', 'type': 'P',
                             'message': 'Category ' + code + ' is already active.'}]}

    db.update(db.t('support360_category_master'),
              {'IS_ACTIVE': 'Y', 'CHG_DATE': now()},
              {'CATEGORY_CODE': code})

    return {'updates': {'IS_ACTIVE': 'Y'},
            'prompts': [{'code': 'CATACT1', 'field': 'is_active', 'type': 'P',
                         'message': 'Category ' + code + ' has been activated.'}]}
