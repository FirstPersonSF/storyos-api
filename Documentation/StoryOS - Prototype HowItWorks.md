# **StoryOS**

# **Prototype**

**Version: 01**

# **HOW IT WORKS**

## Context

**Rendering** is the process of taking all the *structured ingredients* in the system — the content, structure, and style rules — and combining them into an actual *finished output* that a person can read or export. It’s the step when the system **turns data into a document.**

**Render time** is the moment the system is actively generating the output. It’s distinct from storage time (when Elements are saved in the UNF) and assembly time (when the system organizes them into sections). At render time, the system temporarily transforms the content so it looks and reads right — but it never changes the source Elements.

| Phase | Description | Data |
| :---- | :---- | :---- |
| Storage | Elements exist in UNF. Neutral text only. | Persistent |
| Assembly | Deliverable Template \+ Story Model combine Elements. | Temporary |
| Render time | Brand Voice filter and formatting applied → final output created. | Output-only transformation |

## How the process works step-by-step

Let’s follow what happens when a user presses **“Generate”** for a Deliverable like a Press Release: 

1. **Retrieve story data**  
   The system looks at your **Deliverable Template** and fetches the **Elements** it’s bound to (e.g., Problem, Vision Statement, Boilerplate) from the Unified Narrative Framework (UNF).  
     
2. **Assemble structure**  
   Using the **Story Model** (e.g., Inverted Pyramid), it arranges those **Elements** into the right section order: headline, lede, quotes, etc. This creates the *assembled draft.*  
     
3. **Apply Brand Voice filter**  
   The **Brand Voice** rules are now applied: the tone, wording, and stylistic consistency. This is the *render-time* part. The system scans the assembled draft and makes stylistic adjustments or checks for violations.  
     
4. **Output generation**  
   After applying the **Brand Voice**, the system *renders* the final file: an on-screen preview of an on-screen preview or export (PDF, DOCX, HTML). That rendered version is what StoryOS users see.

## Analogy: Kitchen and recipe

Imagine StoryOS like a kitchen:

* **UNF Story Elements** \= ingredients in the pantry.  
* **Story Model** \= the recipe order (“first sauté, then simmer”).  
* **Deliverable Template** \= the list of portions and plating instructions.  
* **Brand Voice** \= the seasoning that gives the final dish the right flavor.  
* **Render time** \= the moment you plate the dish and serve it.

You wouldn’t permanently season the ingredients in the pantry — you season them when you cook and serve. That’s render time.

## Why this matters technically

By keeping rendering as a *late-stage transformation*, the system ensures:

* Elements remain reusable and voice-agnostic.  
* Multiple outputs can be rendered in different voices from the same data.  
* Voice or formatting updates apply automatically to all future renders.  
* Past outputs remain auditable and reproducible because each render logs which voice version was used.

## The Secret Ingredient

**Section bindings** are the links between a Deliverable Template’s *sections* (the placeholders that make up the structure of a document) and *the specific story data* (Elements) stored in the Unified Narrative Framework (UNF). They store instructions and references, not text, and serve as:

* The *instruction set* that tells the system how to fill each section of a Deliverable Template.  
* The *connection points* between story structure (Template) and story data (UNF).  
* The *mechanism* that keeps everything consistent, traceable, and updatable.


**1\. Every Template has “sections”**

Think of a Deliverable Template—like a *Brand Manifesto* or a *Press Release*—as a pre-defined outline. Each outline has sections that describe what belongs where. For example: Brand Manifesto template sections: 1\) The Problem,  2\) Our Vision, 3\) Our Principles, and 4\) Our Commitment. Each section has a purpose but no actual text yet—it’s a *slot* waiting to be filled.

**2\. The UNF stores reusable story content (Elements)**

The **Unified Narrative Framework (UNF)** holds story building blocks, such as:

* *Problem statement*  
* *Vision statement*  
* *Principles*  
* *Key messages*  
* *Boilerplate*

These are universal, reusable Elements that stay consistent across all outputs.

**3\. “Section bindings” connect the two**

A *section binding* tells the system *which Story Element* should fill *which section* in a Template. For example: 

* “For the Manifesto’s ‘Problem’ section, pull content from the UNF Element called *Problem* (in the Category layer).”  
* “For the Manifesto’s ‘Our Vision’ section, pull content from the UNF Element called *Vision Statement* (in the Vision layer).”

Each Template section has one or more *section bindings* that tell the system where to fetch content from and how to use it.

**4\. Bindings can include additional rules**

A section binding can also specify:

* **Quantity** — e.g., pull 3 of 5 Key Messages.  
* **Version** — use the latest approved Element version or a locked one.  
* **Transformation** — take only the headline, or summarize to 150 words.  
* **Formatting** — bullet list, paragraph, or quote style.

This lets a single Element be reused in different ways across different Deliverables.

**5\. Why section bindings matter**

They give the system *intelligence and control*. Instead of copying and pasting text:

* Every section knows exactly which approved content it depends on.  
* If a UNF Element (like the Vision Statement) changes, the system can flag every section bound to it.  
* Templates stay reusable, because they don’t hold actual text—just binding instructions.

**6\. Example**

Here’s a simplified **Press Release template** with section bindings:

| Section | Binding (where content comes from) | Validation rules |
| :---- | :---- | :---- |
| Headline | UNF → Messaging → Key Messages | Use the top-ranked Key Message |
| Lede paragraph | UNF → Vision → Vision Statement | Include one-sentence summary |
| Quote 1 | UNF → Vision → Principles | Use the first principle as quote base |
| Boilerplate | UNF → Messaging → Boilerplate | Always include full approved version |

