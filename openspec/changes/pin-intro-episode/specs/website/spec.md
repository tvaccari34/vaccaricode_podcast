## ADDED Requirements

### Requirement: Pinned intro on landing pages
The site SHALL feature a configurable intro episode as a "start here" card pinned
above the normal content on the home page, the blog listing, and the podcast
listing, in both locales. The card SHALL link to that episode in the current
language and show its title. The featured episode SHALL NOT also appear in the
normal episode list on a page that shows one (it is not duplicated). If the
configured episode does not exist for the current language, no card SHALL be
rendered and the page SHALL otherwise be unaffected.

#### Scenario: Visitor lands on the home, blog, or podcast page
- **WHEN** a visitor opens the home, blog, or podcast listing
- **THEN** a "start here" card for the configured intro episode appears above the
  listing, linking to that episode in the page's language

#### Scenario: Featured episode is not listed twice
- **WHEN** a page renders both the featured card and an episode list
- **THEN** the featured episode is omitted from that list, appearing only as the
  pinned card

#### Scenario: Localized target
- **WHEN** the visitor is on the Portuguese site versus the English site
- **THEN** the card links to that episode's Portuguese (`/podcast/<id>`) or
  English (`/en/podcast/<id>`) page respectively, with a localized label

#### Scenario: Missing episode degrades gracefully
- **WHEN** the configured topic has no published episode in the current language
- **THEN** no card is rendered and the rest of the page renders normally
