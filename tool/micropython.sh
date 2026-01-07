#!/bin/sh
# Docker環境でsinetstream-upythonがつかえるmicropython/unixを起動するスクリプト

set -eu
#set -x

image="micropython/unix:v1.26.0"
image2="sinetstream-upython"

prog="$0"
package_json="$(realpath ../package.json)"

package_list=$(jq --raw-output '.deps[]|.[0]+"@"+.[1]' "$package_json" | tr '\n' ' ')
package_list="$package_list unittest@latest"

docker build --tag "$image2" - <<__END__
FROM $image
RUN micropython -m mip install $package_list
CMD ["/usr/local/bin/micropython"]
__END__

MICROPYPATH=$(docker run --rm "$image" micropython -c 'import sys; print(":".join(sys.path), end="")')

opt_list="--interactive --tty --rm"
opt_list="$opt_list --volume "$(realpath .)":/work"
opt_list="$opt_list --volume "$(realpath $(dirname "$prog")/..)":/sinetstream-upython"
MICROPYPATH="/sinetstream-upython/tool/root/lib:$MICROPYPATH"

docker run $opt_list --env MICROPYPATH="$MICROPYPATH" "$image2" "$@"
