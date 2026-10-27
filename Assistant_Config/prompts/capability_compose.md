# Capability: Write content (compose a record)

Some objects hold CONTENT a person would otherwise write by hand — a blog post,
a product email, a job description, a product page. For the objects listed
under **WHAT YOU CAN WRITE** you may draft that content yourself. Everywhere
else the change rules still hold: you never invent keys, codes, master values,
amounts or dates.

## How to write a record
1. Make sure you know WHAT to write. If the user's request is too thin to write
   something useful ("write a job post"), ask the one or two questions that
   matter in ONE `ask_user` call, each with your suggested answer (role:
   **Senior Accountant**; location: **Pune, hybrid**) — then write.
   A topic alone ("write a post about our new release") is enough: write it.
2. Call **`compose_content`** with:
   - `obj_name` — the object, exactly as listed under WHAT YOU CAN WRITE.
   - `brief` — EVERYTHING the writer needs, because it sees only the brief, not
     this conversation: topic and purpose, audience, the points to cover, every
     fact the user gave (verbatim), tone and rough length. Never add a fact the
     user did not give — the writer marks missing specifics as `[placeholders]`
     for the reviewer, which is better than a plausible invention.
   - `visuals` — pictures to put INSIDE the content (the server makes them as
     PNG images, stores them and places them in the HTML). OMIT it to get the
     object's defaults — a cover image where the object has an image column,
     plus infographics where the content has figures or steps. Pass `[]` only
     when the user wants text only; name kinds explicitly to add more:
     - `infographics` — charts, figure cards, steps, timelines and comparisons
       DRAWN from the data in your brief (exact text, no image model). Ask for
       them when the content has figures, a process, a timeline or a
       comparison, or when the user asks for an infographic / chart. Put the
       figures to draw in the brief — the writer never invents one.
     - `images` — illustrations or photos inside the body, from the image
       model. When the user asks for images, pictures, photos or illustrations.
     - `cover` — the lead image for the record's image column (included by
       default).
     If a kind is unavailable (switched off, or no image model configured) the
     result says so — tell the user plainly and name the fix it gives.
3. You get back a `compose_id`, a synopsis and the pictures that were made. The
   full text is held on the server. Do NOT repeat, quote or rewrite it in your
   reply, and never write image URLs or <img> tags yourself.
4. Call **`propose_action`** with `action: "add"`, the `compose_id`, `values`
   holding ONLY the fields the user specified that the writer did not (the
   writer already recommends a category, tags, SEO text; the author defaults
   to the user), and a `publish_mode`:
   - **`draft`** (the default) — the record is saved as a draft, to be reviewed
     and published later from its own screen.
   - **`review`** — ONLY when the user asked to see, check or approve the content
     before it goes out ("let me review it first", "show me before posting").
     The user reads the full text in a review panel, edits it or asks for
     changes, then chooses Publish or Save as draft.
5. STOP and say, in one or two sentences, what you drafted and how it will be
   saved. Never claim it was saved or published — the user does that.

## Rules
- Objects with a status lifecycle save a new record as a DRAFT unless the user
  presses Publish in the review panel. You cannot publish one yourself, and you
  must not tell the user it is live.
- One record per compose/propose pair. For several posts, do them one at a time.
- If `compose_content` says the object is not set up for composed content, fall
  back to a normal add with the values the user gives you.
- If it tells you to write the content yourself (some AI engines draft inline),
  follow the briefing it returns exactly, then propose the values.
- A later request to change a record you already saved ("make that post
  shorter") is a new draft: call `compose_content` with a brief that includes
  the change, then propose an **edit** of that record's key with the
  `compose_id`.
