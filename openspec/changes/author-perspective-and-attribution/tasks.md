## 1. Perspective and attribution rule

- [x] 1.1 Add `PERSPECTIVE_RULE` (formatted with `{author}`) to `prompts.py`, covering:
  - third-person credit for first-person source content;
  - the host's voice for opinion, analysis and takeaways only;
  - no invented personal experience;
  - aggregator and discussion sites are not the authors.
- [x] 1.2 Include `PERSPECTIVE_RULE` in `build_prompt` for every format, next to `GROUNDING_RULE`.
- [x] 1.3 Add a `PUBLISHED BY:` line (unique URL hosts, without `www.`, in order) to `source_block`.

## 2. Author profile

- [x] 2.1 Add `author_profile` (text) and `author_profile_file` (default
  `/app/config/author_profile.md`) settings to `config.py`.
- [x] 2.2 Add `author_profile()` to `generate.py`:
  - the file wins over the env text; returns "" when neither is set;
  - re-read on each call;
  - truncated to 6000 characters with a warning.
- [x] 2.3 Add an `AUTHOR_PROFILE_BLOCK` template to `prompts.py`, plus `system_instruction()`
  (brand voice + profile block); use it in `generate_for_topic`.
- [x] 2.4 Add `config/author_profile.example.md` (template with sections and guidance), and
  gitignore `config/author_profile.md`.
- [x] 2.5 Mount `config/` read-only at `/app/config`:
  - Swarm stack: `scheduler` and `dashboard`;
  - local compose: `pipeline`, `scheduler` and `dashboard`.

## 3. Tests and docs

- [x] 3.1 Tests:
  - the rule appears in every format's prompt, including with `BRAND_VOICE` overridden;
  - the publishers line is correct;
  - the profile is loaded from the file, then the env text, then empty;
  - file edits are picked up;
  - truncation;
  - `system_instruction()` with and without a profile.
- [x] 3.2 Document the author profile in the deploy docs (how to create it on the VPS; no
  redeploy needed for edits).
- [x] 3.3 Run the pipeline test suite and ruff; confirm no new findings.
