#!/usr/bin/env bash
set -euo pipefail

# Run from the trusted source checkout. The detached worktree supplies history.
state_ref=refs/heads/monitoring-state
state_dir="${RUNNER_TEMP:?}/roadie-monitoring-state"

case "${1:-}" in
  prepare)
    state_commit=HEAD
    if git ls-remote --exit-code origin "$state_ref" >/dev/null; then
      git fetch --depth=1 --no-tags origin "$state_ref"
      state_commit=FETCH_HEAD
    else
      status=$?
      if [ "$status" -ne 2 ]; then
        exit "$status"
      fi
    fi
    git worktree add --detach "$state_dir" "$state_commit"
    ;;
  publish)
    case "${2:-}" in
      gsc) monitor=gsc title=GSC ;;
      cwv) monitor=cwv title=CWV ;;
      *) echo "Expected gsc or cwv snapshot type" >&2; exit 2 ;;
    esac
    cd "$state_dir"
    git add -- "data/$monitor-snapshots"
    if ! git diff --cached --quiet; then
      git config user.name "github-actions[bot]"
      git config user.email "github-actions[bot]@users.noreply.github.com"
      git commit -m "chore: $title monitoring snapshot"
    fi
    git push origin "HEAD:$state_ref"
    ;;
  *) echo "Usage: $0 prepare | publish {gsc|cwv}" >&2; exit 2 ;;
esac
