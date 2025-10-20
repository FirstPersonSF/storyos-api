# **StoryOS**

# **Prototype**

**Version: 01**

# **SYSTEM DETAILS**

## **1\. Unified Narrative Framework (UNF)**

### Definition

The **Unified Narrative Framework** is the structured repository of all reusable narrative building blocks in StoryOS. It defines a hierarchy of **Layers**, optional **Groups**, and atomic **Elements**, which supply content to all Deliverables. It is the system’s single source of truth for Story data.

### Role in system architecture

The UNF provides the foundational content objects that all other components reference. Deliverable Templates and Deliverables never store raw text; they pull approved content from the UNF by Element ID and version. This ensures version control, reuse, and traceability across the platform.

### Core attributes

| Attribute | Description |
| :---- | :---- |
| **Layer** | Logical container for a category of story data. *Prototype layers: Category, Vision, Messaging.* |
| **Group** | Optional UI-only label; not persisted as a separate database entity. Not required for logic. |
| **Element** | Atomic unit of narrative content *(e.g., Problem, Vision Statement, Key Messages)*. Addressable by ID and versioned. |
| **Status** | Draft, Approved, Archived. *Determines whether content is eligible for use in Deliverables.* |
| **Version control** | Each Element maintains version history with timestamps and authorship. |

### 

### Required system behaviors 

* **Addressability**: Each Element has a globally unique ID and is retrievable via Layer reference.

* **Versioning**: Editing is non-destructive and creates a new version; Deliverables maintain linkage to specific versions.

* **Validation**: Element-level validation rules (field completeness, length, structure).

* **Change propagation:** Updates to Elements trigger impact alerts for affected downstream Templates and Deliverables, identified by stored Element-to-Template/Deliverable references.

* **Audit trail:** Every Element’s revision history is recorded and available to view

### UNF interaction with other components

| Component | Interaction |
| :---- | :---- |
| **Deliverable Templates** | Templates query Elements to populate section bindings. |
| **Deliverables** | Deliverables pull approved Element versions at creation. |
| **Brand Voice** | Voice filter applies tone and style rules to Element text during render. |
| **Story Models** | Models determine how Elements are sequenced or combined in narrative flow. |

### 

### Acceptance criteria 

* Elements can be queried, versioned, and reused across multiple Deliverables.  
* Updates to Elements correctly trigger impact notifications.  
* Deliverables always reference specific Element versions.  
* Groups function as optional metadata without breaking logic.

## **2\. Brand Voice (Filter)**

### 

### Definition

**Brand Voice** is a modular filter system that governs how content from the UNF is expressed across Deliverables. Each Brand Voice represents a distinct configuration of tone, style, and vocabulary rules, ensuring consistent expression without altering meaning. Multiple voices can exist simultaneously to support parent brands, sub-brands, or regional variations.

### Role in system architecture

Acts as a *render-time expression layer* applied after content assembly but before output. Deliverable Templates and Deliverables reference a specific Brand Voice (and version) that defines how language is expressed. Voices are modular, versioned, and selectable, enabling different tones or vocabularies across divisions while maintaining system-wide governance.

### Core attributes

| Attribute | Description |
| :---- | :---- |
| **Voice ID** | Unique identifier for each active Brand Voice. *(e.g., Corporate, Product, Regional)* |
| **Traits** | Weighted descriptors defining personality. *(e.g., authoritative, candid, visionary)* |
| **Tone rules** | Formality, contractions, sentence length, POV. |
| **Style guardrails** | Do/don’t lists, banned jargon, formatting standards. |
| **Lexicon** | Required and prohibited terms, boilerplate phrases. |
| **Readability range** | Target complexity level of prose. *Guides how concise or technical language should be* |
| **Version** | Each Voice configuration is versioned for audit, reproducibility, and historical reference. |

### 

### Required system behaviors

* **Render filter**: Apply after content assembly and before output.

* **Non-destructive**: Does not modify source Elements.

* **Multi-voice support**: Allow multiple Brand Voices to coexist and be selected per Template or Deliverable.

* **Inheritance rules**: Sub-brand voices can inherit or override parent voice attributes.

* **Compliance validation**: Detect rule violations; block output if critical.

* **Per-section overrides**: Templates can tighten or relax rules for specific sections.

* **Reporting**: Log which Voice ID was applied, version, and compliance results for each Deliverable render.

### Brand Voice interaction with other components

| Component | Interaction |
| :---- | :---- |
| **Deliverables** | Enforces selected Voice and logs applied version during rendering. |
| **Deliverable Templates** | Defines default Voice ID and version, or allows selection per deliverable type. |
| **UNF Elements** | Applies style and tone rules at render time without modifying stored Element content. |

### 

### Acceptance criteria

* Multiple Brand Voices can exist and be independently versioned.  
* Each Deliverable accurately records the Voice ID and version used.  
* Voice rules apply consistently across all Deliverables.  
* Violations are detected and reported accurately.  
* Source Elements remain unchanged by Voice processing.

## **3\. Story Models (Filter)**

### 

### Definition

**Story Models** define narrative structures and logical flows that guide how Elements from the UNF are arranged within a Deliverable. Each Model provides a repeatable schema for storytelling patterns.

### Role in system architecture

Story Models function as **structural templates** beneath Deliverable Templates. They define section order within the template, purpose, and constraints that ensure consistent storytelling logic.

### Core attributes

| Attribute | Description |
| :---- | :---- |
| **Model ID** | Unique identifier for the Story model. |
| **Name** | Model name. *(e.g., Hero’s Journey, PAS, Inverted Pyramid)* |
| **Sections** | Ordered list of narrative segments. *(e.g., Problem, Solution, Lede, Quote)* |
| **Intent** | Purpose of each section. *(e.g., problem framing, proof, resolution)* |
| **Constraints** | Rules that ensure each section has required content and makes sense. |

### 

### Required system behaviors

* **Section definition**: Model defines fixed sections and their purpose.  
* **Validation logic**: Each section validates that required data is populated.  
* **Swap compatibility**: Deliverables can change models; the system revalidates and remaps sections.  
* **Extensibility**: New models can be added without altering UNF structure.

### Story Model interaction with other components

| Component | Interaction |
| :---- | :---- |
| **Deliverable Templates** | Templates bind their structure to a chosen Story Model. |
| **Deliverables** | Deliverables inherit section structure and validation from the associated Story Model. |
| **UNF Elements** | Models define how Element data fills each section. |

### 

### Acceptance criteria

* Story Models define consistent section schemas usable across Templates.  
* Section validation enforces narrative completeness.  
* Deliverables can swap models with correct revalidation.  
* New Story Models can be added and activated without custom coding.

## **4\. Deliverable Templates**

### 

### Definition

A **Deliverable Template** is a reusable configuration that defines how a specific type of content (e.g., Press Release, Brand Manifesto) is constructed. It combines Story Model structure, UNF Element bindings, Brand Voice rules, and validation constraints.

### Role in system architecture

Templates are **blueprints** that govern Deliverable creation. They ensure each content type uses the same story logic, data bindings, and tone policies.

### Core attributes

| Attribute | Description |
| :---- | :---- |
| **Template ID / Version** | Unique and versioned blueprint identifier. |
| **Associated Story Model** | Defines narrative sections and intent. |
| **Element bindings** | Mappings between UNF Elements and Template sections. |
| **Brand Voice reference** | Default Voice version and any section-level overrides. |
| **Validation rules** | Required sections, max lengths, formatting standards. |
| **Governance policy** | Rules for mandatory inclusions (e.g., Boilerplate in Press Release). |

### 

### Required system behaviors

* **Binding resolution**: Pull content from specified Elements based on ID/version.

* **Validation enforcement**: Prevent incomplete or noncompliant Deliverables from publishing.

* **Voice application**: Apply Brand Voice defaults unless overridden.

* **Versioning**: Changes to Templates create new versions for future Deliverables.

* **Migration support**: Deliverables can opt to migrate to newer Template versions.

### Deliverable Templates interaction with other components

| Component | Interaction |
| :---- | :---- |
| **UNF Elements** | Source content for section bindings. |
| **Story Models** | Provides section structure and logic. |
| **Brand Voice** | Applies expression and tone rules. |
| **Deliverables** | Instantiated from Templates as working outputs. |

### 

### Acceptance criteria

* Deliverable Templates can be versioned, cloned, and reused.  
* All section bindings resolve valid Element data.  
* Governance rules (e.g., required Boilerplate) are enforced.  
* Deliverables created from a Deliverable Template remains stable even if the Deliverable Template updates.

## **5\. Deliverables**

### 

### Definition

A **Deliverable** is a single, time-bound instance rendered from a Deliverable Template. It represents the practical application of story data (UNF Elements), structural logic (Story Model), and tone (Brand Voice) to produce a tangible piece of content.

### Role in system architecture

Deliverables exist at the *execution layer*. They are where reusable story data becomes specific, version-locked outputs. They test the integrity of all preceding components by combining them in a real-world workflow.

### Core attributes

| Attribute | Description |
| :---- | :---- |
| **Deliverable ID / Version** | Unique instance identifier with version history. |
| **Deliverable Template version reference** | The exact Deliverable Template used to generate this instance. |
| **Story Model reference** | Structure applied to its narrative. |
| **Brand Voice reference** | Brand Voice ID and version reference (for reproducibility). |
| **Element provenance** | Per section, the Element IDs and versions used. |
| **Status** | Draft, Review, Approved, Published. |
| **Validation log** | Results of all checks (structure, tone, completeness). |
| **Render artifacts** | Output files (PDF, DOCX, HTML). |
| **Owner / Permissions** | Assigned user roles for editing and approval. |

### Deliverable Instance Fields (Temporary Data)

Certain Deliverable Templates, such as a Press Release, require fields that are unique to each Deliverable and not stored in the Unified Narrative Framework (UNF). These are called **Instance Fields** and are tied only to the specific Deliverable where they’re used.

Instance Fields are temporary data inputs—like “who, what, when, where, and why”—that provide contextual information required by a Deliverable Template but not reusable across other content. 

They exist only at the Deliverable level and are captured before rendering.

**Behavior**

* Each Deliverable Template declares its required Instance Fields, including name, data type, and whether they are mandatory.

* When a user selects a Template, StoryOS automatically displays a **pre-render form** to collect these values.

* The Deliverable cannot render until all required Instance Fields are complete and pass validation.

* These values are referenced in section bindings (e.g., “Lede” section may combine the Vision Statement with {who}, {what}, {when}, {where}, {why} fields).

* Instance Fields are stored within the Deliverable object, versioned with each revision, and included in the provenance record.

**Governance**

* Creators may edit Instance Fields until the Deliverable is approved.  
* Editing Instance Fields after approval creates a new Deliverable revision.  
* Templates may define default values or prefilled examples for common fields.

**Acceptance Criteria**

* Templates can declare Instance Fields in their schema.  
* UI automatically generates data entry forms for those fields.  
* Deliverables cannot render until all required Instance Fields are validated.  
* Instance data persists within the Deliverable and appears in provenance tracking.

### 

### Required system behaviors

* **Instantiation**: Create a new Deliverable using an approved Deliverable Template.

* **Content population:** Auto-fill sections with approved Element versions.

* **Override handling**: Permit limited, rule-based edits or substitutions.

* **Validation and approval**: Must pass all Deliverable Template and Brand Voice checks before publishing.

* **Rendering**: Apply Brand Voice filter and export to final formats.

* **Version locking**: When an Element or Template updates, Deliverables show ‘Update available’; owners can Refresh (pull latest \+ revalidate) or Defer.

* **Audit trail**: Maintain complete provenance of all source versions and user actions.

### Deliverable interaction with other components

| Component | Interaction |
| :---- | :---- |
| **UNF** | Provides content Elements for sections. |
| **Story Model** | Defines the order and intent of each section. |
| **Brand Voice** | Applies expression and tone rules during rendering. |
| **Deliverable Templates** | Supplies structure, bindings, and constraints. |
| **Governance System** | Validates compliance, manages approval, and tracks status. |

### 

### Acceptance criteria

* Deliverables can be created, edited, validated, rendered, and version-locked.  
* Each Deliverable contains a complete provenance record (Deliverable Template, Elements, Brand Voice).  
* Element or Deliverable Template updates trigger accurate impact notifications.  
* Re-rendering with new brand Voice or Element versions creates a new Deliverable revision.  
* Outputs remain reproducible from recorded versions.

