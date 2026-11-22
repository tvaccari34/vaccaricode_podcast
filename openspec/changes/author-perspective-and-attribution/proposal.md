## Why

Generated blog posts and podcast scripts are written as a single host (Tiago) speaking, but the
prompts never say whose words the source material holds. When an article is written in the first
person ("we migrated our stack and cut costs 40%"), the model keeps the "I/we", and the episode
sounds like Tiago claiming someone else's experience. The content should report what the source
author said or experienced, credited to them, with Tiago adding his own opinions and takeaways
on top. Where Tiago really has relevant experience, it should come from facts he provided, not
from the model's invention.

## What Changes

- Add a **perspective and attribution rule** to every blog, podcast and newsletter generation
  prompt:
  - First-person experiences, results, quotes and decisions in the source are reported in the
    third person and credited to the source's author or publisher.
  - The host's own voice is used only for analysis, opinion and takeaways.
  - The host never claims to have done, built or lived something unless it appears in the
    author profile.
  - The rule is part of the per-format prompt, so it still applies when `BRAND_VOICE` overrides
    the default voice.
- Pass the **publisher** of each source (derived from the source URL domains) into the SOURCE
  MATERIAL block, so the model has a name to credit.
- Add an optional **author profile**: Tiago's real background, positions and true anecdotes.
  - It is read from a file (`AUTHOR_PROFILE_FILE`, default `/app/config/author_profile.md`) or
    from the `AUTHOR_PROFILE` env text.
  - It is added to the generation system instruction as the only allowed source of the host's
    personal experiences and recurring opinions.
  - The file is read on every generation, so edits take effect without a redeploy.
  - Without a profile, the host gives opinions as analysis but never invents personal anecdotes.
- Ship `config/author_profile.example.md` as a template. The real `config/author_profile.md` is
  gitignored, and `config/` is mounted read-only into the generating services (Swarm stack and
  local compose).

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `content-generation`: generation adds rules for attributing first-person source content and
  for the host's perspective, makes source publishers available for attribution, and can draw
  on a configured author profile for the host's own experiences and opinions.

## Impact

- `pipeline/src/boosternews/prompts.py`: new `PERSPECTIVE_RULE` and author-profile block text.
- `pipeline/src/boosternews/generate.py`:
  - `source_block` adds a publishers line.
  - `build_prompt` includes the perspective rule.
  - A new `system_instruction()` combines the brand voice and the author profile.
  - A new `author_profile()` loader.
- `pipeline/src/boosternews/config.py`: new `author_profile` and `author_profile_file` settings.
- `deploy/stack.boosternews.yml`, `deploy/docker-compose.yml`: mount `config/` read-only into the
  services that generate (scheduler, dashboard, pipeline).
- `config/author_profile.example.md` (new), `.gitignore` (ignore `config/author_profile.md`).
- Tests in `pipeline/tests/test_generate.py`.
- Existing drafts are unchanged; only new generations are affected. The secondary-language
  (English) versions follow automatically, since they are translations of the primary output.
