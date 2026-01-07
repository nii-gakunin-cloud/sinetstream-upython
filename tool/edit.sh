#!/bin/sh
set -eu
set -x

mpremote="$1"; shift
target_file="$1"

tmp_file=$(mktemp)
bak_file=bak/bak-$(echo ${target_file} | sed 's|/|_|g')-$(date +'%Y%m%d%H%M%S')
mkdir -p bak

${mpremote} fs cp :${target_file} ${tmp_file}
cp ${tmp_file} ${bak_file}b
${EDITOR:-vi} ${tmp_file}
${mpremote} fs cp ${tmp_file} :${target_file}
mv ${tmp_file} ${bak_file}a
