#!/usr/bin/env bash
set -euo pipefail

case "${1:-}" in
  community)
    paths=(':(glob)research-dumps/*-community.md')
    message="chore: refresh community research"
    ;;
  enrichment)
    paths=(':(glob)race-data/*.json' ':(glob)data/enrichment-snapshots/*-pre.json')
    message="chore: re-enrich race profiles"
    ;;
  *)
    echo "Expected community or enrichment." >&2
    exit 2
    ;;
esac

if ! git diff --cached --quiet; then
  echo "The workflow checkout has unexpected staged files." >&2
  exit 1
fi

for path in "${paths[@]}"; do
  changes=$(git status --porcelain --untracked-files=all -- "$path")
  if [[ -n "$changes" ]]; then
    git add -A -- "$path"
  fi
done

if git diff --cached --quiet; then
  printf '%s\n' "No editorial changes to review." >> "$GITHUB_STEP_SUMMARY"
  exit 0
fi

branch="review/roadie/$1-${GITHUB_RUN_ID:?}-${GITHUB_RUN_ATTEMPT:?}"
git -c user.name=github-actions[bot] -c user.email=github-actions[bot]@users.noreply.github.com commit -m "$message"
git push origin "HEAD:refs/heads/$branch"

printf 'Review the generated content in a [pull request](%s/%s/compare/main...%s?expand=1).\n' \
  "$GITHUB_SERVER_URL" "$GITHUB_REPOSITORY" "$branch" >> "$GITHUB_STEP_SUMMARY"
