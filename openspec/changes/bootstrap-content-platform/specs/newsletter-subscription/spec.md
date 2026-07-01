## ADDED Requirements

### Requirement: Double opt-in subscription
The system SHALL manage newsletter subscribers with a double opt-in flow: a new subscriber
must confirm via an emailed link before being considered active.

#### Scenario: New subscriber confirms
- **WHEN** a visitor submits their email and then clicks the confirmation link they receive
- **THEN** they become an active subscriber eligible to receive editions

#### Scenario: Unconfirmed subscriber
- **WHEN** a visitor submits their email but never clicks the confirmation link
- **THEN** they remain unconfirmed and do not receive newsletter editions

### Requirement: Unsubscribe and data rights
The system SHALL let subscribers unsubscribe at any time and SHALL handle subscriber data in
an LGPD/GDPR-compliant manner, including removal on request.

#### Scenario: Subscriber unsubscribes
- **WHEN** a subscriber clicks unsubscribe in an email
- **THEN** they are removed from the active list and receive no further editions

#### Scenario: Data deletion request
- **WHEN** a subscriber requests deletion of their data
- **THEN** their personal data is removed from the subscriber store

### Requirement: Campaign delivery and analytics
The system SHALL send newsletter editions as campaigns to the active list through a
transactional sending provider and SHALL record basic delivery analytics.

#### Scenario: Edition delivered with tracking
- **WHEN** an approved edition is sent
- **THEN** it is delivered to active subscribers and delivery/open metrics are recorded for
  the campaign

### Requirement: Pluggable sending provider
The system SHALL support more than one configured transactional sending provider (e.g. Amazon
SES and Resend) and SHALL allow switching the active provider by configuration without code
changes.

#### Scenario: Switch sending provider
- **WHEN** the operator selects a different configured sending provider
- **THEN** subsequent newsletter editions are delivered through the newly selected provider,
  with no change to source code

#### Scenario: Active provider is misconfigured
- **WHEN** the active sending provider's credentials are missing or invalid
- **THEN** sending fails with a clear error and the operator can switch to another configured
  provider
