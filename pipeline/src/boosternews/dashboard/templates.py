"""Jinja templates for the review dashboard, kept as strings so they ship inside the wheel."""

from __future__ import annotations

INDEX = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Review queue — boosternews</title>
  <style>
    :root { color-scheme: light dark; }
    body { font: 15px/1.6 system-ui, sans-serif; max-width: 60rem; margin: 1.5rem auto; padding: 0 1rem; }
    h1 { margin-bottom: .25rem; }
    .muted { color: #888; font-weight: 400; font-size: .85em; }
    .topic { border: 1px solid #8883; border-radius: 10px; padding: 1rem 1.25rem; margin: 1rem 0; }
    .lang { border: 1px solid #8883; border-radius: 8px; padding: .25rem 1rem 1rem; margin: 1rem 0; }
    .langhead { text-transform: none; margin: .5rem 0; }
    .channel { border-top: 1px solid #8882; padding: .75rem 0; }
    .channel:first-of-type { border-top: none; }
    h3 { margin: .25rem 0; text-transform: capitalize; }
    h4 { margin: .25rem 0; text-transform: capitalize; }
    input[type=file] { flex: 1; }
    pre { white-space: pre-wrap; background: #8881; padding: .75rem; border-radius: 8px; max-height: 22rem; overflow: auto; }
    audio { width: 100%; margin: .5rem 0; }
    form { display: flex; gap: .5rem; align-items: center; margin-top: .5rem; flex-wrap: wrap; }
    input[type=text] { flex: 1; min-width: 12rem; padding: .4rem .5rem; border: 1px solid #8884; border-radius: 6px; background: transparent; color: inherit; }
    button { border: none; border-radius: 6px; padding: .4rem .8rem; cursor: pointer; color: #fff; font-weight: 600; }
    .approve { background: #16a34a; } .edit { background: #d97706; } .reject { background: #dc2626; }
    textarea { width: 100%; box-sizing: border-box; font: 13px/1.5 ui-monospace, monospace; padding: .5rem; border: 1px solid #8884; border-radius: 6px; background: transparent; color: inherit; resize: vertical; }
    .renarrate { margin: .5rem 0; }
    .renarrate form { flex-direction: column; align-items: stretch; }
    .renarrate summary { cursor: pointer; color: #d97706; font-size: .85em; }
    .renarrate button { align-self: flex-start; }
    .badge { font-size: .72rem; padding: .1rem .5rem; border-radius: 999px; border: 1px solid #8884; vertical-align: middle; }
    .pending_review { color: #d97706; } .approved { color: #16a34a; } .rejected { color: #dc2626; }
    .needs_edit { color: #ca8a04; } .published { color: #2563eb; }
  </style>
</head>
<body>
  <h1>Review queue <span class="muted">({{ queue|length }} topic(s) pending) · reviewer: {{ reviewer }}</span></h1>
  <p class="muted">Approve, request edits, or reject each channel. Only approved drafts can be published.</p>
  <p><a class="createlink" href="/create/post">➕ Create Post</a> &nbsp; <a class="createlink" href="/create/episode">➕ Create Episode</a></p>

  {% if manual %}
  <section class="topic">
    <h2>🎙️ English audio — record &amp; upload</h2>
    <p class="muted">Download each script, record it in your own voice, and upload the MP3. Available any time, independent of the review queue.</p>
    {% for m in manual %}
    <div class="channel">
      <h4>{{ m.title }} <span class="badge">{{ m.language }}</span>
        {% if m.audio_url %}<span class="badge approved">audio uploaded{% if m.duration %} · {{ m.duration }}s{% endif %}</span>{% else %}<span class="badge pending_review">no audio yet</span>{% endif %}
      </h4>
      <p>
        <a href="/episode/{{ m.id }}/script">⬇ Baixar roteiro (download script)</a>
        {% if m.audio_url %} · <a href="{{ m.audio_url }}">▶ current audio</a>{% endif %}
      </p>
      <form method="post" action="/episode/{{ m.id }}/audio" enctype="multipart/form-data">
        <input type="file" name="audio" accept="audio/*" required />
        <button class="approve" type="submit">Enviar áudio</button>
      </form>
    </div>
    {% endfor %}
  </section>
  {% endif %}

  {% if episodes %}
  <section class="topic">
    <h2>🎙️ Episodes — edit script &amp; re-narrate</h2>
    <p class="muted">Auto-narrated {{ primary }} episodes. Edit the script and re-narrate — the home GPU worker regenerates the audio. Published episodes stay live and update in place.</p>
    {% for ep in episodes %}
    <div class="channel">
      <h4>{{ ep.title }} <span class="badge {{ ep.status }}">{{ ep.status }}</span>
        {% if ep.audio_url %}<span class="badge approved">audio{% if ep.duration %} · {{ ep.duration }}s{% endif %}</span>{% else %}<span class="badge pending_review">no audio yet</span>{% endif %}
      </h4>
      {% if ep.audio_url %}<audio controls preload="none" src="{{ ep.audio_url }}"></audio>{% endif %}
      <details class="renarrate">
        <summary>✏️ Edit script &amp; re-narrate</summary>
        <form method="post" action="/episode/{{ ep.id }}/renarrate">
          <textarea name="script" rows="14">{{ ep.script }}</textarea>
          <button class="edit" type="submit">Save &amp; re-narrate</button>
        </form>
      </details>
    </div>
    {% endfor %}
  </section>
  {% endif %}

  {% if not queue %}
    <p>Nothing to review right now. 🎉 Generate content with <code>generate</code>, then refresh.</p>
  {% endif %}

  {% for item in queue %}
  <section class="topic">
    <h2>{{ item.title }} <span class="muted">score {{ '%.3f'|format(item.score) }}</span></h2>
    {% set ordered = [primary] + (item.langs.keys() | reject('equalto', primary) | list | sort) %}
    {% for lang in ordered %}
      {% if lang in item.langs %}
      {% set L = item.langs[lang] %}
      {% set manual = lang != primary %}
      <div class="lang">
        <h3 class="langhead">🌐 {{ lang }}{% if manual %} <span class="muted">(manual audio)</span>{% endif %}</h3>
        {% for ch in ['blog', 'newsletter', 'podcast'] %}
          {% set d = L.drafts.get(ch) %}
          {% if d %}
          <div class="channel">
            <h4>{{ ch }} <span class="badge {{ d.status }}">{{ d.status }}</span></h4>
            {% if ch == 'podcast' %}
              {% if L.episode and L.episode.audio_url %}
                <audio controls preload="none" src="{{ L.episode.audio_url }}"></audio>
              {% elif manual and L.episode %}
                <p class="muted">No auto-narration for {{ lang }}. Download the script, record it, and upload the MP3:</p>
                <p>
                  <a href="/episode/{{ L.episode.id }}/script">⬇ Baixar roteiro</a>
                </p>
                <form method="post" action="/episode/{{ L.episode.id }}/audio" enctype="multipart/form-data">
                  <input type="file" name="audio" accept="audio/*" required />
                  <button class="approve" type="submit">Enviar áudio</button>
                </form>
              {% else %}
                <p class="muted">audio being produced by the sound-worker — edit the script &amp; re-narrate in the Episodes section above</p>
              {% endif %}
            {% endif %}
            <details><summary>view {{ ch }}</summary><pre>{{ d.body }}</pre></details>
            <form method="post" action="/review">
              <input type="hidden" name="topic_id" value="{{ item.topic_id }}" />
              <input type="hidden" name="channel" value="{{ ch }}" />
              <input type="hidden" name="language" value="{{ lang }}" />
              <input type="hidden" name="reviewer" value="{{ reviewer }}" />
              <input type="text" name="notes" placeholder="notes (optional)" />
              <button class="approve" name="decision" value="approve">Approve</button>
              <button class="edit" name="decision" value="request_edit">Request edit</button>
              <button class="reject" name="decision" value="reject">Reject</button>
            </form>
          </div>
          {% endif %}
        {% endfor %}
      </div>
      {% endif %}
    {% endfor %}
  </section>
  {% endfor %}
</body>
</html>
"""

_CREATE_STYLE = """
  <style>
    :root { color-scheme: light dark; }
    body { font: 15px/1.6 system-ui, sans-serif; max-width: 60rem; margin: 1.5rem auto; padding: 0 1rem; }
    .muted { color: #888; font-size: .9em; }
    fieldset { border: 1px solid #8884; border-radius: 10px; margin: 1rem 0; padding: .5rem 1rem 1rem; }
    legend { font-weight: 600; padding: 0 .4rem; }
    label { display: block; margin: .6rem 0 .2rem; font-weight: 600; font-size: .9em; }
    input[type=text], textarea { width: 100%; box-sizing: border-box; padding: .5rem; border: 1px solid #8884; border-radius: 6px; background: transparent; color: inherit; font: inherit; }
    textarea { font: 13px/1.5 ui-monospace, monospace; resize: vertical; }
    .actions { margin: 1rem 0; display: flex; gap: .5rem; flex-wrap: wrap; }
    button { border: none; border-radius: 6px; padding: .5rem 1rem; cursor: pointer; color: #fff; font-weight: 600; }
    .draft { background: #6b7280; } .approve { background: #16a34a; }
    a { color: inherit; }
  </style>
"""

CREATE_POST = (
    """
<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Create Post — boosternews</title>
"""
    + _CREATE_STYLE
    + """
</head><body>
  <p><a href="/">← back to review queue</a></p>
  <h1>Create Post</h1>
  <p class="muted">Write a blog post (and optional newsletter blurb) by hand. Fill either or both languages — empty languages are skipped. It enters the same review queue as generated content.</p>
  <form method="post" action="/create/post">
    {% for L in langs %}
    <fieldset>
      <legend>{{ L.label }}</legend>
      <label>Title</label>
      <input type="text" name="{{ L.prefix }}_title" />
      <label>Body (Markdown)</label>
      <textarea name="{{ L.prefix }}_body" rows="14"></textarea>
      <label>Newsletter blurb (optional)</label>
      <textarea name="{{ L.prefix }}_newsletter" rows="4"></textarea>
    </fieldset>
    {% endfor %}
    <div class="actions">
      <button class="draft" name="action" value="draft" type="submit">Save as draft</button>
      <button class="approve" name="action" value="approve" type="submit">Save &amp; approve</button>
    </div>
  </form>
</body></html>
"""
)

CREATE_EPISODE = (
    """
<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Create Episode — boosternews</title>
"""
    + _CREATE_STYLE
    + """
</head><body>
  <p><a href="/">← back to review queue</a></p>
  <h1>Create Episode</h1>
  <p class="muted">Write a podcast episode by hand. Fill either or both languages — empty languages are skipped.</p>
  <form method="post" action="/create/episode">
    {% for L in langs %}
    <fieldset>
      <legend>{{ L.label }}</legend>
      <label>Title</label>
      <input type="text" name="{{ L.prefix }}_title" />
      <label>Script</label>
      <textarea name="{{ L.prefix }}_script" rows="14"></textarea>
      <label>Show notes (optional)</label>
      <textarea name="{{ L.prefix }}_notes" rows="4"></textarea>
      {% if L.prefix == 'primary' %}
      <label style="font-weight:400"><input type="checkbox" name="primary_narrate" value="1" /> Queue {{ primary }} narration now (home GPU sound-worker)</label>
      {% else %}
      <p class="muted">No auto-narration for this language — after saving, upload the recorded MP3 from the review queue.</p>
      {% endif %}
    </fieldset>
    {% endfor %}
    <div class="actions">
      <button class="draft" name="action" value="draft" type="submit">Save as draft</button>
      <button class="approve" name="action" value="approve" type="submit">Save &amp; approve</button>
    </div>
  </form>
</body></html>
"""
)

TEMPLATES = {
    "index.html": INDEX,
    "create_post.html": CREATE_POST,
    "create_episode.html": CREATE_EPISODE,
}
