## Ticket Management
### Create Support Ticket
- Description: Allows an Employee to log a new support ticket describing an issue or request they need help with.
- Data points: TICKET_NO (auto-generated), TITLE, DESCRIPTION, CATEGORY (dropdown, static list: HARDWARE, SOFTWARE, ACCESS, NETWORK; shown on the Create Ticket form immediately after DESCRIPTION, mandatory), PRIORITY_NAME, STATUS (defaults to Pending), RAISED_BY (current Employee - mandatory, auto-filled with the logged-in user's user id, displayed read-only), RAISED_BY_NAME (display-only, resolved from the logged-in user's id (RAISED_BY) to that user's EMAIL address, looked up from the platform's user/session login directory — the same directory of people who log in to the system — NOT from the Support Agent master; falls back to the raw RAISED_BY id if no email can be resolved), ASSIGNED_AGENT, ASSIGNED_AGENT_NAME (display-only, resolved from SUPPORT360_AGENT.AGENT_NAME via ASSIGNED_AGENT), CREATED_DATE, ATTACHMENT (one or more files).
- Business rules:
  - TITLE, DESCRIPTION, CATEGORY and PRIORITY_NAME are all mandatory; ticket cannot be saved without them. CATEGORY is shown on the Create Ticket form immediately after the DESCRIPTION field.
  - RAISED_BY is mandatory and is automatically set to the id of the currently logged-in user; it is shown read-only on the Add screen as the resolved user id (never as a raw parameter token) and is not user-editable.
  - RAISED_BY_NAME is resolved from RAISED_BY to that user's email address via a lookup against the platform's user/session login directory (the directory of people who log in to the system), NOT against the Support Agent master. This resolution happens as part of the same save as the new ticket (pre_commit), not as a separate step afterward. If no email can be resolved for that user id, RAISED_BY_NAME falls back to the raw RAISED_BY id so it is never blank.
  - CATEGORY is a mandatory dropdown with a fixed static list of values: HARDWARE, SOFTWARE, ACCESS, NETWORK (no longer sourced from SUPPORT360_CATEGORY_MASTER). The SUPPORT360_CATEGORY_MASTER table, its admin maintenance, and other screens referencing CATEGORY_NAME are unchanged — only the Create Ticket field is affected.
  - PRIORITY_NAME is a mandatory dropdown selected from the active Priority master (SUPPORT360_PRIORITY_MASTER where IS_ACTIVE = 'Y'). Note: this dropdown continues to be populated live from SUPPORT360_PRIORITY_MASTER (where IS_ACTIVE = 'Y') — only the dedicated admin maintenance screen for this master has been removed; the underlying table and its data are unchanged.
  - TICKET_NO is system-generated and unique.
  - STATUS is set to Pending automatically on creation and is not user-editable at creation.
  - Show clear inline error messages when a mandatory field is missing or invalid, and a success message once the ticket is saved.
  - When CATEGORY is selected (and changed), the ticket is automatically assigned to the Support Agent whose PREFERENCE equals the selected CATEGORY value, but ONLY if that agent's AGENT_STATUS = Active (and, per existing logic, AGENT_AVAILABILITY as previously implemented): ASSIGNED_AGENT is auto-filled from SUPPORT360_AGENT.AGENT_ID where SUPPORT360_AGENT.PREFERENCE = CATEGORY AND SUPPORT360_AGENT.AGENT_STATUS = Active AND SUPPORT360_AGENT.AGENT_AVAILABILITY = Available. When an agent is found this way, STATUS is also automatically changed from Pending to Assigned at the same time. If the matching agent is Active but Occupied (availability not Available), or if no agent has a matching PREFERENCE at all, ASSIGNED_AGENT remains unset and STATUS stays Pending.
  - If the matching agent (PREFERENCE = CATEGORY_NAME, AGENT_STATUS = Active) is Occupied rather than Available, ASSIGNED_AGENT is still auto-filled with that agent and STATUS is automatically changed from Pending to Queued instead of Assigned. Once an Agent resolves the ticket, STATUS becomes Resolved; a ticket with STATUS = Resolved is read-only everywhere — on no screen can its fields or status be changed. On the Admin "Manage All Tickets" screen, a manager can also trigger this same auto-match manually via an "Assign Agent" button, visible only while STATUS = Pending.
  - Note: the ticket's category is identified solely by CATEGORY_NAME. The CATEGORY_CODE column has been fully removed from SUPPORT360_TICKET and from every screen/grid that referenced it (Create Ticket, Manage Ticket Queue, Manage All Tickets, Ticket Assignment, My Tickets, Resolved Tickets, Ticket Activity Log, ticket grids, Admin Dashboard criteria, and the ticket business area). CATEGORY_NAME remains the mandatory dropdown sourced from SUPPORT360_CATEGORY_MASTER where IS_ACTIVE = 'Y', and the CATEGORY_NAME-to-SUPPORT360_AGENT.PREFERENCE auto-assign logic is unchanged.
- Business actions: Add, Edit (before assignment), Delete (own ticket, while Pending), Search.
- Additional data management: Every ATTACHMENT uploaded is linked to the TICKET_NO with uploaded-by and uploaded-date; an entry is written to the ticket's Activity/History Log recording ticket creation.

### My Tickets
- Description: Lets an Employee view and track all tickets they have raised, including current status and updates from the Support Agent.
- Data points: TICKET_NO, TITLE, CATEGORY_CODE, PRIORITY_CODE, STATUS, ASSIGNED_AGENT, CREATED_DATE, LAST_UPDATED_DATE; on drill-in: full DESCRIPTION, ATTACHMENT list, AGENT_COMMENTS, ACTIVITY_HISTORY.
- Business rules:
  - Employee can only view/act on tickets where RAISED_BY = current Employee (row-level restriction to own tickets).
  - Attachments can be added by the Employee at any point in the ticket's life, regardless of STATUS — except once the ticket is Resolved, after which no further attachments may be added.
  - Resolved is the final status for a ticket; a ticket cannot be reopened once it reaches Resolved.
  - Once STATUS = Resolved, the ticket becomes fully read-only everywhere it appears (Create Support Ticket, My Tickets, Manage Ticket Queue, Manage All Tickets, Ticket Assignment): no field may be edited, no attachment may be added, no comment may be posted, and no status-changing or assignment action may be run.
- Business actions: Search, Filter (by STATUS, CATEGORY_CODE, PRIORITY_CODE, date range), View, Add-attachment, Add-comment.
- Additional data management: None beyond the ticket's own Activity/History Log, which records every status change, comment, and attachment addition.

### Resolved Tickets
- Description: Lets an Employee view the tickets they raised that are currently in Resolved status, which is the final status for a ticket.
- Data points: TICKET_NO, TITLE, CATEGORY_CODE, PRIORITY_CODE, STATUS (fixed to Resolved), ASSIGNED_AGENT, CREATED_DATE, CHG_DATE; on drill-in: DESCRIPTION, ATTACHMENT, AGENT_COMMENTS, RESOLUTION_NOTES, ACTIVITY_HISTORY.
- Business rules:
  - View is restricted to tickets where RAISED_BY = current Employee and STATUS = 'Resolved' only (row-level and status restriction).
  - Add, Edit and Delete are disabled; this is a read-only list.
  - Resolved is the final status for a ticket; tickets cannot be reopened once Resolved, and no action on this screen can change the STATUS.
- Business actions: Search, View.
- Additional data management: None; this is a read-only view of tickets already in their final Resolved status.

## Agent Ticket Desk
### Manage Ticket Queue
- Description: Enables a Support Agent to view incoming and assigned tickets, take ownership, work them through resolution, and communicate with the Employee via comments.
- Data points: TICKET_NO, TITLE, DESCRIPTION, CATEGORY_CODE, PRIORITY_CODE, STATUS, RAISED_BY, ASSIGNED_AGENT, CREATED_DATE, LAST_UPDATED_DATE, ATTACHMENT list, COMMENT (text, commented-by, commented-date, list), RESOLUTION_NOTES.
- Business rules:
  - Only tickets with STATUS in (Open, Assigned) that are unassigned or assigned to the current Agent are actionable by that Agent.
  - Assignment of a ticket is not performed from this screen; it is done from the separate Ticket Assignment screen. The ticket queue grid/list shows the assigned agent's name (not just the agent code) in an "Assigned To" column; a ticket must already be assigned before it can move to Resolved.
  - RESOLUTION_NOTES is mandatory before a ticket can be moved to Resolved.
  - STATUS follows a strict forward-only flow: Open → Assigned → Resolved. No other transition is permitted from this screen; tickets transition directly from Assigned to Resolved with no intermediate In Progress step.
  - A ticket with STATUS = Open cannot be set directly to 'Resolved'. It must first be moved to Assigned from the Ticket Assignment screen (Manage Ticket Assignment) or via the Assign action.
  - Only a ticket with STATUS = Assigned may be changed to 'Resolved' (Resolution Notes remain mandatory before resolving).
  - Changing STATUS to the same value, or backwards (e.g. Resolved → Assigned), is rejected with a clear inline error naming the current status and the attempted status.
  - Attachments can be added by the Agent at any point in the ticket's life, regardless of STATUS.
  - Show inline error messages for invalid transitions or missing mandatory fields (e.g. resolving without RESOLUTION_NOTES), and success messages on save.
  - Support Agents can directly edit ticket fields (TITLE, DESCRIPTION, CATEGORY_CODE, PRIORITY_CODE, STATUS, RAISED_BY) from Manage Ticket Queue using the standard Edit action, in addition to the dedicated Add Comment, Add Attachment, and Resolve actions; ASSIGNED_AGENT is maintained only from the Ticket Assignment screen.
  - When an Agent edits a ticket, the STATUS dropdown offers only one selectable value: Resolved. Assigned is no longer a user-selectable status on this screen — it is set only by the assignment action.
  - A ticket with STATUS = Reopen returns to Assigned, and can then be moved to Resolved by the Support Agent using the Resolve action — the same sequence as Assigned → Resolved.
  - The Raised By column shown to the Agent displays the raiser's resolved display name (RAISED_BY_NAME), never the raw user id.
  - STATUS additionally supports the value 'Not Resolved' alongside Pending, Assigned, Queued and Resolved. The Agent selects 'Not Resolved' from the Status dropdown on an Assigned/Queued ticket when the issue cannot be resolved.
  - When the Agent sets STATUS to 'Not Resolved' and clicks Save or Save & Close, the Add Comment field (NEW_COMMENT) is mandatory; the ticket cannot be saved without a comment explaining why it was not resolved.
  - If a ticket's STATUS is Pending, it cannot be moved directly to Resolved or Not Resolved; the ticket must first be moved to Assigned or Queued (i.e. assigned to a Support Agent) before it can be set to Resolved or Not Resolved. Attempting to set STATUS from Pending to Resolved or Not Resolved must be blocked with a clear inline error message instructing the Agent to assign the ticket first.
- Business actions: Search, Filter (by STATUS, PRIORITY_CODE, CATEGORY_CODE, ASSIGNED_AGENT), View, Edit, Add-comment, Add-attachment, Resolve.
- Additional data management: Every assignment, status change, comment, and attachment addition writes a timestamped entry to the ticket's Activity/History Log capturing old value, new value, and changed-by.

### Ticket Assignment
- Description: Lets a Support Agent view a single ticket's key details and assign the Support Agent handling it.
- Data points: TICKET_NO (read-only), TITLE (read-only), ASSIGNED_AGENT (editable, lookup to active Support Agents), STATUS (read-only).
- Business rules:
  - Opened directly for a specific ticket when the Employee clicks 'Assign Agent' on the Create Support Ticket screen (TICKET_NO carried over as context).
  - ASSIGNED_AGENT must be an Agent from SUPPORT360_AGENT with AGENT_STATUS = Active.
  - A ticket is editable on this screen only while its STATUS = Open; for every other STATUS value (Assigned, In Progress, Resolved, Closed) the ticket is fully view-only on this screen and the Assigned Agent field cannot be changed.
  - Once a ticket's STATUS = Closed, the Ticket Assignment screen for that ticket is fully view-only — ASSIGNED_AGENT and all other fields are read-only and no assignment/reassignment actions can be performed. Tickets with any other STATUS remain editable as today.
  - A ticket with STATUS = In Progress cannot be edited on this screen — the Assigned Agent field is protected, the Save action is hidden, and any attempt to save is blocked with an error, exactly like the existing Closed-status read-only behavior.
  - The Assigned Agent lookup on Manage Ticket Assignment shows only Agents whose Status (AGENT_STATUS) = Active; Inactive agents are never shown. Among Active agents, those whose Availability (AGENT_AVAILABILITY) = Occupied remain visible in the list for informational purposes but cannot be selected or saved as the Assigned Agent — attempting to select/save an Occupied agent shows an inline error and the assignment is rejected. Only Active agents with Availability = Available can actually be assigned.
  - An explicit "Assign Agent" action/button is provided on the Ticket Assignment screen. Clicking "Assign Agent" no longer requires ASSIGNED_AGENT to be pre-filled/selected beforehand; the action determines the agent automatically. The action is only available while the ticket is not Closed or In Progress.
  - Clicking "Assign Agent" reads the ticket's CATEGORY_CODE from SUPPORT360_TICKET (looked up via TICKET_NO on this form). If the ticket's STATUS is already 'Assigned', the action shows the message 'This ticket is already assigned' and stops without making any changes. Otherwise it searches SUPPORT360_AGENT for an agent whose PREFERENCE matches the ticket's category (case-insensitive, trimmed comparison) AND AGENT_STATUS = 'Active' AND AGENT_AVAILABILITY = 'Available', picking the agent with the lowest AGENT_ID when multiple agents tie. If no such agent is found, it shows 'No available agent found for category <category_name>' and stops without making any changes. If a matching agent is found, it sets ASSIGNED_AGENT to that agent's AGENT_ID, sets ASSIGNED_AGENT_NAME to that agent's AGENT_NAME, and sets STATUS = 'Assigned' on this form; it also updates the corresponding SUPPORT360_TICKET record's STATUS to 'Assigned', saves, refreshes the form, and shows the message 'Ticket assigned to <Agent Name>'.
  - ASSIGNED_AGENT_NAME and STATUS are read-only on this form; they can be changed only as a result of the Assign Agent action, never by direct user edit.
- Data points (additional): ASSIGNED_AGENT_NAME (read-only, resolved from SUPPORT360_AGENT.AGENT_NAME via ASSIGNED_AGENT).
- Business actions: Save/Update Assigned Agent, Assign Agent.

## Admin Setup
### Manage All Tickets
- Description: Gives the Admin an organization-wide, non-row-restricted view of every ticket, with the ability to directly assign, reassign and otherwise intervene on any ticket.
- Data points: TICKET_NO (read-only), TITLE, DESCRIPTION, CATEGORY_CODE, CATEGORY_NAME (display-only), PRIORITY_CODE, PRIORITY_NAME (display-only), STATUS, RAISED_BY (display-only), ASSIGNED_AGENT, CREATED_DATE, LAST_UPDATED_DATE, ATTACHMENT, COMMENT (new comment plus running AGENT_COMMENTS list), RESOLUTION_NOTES, CLOSED_DATE (display-only), CLOSED_BY (display-only), ACTIVITY_HISTORY (read-only).
- Business rules:
  - No row-level restriction: Admin can view and act on tickets regardless of RAISED_BY or ASSIGNED_AGENT.
  - RESOLUTION_NOTES is mandatory before STATUS can be moved to Resolved.
  - Once STATUS = Closed, the ticket is fully read-only on this screen: TITLE, DESCRIPTION, CATEGORY_CODE, PRIORITY_CODE, RAISED_BY, ASSIGNED_AGENT, ATTACHMENT, COMMENT and RESOLUTION_NOTES can no longer be changed, and the Assign/Reassign actions are hidden.
- Business actions: Search, View, Edit, Assign (visible while STATUS = Open; assigns the Admin-selected agent and moves STATUS to Assigned), Reassign (visible while STATUS is Open, Assigned or In Progress; changes ASSIGNED_AGENT without changing STATUS), Assign Agent (on-demand action, visible only while STATUS = Pending and ASSIGNED_AGENT is empty) — clicking it opens the Ticket Assignment screen (support360_ticket_assignment) for the current ticket.
- Additional data management: Every assignment, reassignment, status change, comment and attachment addition writes a timestamped entry to the ticket's Activity/History Log capturing old value, new value and changed-by; closing a ticket stamps CLOSED_DATE and CLOSED_BY.

### My Agents
- Description: Admin maintains the master list of Support Agents with their availability, status and preference.
- Data points: AGENT_ID, AGENT_NAME, AGENT_AVAILABILITY (dropdown: Available, Occupied), AGENT_STATUS (dropdown: Active, Inactive), PREFERENCE (VARCHAR(50), dropdown, editable, optional — the agent's area of expertise/preference).
- Business rules:
  - AGENT_ID and AGENT_NAME are mandatory; AGENT_ID is unique.
  - AGENT_AVAILABILITY must be one of Available, Occupied; AGENT_STATUS must be one of Active, Inactive.
  - PREFERENCE must be one of HARDWARE, SOFTWARE, ACCESS, NETWORK.
  - Deactivating an Agent (AGENT_STATUS set to Inactive) automatically sets AGENT_AVAILABILITY to Occupied and protects it from edits; activating the Agent restores AGENT_AVAILABILITY to Available and unprotects it.
- Business actions: Search, Add, Edit, Activate Agent, Deactivate Agent.
- Additional data management: None beyond master persistence.

## Search, Filters & Dashboards
### All Tickets (V)
- Visualization: Grid
- Criteria: TICKET_NO, STATUS, PRIORITY_CODE, CATEGORY_CODE, ASSIGNED_AGENT, RAISED_BY, CREATED_DATE range.
- Data points: TICKET_NO, TITLE, CATEGORY_CODE, PRIORITY_CODE, STATUS, RAISED_BY, ASSIGNED_AGENT, CREATED_DATE, LAST_UPDATED_DATE.
- Drill-down: Clicking a row opens the ticket detail (Ticket Management / Agent Ticket Desk depending on role).

### Ticket Count by Status (V)
- Visualization: Column-Chart
- Criteria: CREATED_DATE range, CATEGORY_CODE (optional).
- Data points: STATUS (x-axis) vs COUNT_OF_TICKETS (y-axis).
- Drill-down: Clicking a status bar opens All Tickets (V) filtered by that STATUS.

### Ticket Count by Priority (V)
- Visualization: Pie-Chart
- Criteria: CREATED_DATE range, STATUS (optional).
- Data points: PRIORITY_CODE (segment) vs COUNT_OF_TICKETS (value).
- Drill-down: Clicking a segment opens All Tickets (V) filtered by that PRIORITY_CODE.

### My Open Tickets Count (V)
- Visualization: Card
- Criteria: RAISED_BY = current Employee (default, fixed).
- Data points: COUNT_OF_TICKETS where STATUS in (Open, Assigned, In Progress).
- Drill-down: Clicking the card opens My Tickets filtered to open statuses.

### My Tickets Awaiting Confirmation Count (V)
- Visualization: Card
- Criteria: RAISED_BY = current Employee (default, fixed).
- Data points: COUNT_OF_TICKETS where STATUS = Resolved.
- Drill-down: Clicking the card opens My Tickets filtered to STATUS = Resolved.

### My Queue Count (V)
- Visualization: Card
- Criteria: ASSIGNED_AGENT = current Agent (default, fixed).
- Data points: COUNT_OF_TICKETS where STATUS in (Assigned, In Progress).
- Drill-down: Clicking the card opens Agent Ticket Desk filtered to the current Agent's active tickets.

### Unassigned Tickets Count (V)
- Visualization: Card
- Criteria: STATUS = Open (default, fixed).
- Data points: COUNT_OF_TICKETS where STATUS = Open and ASSIGNED_AGENT is blank.
- Drill-down: Clicking the card opens Agent Ticket Desk filtered to unassigned Open tickets.

### My Queue by Priority (V)
- Visualization: Bar-Chart
- Criteria: ASSIGNED_AGENT = current Agent (default, fixed), STATUS (optional).
- Data points: PRIORITY_CODE (y-axis) vs COUNT_OF_TICKETS (x-axis) for tickets assigned to current Agent.
- Drill-down: Clicking a bar opens Agent Ticket Desk filtered to that PRIORITY_CODE.

### Total Open Tickets Count (V)
- Visualization: Card
- Criteria: none (organization-wide, default).
- Data points: COUNT_OF_TICKETS where STATUS in (Open, Assigned, In Progress).
- Drill-down: Clicking the card opens All Tickets (V) filtered to open statuses.

### Total Resolved This Period Count (V)
- Visualization: Card
- Criteria: CREATED_DATE range (default: current month).
- Data points: COUNT_OF_TICKETS where STATUS in (Resolved, Closed) and LAST_UPDATED_DATE within range.
- Drill-down: Clicking the card opens All Tickets (V) filtered to Resolved/Closed within the period.

### Tickets by Status Trend (V)
- Visualization: Stacked-Column-Chart
- Criteria: CREATED_DATE range (default: last 30 days).
- Data points: CREATED_DATE (x-axis, by day/week) vs COUNT_OF_TICKETS stacked by STATUS.
- Drill-down: Clicking a segment opens All Tickets (V) filtered to that date bucket and STATUS.

### Ticket Detail Log (V)
- Visualization: Grid
- Criteria: TICKET_NO, CHANGED_BY, CHANGE_DATE range, ACTION_TYPE.
- Data points: TICKET_NO, ACTION_TYPE, FIELD_CHANGED, OLD_VALUE, NEW_VALUE, CHANGED_BY, CHANGE_DATE.
- Drill-down: Clicking a row opens the parent ticket's detail view.

## Activity & History Log
### Ticket Activity Log
- Description: Maintains a chronological, non-editable record of every change made to a ticket — creation, assignment, status change, comment, attachment, and edit — for audit and traceability.
- Data points: TICKET_NO, ACTION_TYPE (Created, Assigned, Status-Changed, Commented, Attachment-Added, Edited, Closed), FIELD_CHANGED, OLD_VALUE, NEW_VALUE, CHANGED_BY, CHANGE_DATE.
- Business rules:
  - Log entries are system-generated only; no manual add/edit/delete is permitted by any role.
  - An entry is created automatically whenever a ticket is created, assigned, its status changes, a comment or attachment is added, or its fields are edited.
- Business actions: Search, View (read-only).
- Additional data management: None; this activity is itself the cross-update target written by all other ticket actions.

## Dashboards
### Employee Dashboard (Note)
- 'My Tickets by Priority' and 'My Tickets Status Trend' are no longer composed into a parent Employee Dashboard object. They are now standalone navigation entries under a top-level 'Dashboard' menu.
- Each retains its existing scope: row-level filtered to RAISED_BY = current logged-in Employee.

### Support Agent Dashboard
- Role: Support Agent
- Criteria: ASSIGNED_AGENT = current Agent (fixed default), CREATED_DATE range (default: last 30 days, adjustable).
- Visuals:
  - My Queue Count — Card — count of tickets assigned to current Agent with STATUS in (Assigned, In Progress).
  - Unassigned Tickets Count — Card — count of Open tickets with no ASSIGNED_AGENT (organization-wide, not filtered to current Agent).
  - My Queue by Priority — Bar-Chart — own assigned tickets grouped by PRIORITY_CODE.
  - My Queue by Status — Column-Chart — own assigned tickets grouped by STATUS.
  - My Active Tickets Grid — Grid — TICKET_NO, TITLE, PRIORITY_CODE, STATUS, RAISED_BY, LAST_UPDATED_DATE for own active tickets.
- Drill-through: My Queue Count and My Queue by Status drill to Agent Ticket Desk filtered by the clicked STATUS; Unassigned Tickets Count drills to Agent Ticket Desk filtered to unassigned Open tickets; My Queue by Priority drills to Agent Ticket Desk filtered by the clicked PRIORITY_CODE; My Active Tickets Grid rows drill to ticket detail.

### Admin Dashboard
- Role: Admin
- Criteria: CREATED_DATE range (default: current month, adjustable), CATEGORY_CODE (optional).
- Visuals:
  - Total Open Tickets Count — Card — organization-wide count of tickets with STATUS in (Open, Assigned, In Progress).
  - Total Resolved This Period Count — Card — organization-wide count of tickets Resolved/Closed within the selected period.
  - Ticket Count by Status — Column-Chart — organization-wide tickets grouped by STATUS.
  - Ticket Count by Priority — Pie-Chart — organization-wide tickets grouped by PRIORITY_CODE.
  - Tickets by Status Trend — Stacked-Column-Chart — daily/weekly ticket volume stacked by STATUS over the selected period.
- Drill-through: Total Open Tickets Count and Ticket Count by Status drill to All Tickets (V) filtered by the clicked STATUS; Ticket Count by Priority drills to All Tickets (V) filtered by the clicked PRIORITY_CODE; Tickets by Status Trend drills to All Tickets (V) filtered by the clicked date bucket and STATUS.