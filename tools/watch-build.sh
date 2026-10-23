#!/usr/bin/env bash
# Watch in-flight COPR builds until they finish.
# Exit 0 only if every watched build succeeded; 1 if any failed.
#
# usage: watch-build.sh <owner/project> [package] [interval_seconds]
# The watched set is fixed on the first poll (builds submitted later are not
# added), so "green then push then watch" gives a clean signal per iteration.

set -uo pipefail

project="${1:?usage: watch-build.sh <owner/project> [package] [interval]}"
pkg="${2:-}"
interval="${3:-90}"

ownername="${project%%/*}"
projectname="${project#*/}"
api="https://copr.fedorainfracloud.org/api_3/build/list?ownername=${ownername}&projectname=${projectname}"

states() {
  curl -fsSL "$api" | python3 -c "
import json, sys
pkg = '''$pkg'''
watched = set()
items = json.load(sys.stdin).get('items', [])
inflight = []
for b in items:
    name = (b.get('source_package') or {}).get('name', '')
    state = b['state']
    if pkg and name != pkg:
        continue
    if state in ('pending', 'starting', 'running'):
        inflight.append((b['id'], name, state))
        watched.add(b['id'])
print('\n'.join(f'{i} {n} {s}' for i, n, s in inflight))
print('IDS ' + ' '.join(str(i) for i in watched))
"
}

watched=""
while true; do
  out="$(states)" || { echo "watch: API error, retrying in ${interval}s" >&2; sleep "$interval"; continue; }
  inflight="$(grep -v '^IDS ' <<<"$out" || true)"
  ids="$(grep '^IDS ' <<<"$out" | cut -d' ' -f2- || true)"

  if [ -z "$watched" ]; then
  # first poll: lock the watched set
    watched="$ids"
    if [ -z "$watched" ]; then
      echo "no builds in flight${pkg:+ for $pkg}"
      exit 0
    fi
  fi

  echo "$(date '+%H:%M:%S')"
  for id in $watched; do
    # 2>/dev/null: a build deleted mid-watch makes the API 404 and python
    # would spam a JSONDecodeError traceback before the || fallback runs
    curl -fsSL "https://copr.fedorainfracloud.org/api_3/build/$id" \
      | python3 -c "import json,sys; d=json.load(sys.stdin); sp=d.get('source_package') or {}; print(f\"  {d['id']} {(sp.get('name') or '?'):24} {d['state']}\")" 2>/dev/null \
      || echo "  $id ? (deleted mid-watch or API error)"
  done

  # done when none of the watched ids is pending/starting/running anymore
  busy="$(grep -v '^IDS ' <<<"$out" | awk -v ids="$watched" 'BEGIN{split(ids,a," ")} {for(i in a) if ($1==a[i]) print}' | wc -l)"
  [ "$busy" -eq 0 ] && break
  sleep "$interval"
done

echo
echo "watched builds finished:"
rc=0
for id in $watched; do
  state="$(curl -fsSL "https://copr.fedorainfracloud.org/api_3/build/$id" \
    | python3 -c "import json,sys; print(json.load(sys.stdin)['state'])" 2>/dev/null || true)"
  [ -n "$state" ] || state="unknown (deleted mid-watch?)"
  echo "  $id $state"
  [ "$state" = "succeeded" ] || rc=1
done
exit "$rc"
