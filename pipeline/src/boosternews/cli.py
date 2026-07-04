"""Command-line interface for the boosternews pipeline.

Subcommands:
  check          validate config + check Postgres/storage connectivity
  seed-sources   insert the default trend sources (idempotent)
  ingest         run one trend-discovery pass (fetch → score → dedup/merge)
  extract        backfill article text for topics that lack it
  list-topics    show the top candidate topics by score
"""

from __future__ import annotations

import argparse
import logging
import sys

from .config import get_settings, mask


def cmd_check(_args) -> int:
    try:
        s = get_settings()
    except Exception as exc:  # noqa: BLE001
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    print("boosternews configuration loaded OK")
    print(f"  database_url       : {mask(s.database_url, keep=18)}")
    print(f"  gemini_api_key     : {mask(s.gemini_api_key)}")
    print(f"  gemini_model       : {s.gemini_model}")
    print(f"  s3_endpoint_url    : {s.s3_endpoint_url}")
    print(f"  s3_bucket_audio    : {s.s3_bucket_audio}")
    print(f"  worker_auth_token  : {mask(s.worker_auth_token)}")

    try:
        from .db import ping

        print(f"  postgres           : {'reachable' if ping() else 'NOT reachable'}")
    except Exception as exc:  # noqa: BLE001
        print(f"  postgres           : check skipped ({exc})")

    try:
        from .storage import ensure_bucket

        print(f"  object storage     : bucket '{ensure_bucket()}' ready")
    except Exception as exc:  # noqa: BLE001
        print(f"  object storage     : check skipped ({exc})")
    return 0


def cmd_seed_sources(_args) -> int:
    from .seed import seed_default_sources

    n = seed_default_sources()
    print(f"Seeded {n} new source(s).")
    return 0


def cmd_ingest(args) -> int:
    from .ingest import run_ingest

    results = run_ingest(only_due=not args.all, source_name=args.source, extract=args.extract)
    if not results:
        print("No sources due. Use --all to force, or run 'seed-sources' first.")
        return 0
    total_new = sum(r.created for r in results)
    total_merged = sum(r.merged for r in results)
    for r in results:
        if r.status == "ok":
            print(f"  [ok]    {r.name}: {r.created} new, {r.merged} merged")
        else:
            print(f"  [error] {r.name}: {r.detail}")
    print(f"Done — {total_new} new, {total_merged} merged across {len(results)} source(s).")
    return 0


def cmd_extract(args) -> int:
    from .ingest import run_extraction

    n = run_extraction(limit=args.limit)
    print(f"Extracted text for {n} topic(s).")
    return 0


def cmd_generate(args) -> int:
    from .generate import generate_for_topic, generate_top

    result = generate_for_topic(args.topic) if args.topic else generate_top()
    if not result:
        print("No eligible topic. Run 'ingest --all' then 'extract', or pass --topic <id>.")
        return 0
    print(f"Generated drafts for topic {result['topic_id']}: {result['title']}")
    print(
        f"  languages : {', '.join(result['languages'])} (primary auto-narrated; others manual audio)"
    )
    print(f"  episode   : {result['episode_id']}")
    for fmt, preview in result["previews"].items():
        print(f"\n--- {fmt} preview (primary) ---\n{preview}")
    return 0


def cmd_list_drafts(args) -> int:
    from .repository import list_drafts

    rows = list_drafts(limit=args.limit, channel=args.channel)
    if not rows:
        print("No drafts yet. Run 'generate --top'.")
        return 0
    print(f"{'channel':>10}  {'status':>14}  {'chars':>6}  title")
    for r in rows:
        print(f"{r['channel']:>10}  {r['status']:>14}  {r['chars']:>6}  {(r['title'] or '')[:60]}")
    return 0


def cmd_show_draft(args) -> int:
    from .repository import get_draft_body

    body = get_draft_body(args.topic, args.channel)
    if body is None:
        print(f"No {args.channel} draft for topic {args.topic}.")
        return 1
    print(body)
    return 0


def cmd_publish(args) -> int:
    from .publish import publish_all, publish_topic

    if args.topic:
        summary = publish_topic(args.topic)
        print(f"Published topic {args.topic}:")
        for ch, st in summary.items():
            print(f"  {ch}: {st}")
    else:
        results = publish_all()
        if not results:
            print("Nothing approved to publish. Approve drafts in the dashboard first.")
            return 0
        for tid, summary in results.items():
            print(f"Topic {tid}: " + ", ".join(f"{ch}={st}" for ch, st in summary.items()))
    print("\nNext: rebuild the site so it renders the published content → `make web-build`.")
    print("(The scheduler in task group 9 runs this automatically after publishing.)")
    return 0


def cmd_list_publications(args) -> int:
    from .repository import list_publications

    rows = list_publications(limit=args.limit)
    if not rows:
        print("Nothing published yet.")
        return 0
    print(f"{'channel':>10}  {'when':>19}  url / campaign")
    for r in rows:
        when = r["published_at"].strftime("%Y-%m-%d %H:%M:%S") if r["published_at"] else ""
        target = r["url"] or (f"campaign #{r['external_id']}" if r["external_id"] else "")
        print(f"{r['channel']:>10}  {when:>19}  {target}")
    return 0


def cmd_enqueue_narration(args) -> int:
    from .db import get_conn
    from .repository import enqueue_narration, episodes_needing_narration

    pending = episodes_needing_narration()
    if not pending:
        print("No episodes need narration.")
        return 0
    n = 0
    with get_conn() as conn:
        for episode_id, voice_id, script in pending:
            if enqueue_narration(conn, episode_id, voice_id or "tiago", script):
                n += 1
        conn.commit()
    print(f"Queued narration for {n} episode(s).")
    return 0


def cmd_narration_status(args) -> int:
    from .repository import list_narration_jobs

    rows = list_narration_jobs(limit=args.limit)
    if not rows:
        print("No narration jobs. Generate content, then `enqueue-narration`.")
        return 0
    print(f"{'status':>10}  {'try':>5}  title")
    for r in rows:
        print(
            f"{r['status']:>10}  {r['attempts']}/{r['max_attempts']:>2}  {(r['title'] or '')[:60]}"
        )
    return 0


def cmd_digest(args) -> int:
    from .digest import run_digest

    summary = run_digest()
    print("Weekly newsletter digest:")
    for lang, msg in summary.items():
        print(f"  {lang}: {msg}")
    return 0


def cmd_list_topics(args) -> int:
    from .repository import list_topics

    rows = list_topics(limit=args.limit, status=args.status)
    if not rows:
        print("No topics yet. Run 'seed-sources' then 'ingest --all'.")
        return 0
    print(f"{'score':>7}  {'src':>3}  {'txt':>3}  title")
    for r in rows:
        txt = "yes" if r["has_text"] else "-"
        title = (r["title"] or "")[:80]
        print(f"{r['score']:>7.3f}  {r['sources']:>3}  {txt:>3}  {title}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="boosternews", description="boosternews content pipeline")
    sub = p.add_subparsers(dest="command")

    sub.add_parser("check", help="validate config + connectivity").set_defaults(func=cmd_check)
    sub.add_parser("seed-sources", help="insert default trend sources").set_defaults(
        func=cmd_seed_sources
    )

    pi = sub.add_parser("ingest", help="run one trend-discovery pass")
    pi.add_argument("--all", action="store_true", help="ignore fetch intervals; fetch every source")
    pi.add_argument("--source", help="only this source (by name)")
    pi.add_argument(
        "--extract",
        action="store_true",
        help="also extract article text for new topics",
    )
    pi.set_defaults(func=cmd_ingest)

    pe = sub.add_parser("extract", help="backfill article text for topics missing it")
    pe.add_argument("--limit", type=int, default=25)
    pe.set_defaults(func=cmd_extract)

    pl = sub.add_parser("list-topics", help="show top candidate topics")
    pl.add_argument("--limit", type=int, default=20)
    pl.add_argument("--status", help="filter by status (e.g. new)")
    pl.set_defaults(func=cmd_list_topics)

    pg = sub.add_parser("generate", help="generate blog + script + newsletter for a topic")
    pg.add_argument("--topic", help="topic id (default: highest-scoring new topic with text)")
    pg.set_defaults(func=cmd_generate)

    pd = sub.add_parser("list-drafts", help="show generated drafts")
    pd.add_argument("--limit", type=int, default=20)
    pd.add_argument("--channel", help="filter by channel (blog|podcast|newsletter)")
    pd.set_defaults(func=cmd_list_drafts)

    ps = sub.add_parser("show-draft", help="print a draft body")
    ps.add_argument("topic", help="topic id")
    ps.add_argument("channel", choices=["blog", "podcast", "newsletter"])
    ps.set_defaults(func=cmd_show_draft)

    pp = sub.add_parser("publish", help="publish approved drafts (gate-enforced)")
    pp.add_argument("--topic", help="topic id (default: all topics with approved drafts)")
    pp.add_argument(
        "--all",
        action="store_true",
        help="publish all approved (explicit; the default)",
    )
    pp.set_defaults(func=cmd_publish)

    pl2 = sub.add_parser("list-publications", help="show what has been published")
    pl2.add_argument("--limit", type=int, default=20)
    pl2.set_defaults(func=cmd_list_publications)

    sub.add_parser(
        "enqueue-narration", help="queue narration for episodes lacking audio"
    ).set_defaults(func=cmd_enqueue_narration)

    pn = sub.add_parser("narration-status", help="show the narration job queue")
    pn.add_argument("--limit", type=int, default=20)
    pn.set_defaults(func=cmd_narration_status)

    sub.add_parser(
        "digest", help="create the weekly newsletter digest campaign(s)"
    ).set_defaults(func=cmd_digest)

    return p


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)
    func = getattr(args, "func", cmd_check)  # default to the health check
    return func(args)
