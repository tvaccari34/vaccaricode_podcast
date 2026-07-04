## MODIFIED Requirements

### Requirement: Publishing does not email subscribers per post
Publishing an individual post SHALL NOT create or send a newsletter campaign. Publishing SHALL
still release the post's blog/podcast/newsletter content and record its publications; the weekly
digest is the only thing that creates newsletter campaigns.

#### Scenario: Publishing a single post
- **WHEN** a post is published (manually or by the pipeline)
- **THEN** its content goes live and its publications are recorded, but no Listmonk campaign is
  created for that post

#### Scenario: The newsletter blurb remains available to the digest
- **WHEN** a post with an approved newsletter blurb is published
- **THEN** the blurb is stored and later included as that post's section in the weekly digest
