# project: Support360
# object_type: T
# object_name: support360_create_ticket
# event_type: followup_action
# function_name: auto_assign_agent
# action_name: auto_assign_agent
# condition: on-add
# language: python
# description: Auto-assign the ticket to a matching active agent based on category preference
# functional_specification: After a new SUPPORT360_TICKET row is added, select from SUPPORT360_AGENT the agents whose PREFERENCE equals the new ticket's CATEGORY_NAME (case/space insensitive) and AGENT_STATUS = 'Active'. Among matches, prefer one with AGENT_AVAILABILITY = 'Available'; otherwise take the lowest AGENT_ID. If no Active agent matches the category, leave ASSIGNED_AGENT empty and STATUS = 'Pending'. If the chosen agent is Occupied, also leave the ticket Pending. Otherwise, assign the agent (ASSIGNED_AGENT, STATUS = 'Assigned'), persist the update, and record an entry in SUPPORT360_TICKET_ACTLOG. This is a notification/auto-assignment write only and must never block or roll back the ticket save; any failure in this step must be caught and ignored so the ticket save still commits.
# business_logic: Auto-assign the ticket to a matching available agent and log the assignment


def run(args):
    # Never block or roll back the ticket save: swallow every failure.
    try:
        ticket_no = args.get('TICKET_NO')
        category_code = args.get('CATEGORY_CODE')
        if is_empty(ticket_no) or is_empty(category_code):
            return None

        ticket_no_val = str(ticket_no).strip()
        category_code_val = str(category_code).strip()

        category_row = db.query_one(
            'SELECT CATEGORY_NAME FROM ' + db.t('SUPPORT360_CATEGORY_MASTER') +
            ' WHERE CATEGORY_CODE = :category_code',
            {'category_code': category_code_val})
        if is_empty(category_row) or is_empty(category_row.get('CATEGORY_NAME')):
            # Unknown category: leave ticket Pending / unassigned.
            return None

        normalized_category = str(category_row.get('CATEGORY_NAME')).strip().upper()

        rows = db.query(
            'SELECT AGENT_ID, AGENT_AVAILABILITY FROM ' + db.t('SUPPORT360_AGENT') +
            ' WHERE UPPER(TRIM(PREFERENCE)) = :pref'
            ' AND AGENT_STATUS = :status'
            ' ORDER BY CASE WHEN AGENT_AVAILABILITY = :available THEN 0 ELSE 1 END, AGENT_ID',
            {'pref': normalized_category,
             'status': 'Active',
             'available': 'Available'})
        if not rows:
            # No Active agent matches this category: leave ticket Pending / unassigned.
            return None

        chosen = rows[0]
        agent_id = chosen.get('AGENT_ID')
        if is_empty(agent_id):
            return None
        agent_id = str(agent_id).strip()

        if str(chosen.get('AGENT_AVAILABILITY')).strip() != 'Available':
            # Only matching agent is Occupied: leave ticket Pending / unassigned.
            return None

        db.update('SUPPORT360_TICKET',
                  {'ASSIGNED_AGENT': agent_id, 'STATUS': 'Assigned'},
                  {'TICKET_NO': ticket_no_val})

        try:
            if db.table_exists('SUPPORT360_TICKET_ACTLOG'):
                db.insert('SUPPORT360_TICKET_ACTLOG', {
                    'TICKET_NO': ticket_no_val,
                    'ACTION_TYPE': 'Assigned',
                    'FIELD_CHANGED': 'ASSIGNED_AGENT',
                    'OLD_VALUE': None,
                    'NEW_VALUE': agent_id,
                    'CHANGED_BY': 'System',
                    'CHANGE_DATE': datetime.now()
                })
        except Exception:
            # Log-table write is best-effort only; never block the assignment.
            logging.exception('Failed to write SUPPORT360_TICKET_ACTLOG for ticket %s', ticket_no_val)

        return {'updates': {'assigned_agent': agent_id, 'status': 'Assigned'}}
    except Exception:
        logging.exception('auto_assign_agent failed for ticket %s', args.get('TICKET_NO'))
    return None
