# event: validation
# object: support360_manage_all_tickets
# form: 1
# field: status
# method: validate_ticket_status_transition
# description: Validate that the new ticket status is an allowed transition.
# functional_specification:
#   STATUS may only be 'In Progress' or 'Resolved'. On edit the stored status is
#   read and the transition checked: Resolved is a terminal state (it cannot be
#   re-opened to In Progress); a ticket may only move to In Progress when an agent
#   is assigned; a ticket may only move to Resolved when it has resolution notes
#   and an assigned agent. Re-selecting the same status is reported as an
#   informational prompt. Resolving a ticket that has no agent comments raises an
#   override-able warning.


ALLOWED = ['In Progress', 'Resolved']


def run(args):
    out = {'errors': []}
    ignored = set(args.get('_ignore_warnings') or [])

    new_status = args.get('STATUS')
    ticket_no = args.get('TICKET_NO')

    if is_empty(new_status):
        return 'Status is required.'

    if not in_list(new_status, 'In Progress,Resolved'):
        return 'Invalid status "' + str(new_status) + '". Allowed values are: In Progress, Resolved.'

    assigned = coalesce(args.get('ASSIGNED_AGENT'), '')
    old_status = ''

    if args.get('_action') == 'edit' and not_empty(ticket_no):
        cur = db.query_one(
            'SELECT STATUS, ASSIGNED_AGENT, AGENT_COMMENTS, RESOLUTION_NOTES '
            'FROM ' + db.t('SUPPORT360_TICKET') + ' WHERE TICKET_NO = :t',
            {'t': ticket_no})
        if cur:
            old_status = coalesce(cur.get('STATUS'), '')
            if is_empty(assigned):
                assigned = coalesce(cur.get('ASSIGNED_AGENT'), '')

    if old_status == 'Resolved' and new_status != 'Resolved':
        out['errors'].append({'code': 'VSTAT1', 'field': 'status', 'type': 'E',
                              'message': 'Ticket is already Resolved. A resolved ticket cannot be moved back to '
                                         + str(new_status) + '.'})

    if new_status == 'In Progress' and is_empty(assigned):
        out['errors'].append({'code': 'VSTAT2', 'field': 'status', 'type': 'E',
                              'message': 'Assign an agent before setting the status to In Progress.'})

    if new_status == 'Resolved':
        if is_empty(assigned):
            out['errors'].append({'code': 'VSTAT3', 'field': 'status', 'type': 'E',
                                  'message': 'A ticket without an assigned agent cannot be Resolved.'})
        if is_empty(args.get('RESOLUTION_NOTES')):
            out['errors'].append({'code': 'VSTAT4', 'field': 'resolution_notes', 'type': 'E',
                                  'message': 'Enter resolution notes before resolving the ticket.'})
        if is_empty(args.get('AGENT_COMMENTS')) and is_empty(args.get('NEW_COMMENT')):
            if 'VSTAT5' not in ignored:
                out['errors'].append({'code': 'VSTAT5', 'field': 'status', 'type': 'W',
                                      'message': 'This ticket is being resolved without any agent comments.'})

    if not_empty(old_status) and old_status == new_status:
        out['errors'].append({'code': 'VSTAT6', 'field': 'status', 'type': 'P',
                              'message': 'Status is unchanged (' + str(new_status) + ').'})

    if not out['errors']:
        return None

    blocking = [e for e in out['errors'] if coalesce(e.get('type'), 'E') == 'E']
    if blocking:
        out['error'] = blocking[0]['message']
    return out
