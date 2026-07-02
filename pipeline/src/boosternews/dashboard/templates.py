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
                <p class="muted">audio being produced by the sound-worker — review the script below</p>
              {% endif %}
              {% if not manual and L.episode %}
                <details class="renarrate">
                  <summary>✏️ Edit script &amp; re-narrate (regenerates the pt-BR audio)</summary>
                  <form method="post" action="/episode/{{ L.episode.id }}/renarrate">
                    <textarea name="script" rows="14">{{ L.episode.script }}</textarea>
                    <button class="edit" type="submit">Save &amp; re-narrate</button>
                  </form>
                </details>
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

TEMPLATES = {"index.html": INDEX}
