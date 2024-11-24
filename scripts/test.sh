#!/usr/bin/env bash

set -e

command=( "$@" )
if [ "${#command[@]}" -eq 0 ]; then
  command=( "pytest" )
fi

chrome_version=$(google-chrome --version)
echo "Chrome version: $chrome_version"

set -x
uv run "${command[@]}"
