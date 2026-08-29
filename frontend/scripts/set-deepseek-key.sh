#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
frontend_dir=$(CDPATH= cd -- "$script_dir/.." && pwd)
repo_root=$(CDPATH= cd -- "$frontend_dir/.." && pwd)
env_file="$frontend_dir/.env.local"

if ! git -C "$repo_root" check-ignore -q frontend/.env.local; then
  printf '%s\n' "Refusing to continue: frontend/.env.local is not ignored by Git." >&2
  exit 1
fi
if [ -L "$env_file" ]; then
  printf '%s\n' "Refusing to replace a symbolic-link .env.local." >&2
  exit 1
fi
if [ ! -t 0 ]; then
  printf '%s\n' "Run this helper from an interactive terminal." >&2
  exit 1
fi

restore_tty() {
  stty echo 2>/dev/null || true
  printf '\n' >&2
}
trap 'restore_tty; exit 130' HUP INT TERM
printf '%s' "DeepSeek API key (input hidden): " >&2
stty -echo
if ! IFS= read -r deepseek_key; then
  restore_tty
  exit 1
fi
restore_tty
trap - HUP INT TERM
if [ -z "$deepseek_key" ]; then
  printf '%s\n' "No key was entered; .env.local was not changed." >&2
  exit 1
fi

umask 077
tmp_file=$(mktemp "$frontend_dir/.env.local.tmp.XXXXXX")
cleanup() { rm -f -- "$tmp_file"; }
trap cleanup EXIT
key_written=false
if [ -f "$env_file" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      DEEPSEEK_API_KEY=*)
        if [ "$key_written" = false ]; then
          printf '%s\n' "DEEPSEEK_API_KEY=$deepseek_key" >> "$tmp_file"
          key_written=true
        fi
        ;;
      *) printf '%s\n' "$line" >> "$tmp_file" ;;
    esac
  done < "$env_file"
fi
if [ "$key_written" = false ]; then
  printf '%s\n' "DEEPSEEK_API_KEY=$deepseek_key" >> "$tmp_file"
fi
chmod 600 "$tmp_file"
mv -f -- "$tmp_file" "$env_file"
trap - EXIT
unset deepseek_key
git -C "$repo_root" check-ignore -q frontend/.env.local
printf '%s\n' "Updated frontend/.env.local, preserved unrelated values, and set permissions to 600. The key was not printed."
