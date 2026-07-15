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
    .eptabs > input[type=radio] { position: absolute; opacity: 0; pointer-events: none; }
    .tabbar { display: flex; gap: .4rem; margin: 1.25rem 0 0; border-bottom: 1px solid #8884; }
    .tabbar label { cursor: pointer; padding: .5rem .9rem; border: 1px solid #8884; border-bottom: none;
                    border-radius: 8px 8px 0 0; background: #8881; font-weight: 600; font-size: .9em; margin-bottom: -1px; }
    #eptab-review:checked ~ .tabbar label[for=eptab-review],
    #eptab-pub:checked ~ .tabbar label[for=eptab-pub] { background: #2563eb; color: #fff; border-color: #2563eb; }
    .tabpanel { display: none; }
    #eptab-review:checked ~ #eppanel-review,
    #eptab-pub:checked ~ #eppanel-pub { display: block; }
    .tabpanel > section.topic { border-top-left-radius: 0; }
  </style>
</head>
<body>
  <h1>Review queue <span class="muted">({{ queue|length }} topic(s) pending) · reviewer: {{ reviewer }}</span></h1>
  <p class="muted">Approve, request edits, or reject each channel. Only approved drafts can be published.</p>
  <p><a class="createlink" href="/create/post">➕ Create Post</a> &nbsp; <a class="createlink" href="/create/episode">➕ Create Episode</a> &nbsp; <a class="createlink" href="/manage">🗂️ Manage content</a></p>

  {% macro render_audio(m) %}
    <div class="channel">
      <h4>{{ m.title }} <span class="badge">{{ m.language }}</span>
        <span class="badge {{ m.status }}">{{ m.status }}</span>
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
  {% endmacro %}
  {% macro render_episode(ep) %}
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
  {% endmacro %}

  {% set manual_review = manual|rejectattr('status', 'equalto', 'published')|list %}
  {% set manual_pub = manual|selectattr('status', 'equalto', 'published')|list %}
  {% set ep_review = episodes|rejectattr('status', 'equalto', 'published')|list %}
  {% set ep_pub = episodes|selectattr('status', 'equalto', 'published')|list %}
  {% if manual or episodes %}
  <div class="eptabs">
    <input type="radio" name="eptab" id="eptab-review" checked />
    <input type="radio" name="eptab" id="eptab-pub" />
    <div class="tabbar">
      <label for="eptab-review">⏳ Waiting review ({{ manual_review|length + ep_review|length }})</label>
      <label for="eptab-pub">✅ Published ({{ manual_pub|length + ep_pub|length }})</label>
    </div>

    <div class="tabpanel" id="eppanel-review">
      {% if manual_review %}
      <section class="topic">
        <h2>🎙️ English audio — record &amp; upload</h2>
        <p class="muted">Download each script, record it in your own voice, and upload the MP3. Available any time, independent of the review queue.</p>
        {% for m in manual_review %}{{ render_audio(m) }}{% endfor %}
      </section>
      {% endif %}
      {% if ep_review %}
      <section class="topic">
        <h2>🎙️ Episodes — edit script &amp; re-narrate</h2>
        <p class="muted">Auto-narrated {{ primary }} episodes awaiting review. Edit the script and re-narrate — the home GPU worker regenerates the audio.</p>
        {% for ep in ep_review %}{{ render_episode(ep) }}{% endfor %}
      </section>
      {% endif %}
      {% if not manual_review and not ep_review %}<p class="muted">No episodes waiting review. 🎉</p>{% endif %}
    </div>

    <div class="tabpanel" id="eppanel-pub">
      {% if manual_pub %}
      <section class="topic">
        <h2>🎙️ English audio — published</h2>
        <p class="muted">Already-published English episodes. Re-upload the MP3 to replace the live audio.</p>
        {% for m in manual_pub %}{{ render_audio(m) }}{% endfor %}
      </section>
      {% endif %}
      {% if ep_pub %}
      <section class="topic">
        <h2>🎙️ Episodes — published</h2>
        <p class="muted">Published {{ primary }} episodes stay live. Edit the script and re-narrate — the audio updates in place.</p>
        {% for ep in ep_pub %}{{ render_episode(ep) }}{% endfor %}
      </section>
      {% endif %}
      {% if not manual_pub and not ep_pub %}<p class="muted">No published episodes yet.</p>{% endif %}
    </div>
  </div>
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
    input[type=file] { display: block; margin: .35rem 0; max-width: 100%; }
    .hint { color: #888; font-size: .8em; margin: .2rem 0 0; }
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
  <form method="post" action="/create/episode" enctype="multipart/form-data">
    {% for L in langs %}
    <fieldset>
      <legend>{{ L.label }}</legend>
      <label>Title</label>
      <input type="text" name="{{ L.prefix }}_title" />
      <label>Script</label>
      <textarea name="{{ L.prefix }}_script" rows="14"></textarea>
      <label>Show notes (optional)</label>
      <textarea name="{{ L.prefix }}_notes" rows="4"></textarea>
      <label for="{{ L.prefix }}_audio">Upload audio (MP3, optional)</label>
      <input id="{{ L.prefix }}_audio" type="file" name="{{ L.prefix }}_audio" accept="audio/*" />
      <p class="hint">The file uploads when you click <strong>Save</strong> below — there's no separate upload button. Leave empty to add audio later from Manage.</p>
      {% if L.prefix == 'primary' %}
      <label style="font-weight:400"><input type="checkbox" name="primary_narrate" value="1" /> …or queue {{ primary }} narration now (home GPU sound-worker) — ignored if you upload a file above</label>
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

MANAGE = """
<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Manage content — boosternews</title>
<style>
  :root { color-scheme: light dark; }
  body { font: 14px/1.5 system-ui, sans-serif; max-width: 70rem; margin: 1.5rem auto; padding: 0 1rem; }
  .muted { color: #888; font-size: .9em; }
  h2 { margin-top: 1.5rem; }
  table { border-collapse: collapse; width: 100%; }
  th, td { text-align: left; padding: .45rem .5rem; border-bottom: 1px solid #8883; vertical-align: middle; }
  th { font-size: .8em; text-transform: uppercase; color: #888; }
  .badge { font-size: .72rem; padding: .1rem .5rem; border-radius: 999px; border: 1px solid #8884; }
  .published { color: #2563eb; } .approved { color: #16a34a; } .pending_review { color: #d97706; }
  .ready { color: #16a34a; } .script_ready { color: #d97706; } .needs_edit { color: #ca8a04; } .rejected { color: #dc2626; }
  .actions { display: flex; gap: .4rem; align-items: center; flex-wrap: wrap; }
  .actions form { display: inline; margin: 0; }
  .actions input[type=file] { width: 9rem; }
  a { color: inherit; }
  button { border: none; border-radius: 6px; padding: .3rem .6rem; cursor: pointer; color: #fff; font-weight: 600; font-size: .82em; }
  .go { background: #16a34a; } .warn { background: #d97706; } .danger { background: #dc2626; } .rebuild { background: #2563eb; padding: .45rem .9rem; }
  h3.grp { margin: 1rem 0 .3rem; font-size: .92rem; color: #777; }
  .filterbar { display: flex; gap: .75rem; align-items: center; flex-wrap: wrap; margin: .6rem 0 1.2rem; }
  .langtoggle { display: inline-flex; gap: .25rem; }
  .langtoggle button { background: #8882; color: inherit; border: 1px solid #8884; }
  .langtoggle button.active { background: #2563eb; color: #fff; }
  #titlefilter { padding: .38rem .6rem; border: 1px solid #8886; border-radius: 6px; background: transparent; color: inherit; min-width: 15rem; }
  details.pubwrap { margin: .2rem 0 1rem; }
  details.pubwrap > summary { cursor: pointer; padding: .45rem 0; font-weight: 600; color: #2563eb; }
</style></head><body>
  <p><a href="/">← back to review queue</a></p>
  <h1>Manage content</h1>
  <form method="post" action="/manage/rebuild"><button class="rebuild">🔄 Rebuild site now</button></form>
  <p class="muted">Publish, unpublish, edit, replace audio, or delete. Changes appear on the live site within ~1 minute (a rebuild is queued automatically). Deleting is permanent.</p>

  <div class="filterbar">
    <div class="langtoggle" id="langtoggle">
      <button type="button" data-lang="all" class="active">All</button>
      <button type="button" data-lang="pt-BR">PT</button>
      <button type="button" data-lang="en">EN</button>
    </div>
    <input type="search" id="titlefilter" placeholder="🔍 filter by title…" autocomplete="off" />
  </div>

  {% macro post_row(p) %}
  <tr data-lang="{{ p.language }}" data-title="{{ (p.title or '')|lower }}">
    <td>{{ p.language }}</td>
    <td>{{ p.title or '(untitled)' }} {% if p.origin == 'manual' %}<span class="badge">manual</span>{% endif %}</td>
    <td><span class="badge {{ p.status }}">{{ p.status }}</span></td>
    <td class="actions">
      <a href="/manage/post/{{ p.id }}/edit">edit</a>
      {% if p.status == 'published' %}
      <form method="post" action="/manage/post/{{ p.id }}/unpublish" onsubmit="return confirm('Unpublish this post?')"><button class="warn">unpublish</button></form>
      {% else %}
      <form method="post" action="/manage/post/{{ p.id }}/publish"><button class="go">publish</button></form>
      {% endif %}
      <form method="post" action="/manage/post/{{ p.id }}/delete" onsubmit="return confirm('Delete this post permanently?')"><button class="danger">delete</button></form>
    </td>
  </tr>
  {% endmacro %}
  {% macro episode_row(e) %}
  <tr data-lang="{{ e.language }}" data-title="{{ (e.title or '')|lower }}">
    <td>{{ e.language }}</td>
    <td>{{ e.title }} {% if e.origin == 'manual' %}<span class="badge">manual</span>{% endif %}</td>
    <td><span class="badge {{ e.status }}">{{ e.status }}</span></td>
    <td>{% if e.audio_url %}<a href="{{ e.audio_url }}">▶{% if e.duration %} {{ e.duration }}s{% endif %}</a>{% else %}—{% endif %}</td>
    <td class="actions">
      {% if e.status == 'published' %}
      <form method="post" action="/manage/episode/{{ e.id }}/unpublish" onsubmit="return confirm('Unpublish this episode?')"><button class="warn">unpublish</button></form>
      {% else %}
      <form method="post" action="/manage/episode/{{ e.id }}/publish"><button class="go">publish</button></form>
      {% endif %}
      <form method="post" action="/episode/{{ e.id }}/audio" enctype="multipart/form-data"><input type="file" name="audio" accept="audio/*" required /><button class="go">upload audio</button></form>
      <form method="post" action="/manage/episode/{{ e.id }}/delete" onsubmit="return confirm('Delete this episode and its audio permanently?')"><button class="danger">delete</button></form>
    </td>
  </tr>
  {% endmacro %}

  {% set act_posts = posts|rejectattr('status', 'equalto', 'published')|list %}
  {% set pub_posts = posts|selectattr('status', 'equalto', 'published')|list %}
  <h2>Posts <span class="muted">({{ posts|length }})</span></h2>
  <h3 class="grp">Needs action <span class="muted">({{ act_posts|length }})</span></h3>
  <table class="mtable">
    <tr><th>Lang</th><th>Title</th><th>Status</th><th>Actions</th></tr>
    {% for p in act_posts %}{{ post_row(p) }}{% endfor %}
    {% if not act_posts %}<tr class="noitems"><td colspan="4" class="muted">Nothing awaiting action.</td></tr>{% endif %}
  </table>
  <details class="pubwrap">
    <summary>Published <span class="muted">({{ pub_posts|length }})</span></summary>
    <table class="mtable">
      <tr><th>Lang</th><th>Title</th><th>Status</th><th>Actions</th></tr>
      {% for p in pub_posts %}{{ post_row(p) }}{% endfor %}
      {% if not pub_posts %}<tr class="noitems"><td colspan="4" class="muted">No published posts.</td></tr>{% endif %}
    </table>
  </details>

  {% set act_eps = episodes|rejectattr('status', 'equalto', 'published')|list %}
  {% set pub_eps = episodes|selectattr('status', 'equalto', 'published')|list %}
  <h2>Episodes <span class="muted">({{ episodes|length }})</span></h2>
  <h3 class="grp">Needs action <span class="muted">({{ act_eps|length }})</span></h3>
  <table class="mtable">
    <tr><th>Lang</th><th>Title</th><th>Status</th><th>Audio</th><th>Actions</th></tr>
    {% for e in act_eps %}{{ episode_row(e) }}{% endfor %}
    {% if not act_eps %}<tr class="noitems"><td colspan="5" class="muted">Nothing awaiting action.</td></tr>{% endif %}
  </table>
  <details class="pubwrap">
    <summary>Published <span class="muted">({{ pub_eps|length }})</span></summary>
    <table class="mtable">
      <tr><th>Lang</th><th>Title</th><th>Status</th><th>Audio</th><th>Actions</th></tr>
      {% for e in pub_eps %}{{ episode_row(e) }}{% endfor %}
      {% if not pub_eps %}<tr class="noitems"><td colspan="5" class="muted">No published episodes.</td></tr>{% endif %}
    </table>
  </details>
  <p class="muted">To edit an episode's script or re-narrate the {{ primary }} audio, use the “Episodes — edit script &amp; re-narrate” section on the <a href="/">review queue page</a>.</p>

  <script>
  (function () {
    var lang = "all", q = "";
    var toggle = document.getElementById("langtoggle");
    var search = document.getElementById("titlefilter");
    function apply() {
      document.querySelectorAll("tr[data-lang]").forEach(function (tr) {
        var okL = lang === "all" || tr.getAttribute("data-lang") === lang;
        var okQ = !q || (tr.getAttribute("data-title") || "").indexOf(q) !== -1;
        tr.style.display = (okL && okQ) ? "" : "none";
      });
      if (q) document.querySelectorAll("details.pubwrap").forEach(function (d) { d.open = true; });
    }
    toggle.addEventListener("click", function (ev) {
      var b = ev.target.closest("button[data-lang]"); if (!b) return;
      lang = b.getAttribute("data-lang");
      toggle.querySelectorAll("button").forEach(function (x) { x.classList.toggle("active", x === b); });
      apply();
    });
    search.addEventListener("input", function () { q = search.value.trim().toLowerCase(); apply(); });
  })();
  </script>
</body></html>
"""

EDIT_POST = (
    """
<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Edit post — boosternews</title>
"""
    + _CREATE_STYLE
    + """
</head><body>
  <p><a href="/manage">← back to manage</a></p>
  <h1>Edit post</h1>
  <p class="muted">{{ d.language }} · {{ d.channel }} · status: {{ d.status }}</p>
  <form method="post" action="/manage/post/{{ d.id }}/edit">
    <label>Title</label>
    <input type="text" name="title" value="{{ d.title or '' }}" />
    <label>Body (Markdown)</label>
    <textarea name="body" rows="20">{{ d.body }}</textarea>
    <div class="actions">
      <button class="approve" type="submit">Save</button>
      <a href="/manage" style="align-self:center">cancel</a>
    </div>
  </form>
</body></html>
"""
)

TEMPLATES = {
    "index.html": INDEX,
    "create_post.html": CREATE_POST,
    "create_episode.html": CREATE_EPISODE,
    "manage.html": MANAGE,
    "edit_post.html": EDIT_POST,
}
