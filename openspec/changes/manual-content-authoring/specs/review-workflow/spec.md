## ADDED Requirements

### Requirement: Dashboard content-creation actions
The review dashboard SHALL provide "Create Post" and "Create Episode" actions that let a reviewer
author content by hand, in Portuguese and/or English.

#### Scenario: Open the create forms
- **WHEN** a reviewer is on the dashboard
- **THEN** they can open a "Create Post" form and a "Create Episode" form and choose the target
  language(s)

#### Scenario: Validation on create
- **WHEN** a reviewer submits a create form without a title or body for any selected language
- **THEN** the system rejects the submission and prompts for the missing fields

### Requirement: Manual drafts enter the same review queue
Manually authored drafts SHALL appear in the same review queue as generated drafts and support the
same per-channel approve / reject / request-edit decisions, recording who decided and when.

#### Scenario: Review a manual draft
- **WHEN** a reviewer opens the queue after a manual post is saved as a draft
- **THEN** the manual blog (and newsletter) draft appears with the same approve/reject/edit
  controls as generated drafts

#### Scenario: Manual and automated content coexist in the queue
- **WHEN** both manually authored and AI-generated drafts are pending
- **THEN** both are listed and independently reviewable, with neither mode hiding or overriding the
  other
