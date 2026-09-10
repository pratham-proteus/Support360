# project: Support360
# object_type: T
# object_name: support360_category_master
# event_type: form_action
# function_name: deactivate_category
# form_no: 1
# action_name: Deactivate
# language: python
# description: Deactivate a category
# functional_specification: Set IS_ACTIVE to 'N' for the current category record and return a confirmation message. Allowed regardless of whether the category is referenced by tickets, since deactivation (not deletion) is always permitted.
# business_logic: Deactivate a category


def run(args):
    code = args.get('CATEGORY_CODE')
    if is_empty(code):
        return 'Category code is missing; cannot deactivate.'
    code = str(code).strip()

    row = db.query_one(
        'SELECT CATEGORY_CODE, CATEGORY_NAME, IS_ACTIVE FROM ' +
        db.t('support360_category_master') + ' WHERE CATEGORY_CODE = :c',
        {'c': code})
    if not row:
        return 'Category ' + code + ' not found.'

    if (row.get('IS_ACTIVE') or '').strip() == 'N':
        return {'prompts': [{'code': 'CATDCT0', 'field': 'is_active', 'type': 'P',
                             'message': 'Category ' + code + ' is already inactive.'}]}

    # Deactivation is always allowed, even when tickets reference this category.
    db.update(db.t('support360_category_master'),
              {'IS_ACTIVE': 'N', 'CHG_DATE': now()},
              {'CATEGORY_CODE': code})

    return {'updates': {'IS_ACTIVE': 'N'},
            'prompts': [{'code': 'CATDCT1', 'field': 'is_active', 'type': 'P',
                         'message': 'Category ' + code + ' has been deactivated.'}]}
