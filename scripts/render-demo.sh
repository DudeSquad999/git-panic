#!/usr/bin/env bash
# Regenerates assets/demo-terminal.svg from REAL git-panic output.
#
# It builds a disposable repository in a fresh temporary directory, makes the
# classic "git reset --hard" mistake there (never in your project), runs the
# actual git-panic binary, and renders the captured text into an SVG.
#
# Usage:  scripts/render-demo.sh [path/to/git-panic]   (default: target/release/git-panic)
# Needs:  bash, git >= 2.28, python3. Run `cargo build --release` first.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
bin="${1:-$root/target/release/git-panic}"
[ -x "$bin" ] || { echo "git-panic binary not found: $bin (run cargo build --release)" >&2; exit 1; }

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null
export GIT_AUTHOR_DATE="2026-01-01T00:00:00Z" GIT_COMMITTER_DATE="2026-01-01T00:00:00Z"

cd "$work"
mkdir practice && cd practice
git init -q -b main
git config user.name "git-panic demo"
git config user.email "demo@example.invalid"
git config commit.gpgsign false
git config core.hooksPath /dev/null

printf 'one\n' > notes.txt && git add notes.txt && git commit -q -m "demo: first version"
printf 'two\n' > notes.txt && git add notes.txt && git commit -q -m "demo: second version"
git reset -q --hard HEAD~1   # the "mistake", inside the disposable repo only

transcript="$work/transcript.txt"
run() {  # print the command line, then its real output
  printf '$ %s\n' "$*" >> "$transcript"
  "$@" >> "$transcript" 2>&1 || true
}
SHA="$("$bin" "demo: second" | awk 'NR==1{print $2}')"

run "$bin" "demo: second"
run "$bin" recover "$SHA" --branch panic/lost
run "$bin" recover "$SHA" --branch panic/lost --create
printf '$ git show panic/lost:notes.txt\n' >> "$transcript"; git show panic/lost:notes.txt >> "$transcript"
printf '$ cat notes.txt\n' >> "$transcript"; cat notes.txt >> "$transcript"

# Show the tool by name, not by temp path.
sed -i "s#$bin#git-panic#g" "$transcript"

python3 "$root/scripts/transcript_to_svg.py" "$transcript" "$root/assets/demo-terminal.svg"
echo "wrote $root/assets/demo-terminal.svg"
