# project: Support360
# object_type: T
# object_name: support360_manage_ticket_queue
# event_type: pre_commit
# function_name: set_status_assigned_on_save
# language: python
# description: No-op; STATUS transitions are owned elsewhere
# functional_specification: This hook no longer modifies STATUS. The Pending->Assigned transition is the sole responsibility of form_action__1__assign_agent_by_preference.py, which only changes STATUS when it actually finds a matching agent. Leave STATUS untouched for any current value (including the existing 'Not Resolved' transition logic and its mandatory Add Comment rule, which are untouched).
# business_logic: No-op; STATUS is left untouched by this hook


def run(args):
    return None
