#!/bin/sh

find_micropython() {
    micropython=""
    for x in micropython \
             "SKIP $HOME/repo/micropython/ports/unix/build-coverage/micropython" \
             "$HOME/repo/micropython/ports/unix/build-standard/micropython" \
             ;
    do
        case "$x" in
        SKIP*) continue;;
        esac
        if type "$x" >/dev/null 2>&1; then
            micropython="$x"
            printf "%s\n" "$micropython"
            return 0
        fi
    done
    if [ -z "$micropython" ]; then
        echo "micropython is not found"
        exit 1
    fi
}
