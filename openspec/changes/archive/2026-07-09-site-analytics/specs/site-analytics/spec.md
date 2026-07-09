## ADDED Requirements

### Requirement: Privacy-friendly web analytics
The system SHALL collect website traffic analytics using a self-hosted, cookieless analytics service
that stores no personally identifying information, so no cookie-consent banner is required.

#### Scenario: Pageview is recorded
- **WHEN** a visitor loads a page of the public site
- **THEN** a pageview is recorded in the analytics dashboard, without setting cookies or storing PII

#### Scenario: No consent banner needed
- **WHEN** analytics is enabled
- **THEN** the site does not require a cookie-consent banner for it, because tracking is cookieless
  and anonymous

### Requirement: Analytics is configuration-gated
The tracker SHALL be emitted only when analytics is configured, so development/local builds and a
disabled state carry no tracker.

#### Scenario: Disabled by default in dev
- **WHEN** the analytics website id is not configured
- **THEN** the built pages contain no tracker script

#### Scenario: Kill switch
- **WHEN** the operator unsets the analytics website id and rebuilds
- **THEN** the tracker is removed from the live site

### Requirement: Content Security Policy permits the tracker
The CSP SHALL allow the analytics origin for script loading and data collection, and SHALL NOT
otherwise relax the policy.

#### Scenario: Tracker loads without CSP violation
- **WHEN** a page with analytics enabled is loaded
- **THEN** the tracker script loads and sends data with no CSP violation, while all other origins
  remain disallowed

### Requirement: Collection is public, dashboard is protected
The analytics collection endpoints (tracker script and event ingest) SHALL be publicly reachable,
while the analytics dashboard SHALL require authentication.

#### Scenario: Collection endpoints are open
- **WHEN** any client requests the tracker script or posts an event
- **THEN** the request is served without HTTP authentication

#### Scenario: Dashboard requires login
- **WHEN** a user opens the analytics dashboard
- **THEN** access requires a valid login

### Requirement: Traffic-source attribution via UTM convention
Links delivered through external channels (newsletter email, podcast show notes) that point back to
the site SHALL carry UTM parameters following a documented convention, so analytics attributes visits
to their source. On-site links SHALL NOT be UTM-tagged.

#### Scenario: Newsletter link is attributed
- **WHEN** a reader clicks a link in the weekly newsletter email
- **THEN** the visit is attributed in analytics to source `newsletter`, medium `email`, and the
  week's digest campaign

#### Scenario: Podcast show-notes link is attributed
- **WHEN** a listener follows the subscribe link in an episode's show notes
- **THEN** the visit is attributed to source `podcast`, medium `podcast`, and that episode's campaign

#### Scenario: On-site links are not tagged
- **WHEN** the site generates an internal subscribe CTA on a blog page
- **THEN** that link carries no UTM parameters, avoiding self-referral noise
