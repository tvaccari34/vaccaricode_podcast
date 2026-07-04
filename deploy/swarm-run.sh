#!/usr/bin/env bash
# swarm_run NAME -- <docker service create args...>
# Runs a one-off task on BoosterBot_Network to completion, prints logs, returns its exit code.
swarm_run() {
  local name="$1"; shift; [ "$1" = "--" ] && shift
  docker service rm "$name" >/dev/null 2>&1
  docker service create --name "$name" --network BoosterBot_Network \
    --restart-condition none --detach "$@" >/dev/null 2>&1 || { echo "create failed"; return 1; }
  # wait for the single task to reach a terminal state
  local st="" err="" tries=0
  while :; do
    st=$(docker service ps "$name" --no-trunc --format '{{.CurrentState}}' 2>/dev/null | head -1)
    case "$st" in
      Complete*) break ;;
      Failed*|Rejected*|Shutdown*) err=$(docker service ps "$name" --no-trunc --format '{{.Error}}' | head -1); break ;;
    esac
    tries=$((tries+1)); [ $tries -gt 450 ] && { echo "TIMEOUT waiting ($st)"; break; }
    sleep 2
  done
  echo "----- logs ($name) -----"
  docker service logs --raw "$name" 2>&1 | tail -40
  echo "----- state: ${st} ${err} -----"
  docker service rm "$name" >/dev/null 2>&1
  case "$st" in Complete*) return 0 ;; *) return 1 ;; esac
}
