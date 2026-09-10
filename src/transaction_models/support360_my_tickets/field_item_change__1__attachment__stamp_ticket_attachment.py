# project: Support360
# object_type: T
# object_name: support360_my_tickets
# event_type: field_item_change
# function_name: stamp_ticket_attachment
# form_no: 1
# field_name: attachment
# language: python
# description: Stamp attachment uploaded-by/date and log it
# functional_specification: On change of ATTACHMENT (a new file is uploaded to this ticket by the raising Employee), set ATTACHMENT_UPLOADED_BY to the current logged-in user and ATTACHMENT_UPLOADED_DATE to the current timestamp on this SUPPORT360_TICKET row (return {"updates": {"attachment_uploaded_by": ..., "attachment_uploaded_date": ...}}). This must work regardless of the ticket's current STATUS. Also append one entry to the ticket's Activity/History Log (table to be confirmed once the Ticket Activity Log object is designed) with TICKET_NO = this ticket, ACTION_TYPE = 'Attachment-Added', CHANGED_BY = current user, CHANGE_DATE = now; this log write must never block the attachment update.
# business_logic: Stamp attachment uploaded-by/date and log it


def _current_user(args):
    return coalesce(args.get('CHG_USER'), args.get('ADD_USER'), args.get('RAISED_BY'), '')


def run(args):
    attachment = args.get('ATTACHMENT')

    # File removed / cleared -> clear the stamps as well.
    if is_empty(attachment):
        return {'updates': {
            'attachment_uploaded_by': None,
            'attachment_uploaded_date': None,
        }}

    user = _current_user(args)
    stamp = now().strftime('%Y-%m-%d %H:%M:%S')

    # Stamped regardless of the ticket's current STATUS.
    updates = {
        'attachment_uploaded_by': user,
        'attachment_uploaded_date': stamp,
    }

    # Activity / History log. The dedicated Ticket Activity Log object does not
    # exist yet, so the entry is appended to the ticket's own ACTIVITY_HISTORY
    # column. Wrapped so a logging problem can never block the stamping.
    try:
        entry = '%s | Attachment-Added | %s | %s' % (stamp, user, attachment)
        history = args.get('ACTIVITY_HISTORY')
        updates['activity_history'] = entry if is_empty(history) \
            else str(history).rstrip() + '\n' + entry
    except Exception:
        pass

    return {'updates': updates}
