#!/bin/zsh
set -euo pipefail

typeset -a forwarded
typeset sql=''
while (( $# > 0 )); do
  if [[ "$1" == '-c' ]]; then
    shift
    sql="$1"
  else
    forwarded+=("$1")
  fi
  shift
done

if [[ -z "$sql" ]]; then
  print -u2 -- 'psql wrapper requires one -c SQL payload'
  exit 64
fi

/opt/homebrew/opt/postgresql@16/bin/psql "${forwarded[@]}" -f - <<< "$sql"
