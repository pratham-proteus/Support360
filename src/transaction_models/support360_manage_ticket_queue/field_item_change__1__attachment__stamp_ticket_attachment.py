# project: Support360
# object_type: T
# object_name: support360_manage_ticket_queue
# event_type: field_item_change
# function_name: stamp_ticket_attachment
# form_no: 1
# field_name: attachment
# language: python
# description: Stamp attachment uploaded-by/date and log it
# functional_specification: On change of ATTACHMENT (a new file is uploaded to this ticket by the Support Agent), set ATTACHMENT_UPLOADED_BY to the current logged-in user and ATTACHMENT_UPLOADED_DATE to the current timestamp on this SUPPORT360_TICKET row (return {"updates": {"attachment_uploaded_by": ..., "attachment_uploaded_date": ...}}). This must work regardless of the ticket's current STATUS. Also append one entry to the ticket's Activity/History Log (table to be confirmed once the Ticket Activity Log object is designed) with TICKET_NO = this ticket, ACTION_TYPE = 'Attachment-Added', CHANGED_BY = current user, CHANGE_DATE = now; this log write must never block the attachment update. NOTE: this method name and contract must match the identical item_change wired on the ATTACHMENT column of support360_my_tickets — implement it once and reuse.
# business_logic: Stamp attachment uploaded-by/date and log it


def run(args):
    attachment = args.get('ATTACHMENT')

    # Attachment cleared -> clear the stamps as well; nothing to log.
    if is_empty(attachment):
        return {'updates': {
            'attachment_uploaded_by': None,
            'attachment_uploaded_date': None,
        }}

    # The payload carries no identity object, so the current user is taken from
    # the engine-stamped audit columns available on this form.
    current_user = coalesce(args.get('CHG_USER'), args.get('ADD_USER'), args.get('RAISED_BY'))
    stamp = now()
    ticket_no = args.get('TICKET_NO')

    # Activity-log entry. An item_change runs read-scoped (a db write here would
    # be rolled back), so the log is written via api.add_record, which commits in
    # its own transaction. A failure must never block the attachment stamping,
    # and it applies whatever the ticket's current STATUS is.
    if not_empty(ticket_no):
        try:
            api.add_record('support360_ticket_actlog', {
                'TICKET_NO': ticket_no,
                'ACTION_TYPE': 'Attachment-Added',
                'FIELD_CHANGED': 'ATTACHMENT',
                'NEW_VALUE': str(attachment)[:2000],
                'CHANGED_BY': current_user,
                'CHANGE_DATE': stamp,
            })
        except Exception:
            pass

    return {'updates': {
        'attachment_uploaded_by': current_user,
        'attachment_uploaded_date': stamp,
    }}
