#!/usr/bin/env bash

set -e

command=( "$@" )
if [ "${#command[@]}" -eq 0 ]; then
  command=( "pytest" )
fi

set -x
uv run "${command[@]}"
