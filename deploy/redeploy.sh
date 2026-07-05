#!/usr/bin/env bash
# Redeploy boosternews after code is merged to main. One command that:
#   1. pulls latest main
#   2. rebuilds the pipeline image
#   3. applies any new DB migrations (aborts if they fail)
#   4. redeploys the Swarm stack (stack + env changes) and forces the pipeline services onto the
#      freshly-built local image
#   5. rebuilds the static site
# Safe to run repeatedly. Run from anywhere: bash /root/vaccaricode_podcast/deploy/redeploy.sh
set -uo pipefail
REPO=/root/vaccaricode_podcast
IMG=boosternews/pipeline:local
PIPELINE_SVCS="scheduler narration-api dashboard"
cd "$REPO"
source deploy/swarm-run.sh   # NOTE: keep this script free of `set -e` (swarm_run relies on it)

echo "==> [1/5] git pull --ff-only origin main"
git pull --ff-only origin main || { echo "    pull failed (uncommitted changes / diverged) — aborting"; exit 1; }
echo "    at $(git rev-parse --short HEAD)"

echo "==> [2/5] rebuild image $IMG"
docker build -f pipeline/Dockerfile -t "$IMG" . >/tmp/redeploy-build.log 2>&1 \
  || { echo "    image build FAILED — see /tmp/redeploy-build.log"; tail -5 /tmp/redeploy-build.log; exit 1; }
echo "    built"

echo "==> [3/5] apply migrations"
swarm_run bn-migrate -- --env-file "$REPO/.env" "$IMG" python -m boosternews.migrate \
  || { echo "    migrations FAILED — aborting before redeploy"; exit 1; }

echo "==> [4/5] redeploy stack + pipeline services"
set -a; . "$REPO/.env"; set +a
docker stack deploy -c deploy/stack.boosternews.yml boosternews >/dev/null 2>&1
for s in $PIPELINE_SVCS; do docker service update --force --image "$IMG" "boosternews_$s" >/dev/null 2>&1 & done
wait
for i in $(seq 1 40); do
  ok=1
  for s in $PIPELINE_SVCS; do
    st=$(docker service inspect "boosternews_$s" --format '{{.UpdateStatus.State}}' 2>/dev/null)
    case "$st" in completed|""|"<no value>") ;; *) ok=0 ;; esac
  done
  [ "$ok" = 1 ] && break
  sleep 3
done
echo "    services converged"

echo "==> [5/5] rebuild static site"
bash deploy/publish-rebuild.sh rebuild >/tmp/redeploy-site.log 2>&1 \
  && echo "    site rebuilt" || { echo "    site rebuild FAILED — see /tmp/redeploy-site.log"; tail -8 /tmp/redeploy-site.log; }

echo "==> services now:"
docker stack services boosternews --format '  {{.Name}}  {{.Replicas}}  {{.Image}}'
echo "==> done. Live: https://tiagovaccari.com  ·  dashboard: https://dashboard.tiagovaccari.com"
