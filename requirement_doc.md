## Ticket Management
### Create Support Ticket
- Description: Allows an Employee to log a new support ticket describing an issue or request they need help with.
- Data points: TICKET_NO (auto-generated), TITLE, DESCRIPTION, CATEGORY_CODE, PRIORITY_CODE, STATUS (defaults to Open), RAISED_BY (current Employee), CREATED_DATE, ATTACHMENT (one or more files).
- Business rules:
  - TITLE, DESCRIPTION, CATEGORY_CODE and PRIORITY_CODE are mandatory; ticket cannot be saved without them.
  - CATEGORY_CODE must exist in active Category master; PRIORITY_CODE must exist in active Priority master.
  - TICKET_NO is system-generated and unique.
  - STATUS is set to Open automatically on creation and is not user-editable at creation.
  - Show clear inline error messages when a mandatory field is missing or invalid, and a success message once the ticket is saved.
- Business actions: Add, Edit (before assignment), Delete (own ticket, while Open), Search. Clicking Assign Agent opens the Ticket Assignment screen for the current ticket.
- Additional data management: Every ATTACHMENT uploaded is linked to the TICKET_NO with uploaded-by and uploaded-date; an entry is written to the ticket's Activity/History Log recording ticket creation.

### My Tickets
- Description: Lets an Employee view and track all tickets they have raised, including current status and updates from the Support Agent.
- Data points: TICKET_NO, TITLE, CATEGORY_CODE, PRIORITY_CODE, STATUS, ASSIGNED_AGENT, CREATED_DATE, LAST_UPDATED_DATE; on drill-in: full DESCRIPTION, ATTACHMENT list, AGENT_COMMENTS, ACTIVITY_HISTORY.
- Business rules:
  - Employee can only view/act on tickets where RAISED_BY = current Employee (row-level restriction to own tickets).
  - Attachments can be added by the Employee at any point in the ticket's life, regardless of STATUS.
  - Ticket can be moved to Closed only by the Employee, and only when STATUS = Resolved.
- Business actions: Search, Filter (by STATUS, CATEGORY_CODE, PRIORITY_CODE, date range), View, Add-attachment, Confirm-and-close, Reopen-comment (add comment; does not change status).
- Additional data management: Confirm-and-close action updates STATUS to Closed, stamps CLOSED_DATE and CLOSED_BY, and writes an entry to the Activity/History Log.

## Agent Ticket Desk
### Manage Ticket Queue
- Description: Enables a Support Agent to view incoming and assigned tickets, take ownership, work them through resolution, and communicate with the Employee via comments.
- Data points: TICKET_NO, TITLE, DESCRIPTION, CATEGORY_CODE, PRIORITY_CODE, STATUS, RAISED_BY, ASSIGNED_AGENT, CREATED_DATE, LAST_UPDATED_DATE, ATTACHMENT list, COMMENT (text, commented-by, commented-date, list), RESOLUTION_NOTES.
- Business rules:
  - Only tickets with STATUS in (Open, Assigned, In Progress) that are unassigned or assigned to the current Agent are actionable by that Agent.
  - Clicking the Assign action does not require the Agent to pick an assignee. The system randomly selects one Support Agent from the Agent master (SUPPORT360_AGENT) whose AGENT_STATUS = Active and AGENT_AVAILABILITY = Available, sets ASSIGNED_AGENT to that agent, and moves STATUS from Open to Assigned. The Assigned Agent field is not manually editable. The ticket queue grid/list shows the assigned agent's name (not just the agent code) in an "Assigned To" column; a ticket must be assigned before it can move to In Progress.
  - Starting work moves STATUS from Assigned to In Progress.
  - RESOLUTION_NOTES is mandatory before a ticket can be moved to Resolved.
  - STATUS transitions are restricted to the sequence Open → Assigned → In Progress → Resolved → Closed; no skipping or reverse transitions except Reassign (keeps current STATUS, changes ASSIGNED_AGENT).
  - Attachments can be added by the Agent at any point in the ticket's life, regardless of STATUS.
  - Show inline error messages for invalid transitions or missing mandatory fields (e.g. resolving without RESOLUTION_NOTES), and success messages on save.
  - Support Agents can directly edit ticket fields (TITLE, DESCRIPTION, CATEGORY_CODE, PRIORITY_CODE, STATUS, RAISED_BY, ASSIGNED_AGENT) from Manage Ticket Queue using the standard Edit action, in addition to the dedicated Assign, Reassign, Start Progress, Add Comment, Add Attachment, and Resolve actions.
- Business actions: Search, Filter (by STATUS, PRIORITY_CODE, CATEGORY_CODE, ASSIGNED_AGENT), Edit, Assign, Reassign, Start-progress, Add-comment, Add-attachment, Resolve.
- Additional data management: Every assignment, status change, comment, and attachment addition writes a timestamped entry to the ticket's Activity/History Log capturing old value, new value, and changed-by.

### Ticket Assignment
- Description: Lets a Support Agent view a single ticket's key details and assign or change the Support Agent handling it.
- Data points: TICKET_NO (read-only), TITLE (read-only), ASSIGNED_AGENT (editable, lookup to active Support Agents), STATUS (read-only).
- Business rules:
  - Opened directly for a specific ticket when the Employee clicks 'Assign Agent' on the Create Support Ticket screen (TICKET_NO carried over as context).
  - ASSIGNED_AGENT must be an Agent from SUPPORT360_AGENT with AGENT_STATUS = Active.
- Business actions: Save/Update Assigned Agent.

## Admin Setup
### Manage Category Master
- Description: Allows Admin to define and maintain the list of ticket categories used to classify support tickets.
- Data points: CATEGORY_CODE, CATEGORY_NAME, DESCRIPTION, IS_ACTIVE.
- Business rules:
  - CATEGORY_CODE and CATEGORY_NAME are mandatory and unique.
  - A Category cannot be deactivated/deleted if it is referenced by any existing ticket; it can only be marked inactive (retained for historical tickets) in that case.
- Business actions: Search, Add, Edit, Delete (only if unused), Activate/Deactivate.
- Additional data management: None beyond master persistence.

### Manage Priority Master
- Description: Allows Admin to define and maintain the list of priority levels used to rank ticket urgency.
- Data points: PRIORITY_CODE, PRIORITY_NAME, SEQUENCE_NO (for sort order/severity ranking), IS_ACTIVE.
- Business rules:
  - PRIORITY_CODE, PRIORITY_NAME and SEQUENCE_NO are mandatory; PRIORITY_CODE and SEQUENCE_NO are unique.
  - A Priority cannot be deactivated/deleted if it is referenced by any existing ticket; it can only be marked inactive in that case.
- Business actions: Search, Add, Edit, Delete (only if unused), Activate/Deactivate.
- Additional data management: None beyond master persistence.

### Manage All Tickets
- Description: Gives Admin an overarching view of all tickets in the system with the ability to correct data, reassign, or intervene in any ticket irrespective of who raised or is working it.
- Data points: TICKET_NO, TITLE, DESCRIPTION, CATEGORY_CODE, PRIORITY_CODE, STATUS, RAISED_BY, ASSIGNED_AGENT, CREATED_DATE, LAST_UPDATED_DATE, ATTACHMENT list, COMMENT list, ACTIVITY_HISTORY.
- Business rules:
  - Admin can view and edit any ticket regardless of RAISED_BY or ASSIGNED_AGENT (no row-level restriction).
  - Status transitions performed by Admin follow the same Open → Assigned → In Progress → Resolved → Closed sequence and validations as the Agent Ticket Desk.
  - Admin edits to TITLE, DESCRIPTION, CATEGORY_CODE or PRIORITY_CODE are permitted at any STATUS other than Closed.
  - ASSIGNED_AGENT is directly editable by the Admin on the ticket record (in addition to being settable via the Assign/Reassign actions); it may be left blank (unassigned) at any time.
- Business actions: Search, Filter (by STATUS, PRIORITY_CODE, CATEGORY_CODE, ASSIGNED_AGENT, RAISED_BY), Edit, Assign, Reassign, Delete.
- Additional data management: Any Admin change to a ticket writes an entry to the Activity/History Log capturing old value, new value, and changed-by.

## Search, Filters & Dashboards
### All Tickets (V)
- Visualization: Grid
- Criteria: TICKET_NO, STATUS, PRIORITY_CODE, CATEGORY_CODE, ASSIGNED_AGENT, RAISED_BY, CREATED_DATE range.
- Data points: TICKET_NO, TITLE, CATEGORY_CODE, PRIORITY_CODE, STATUS, RAISED_BY, ASSIGNED_AGENT, CREATED_DATE, LAST_UPDATED_DATE.
- Drill-down: Clicking a row opens the ticket detail (Ticket Management / Agent Ticket Desk / Manage All Tickets depending on role).

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
- Data points: TICKET_NO, ACTION_TYPE (Created, Assigned, Reassigned, Status-Changed, Commented, Attachment-Added, Edited, Closed), FIELD_CHANGED, OLD_VALUE, NEW_VALUE, CHANGED_BY, CHANGE_DATE.
- Business rules:
  - Log entries are system-generated only; no manual add/edit/delete is permitted by any role.
  - An entry is created automatically whenever a ticket is created, assigned/reassigned, its status changes, a comment or attachment is added, or its fields are edited.
- Business actions: Search, View (read-only).
- Additional data management: None; this activity is itself the cross-update target written by all other ticket actions.

## Dashboards
### Employee Dashboard
- Role: Employee
- Criteria: RAISED_BY = current Employee (fixed default), CREATED_DATE range (default: last 90 days, adjustable).
- Visuals:
  - My Open Tickets Count — Card — count of own tickets with STATUS in (Open, Assigned, In Progress).
  - My Tickets Awaiting Confirmation Count — Card — count of own tickets with STATUS = Resolved.
  - My Tickets by Status — Pie-Chart — own tickets grouped by STATUS.
  - My Tickets Grid — Grid — TICKET_NO, TITLE, CATEGORY_CODE, PRIORITY_CODE, STATUS, LAST_UPDATED_DATE for own tickets.
- Drill-through: My Open Tickets Count and My Tickets by Status drill to My Tickets (V) filtered by the clicked STATUS; My Tickets Grid rows drill to ticket detail.

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