#!/bin/sh

set -eu
#set -x

prog="$0"

# ディレクトリ構成
top_dir=".."
img_dir="$top_dir/img"
lib_dir="$img_dir/lib"

test_file() {
    test -f "$1" || {
        printf "%s: %s doesn't exist\n" "$prog" "$1"
        exit 1
    }
}
test_dir() {
    test -d "$1" || {
        printf "%s: %s doesn't exist\n" "$prog" "$1"
        exit 1
    }
}

test_file "$top_dir/package.json"
test_dir "$img_dir"

# バイトコンパイラの作成
docker build --no-cache --tag mpy-cross - < Dockerfile.mpy-cross
docker run --rm mpy-cross /mpy-cross --version

# ソースファイルをコピーする
rm -rf "$lib_dir"
mkdir -p "$lib_dir"
lib_dir_abs=$(realpath "$lib_dir")
(cd root/lib &&
 find . -follow -name "*.py" -print | cpio -p --make-directories --dereference "$lib_dir_abs")

# バイトコンパイルする
docker run --user $(id -u) --rm --volume "$(realpath "$img_dir")":/ss mpy-cross /bin/sh -c 'cd /ss && find * -name "*.py" -print0 | xargs -0 -n1 -t /mpy-cross'

# ファイルサイズの表示
show_sz() {
    bytes() {
        cat "$1" | wc -c
    }
    (
    cd "$img_dir"
    find * -name "*.py" -print | while read X_PY ; do
        X_MPY="${X_PY%.py}.mpy"
        PY_SZ=$(bytes "$X_PY")
        MPY_SZ=$(bytes "$X_MPY")
        printf "%s %d -> %s %d (%d%%)\n" "$X_PY" "$PY_SZ" "$X_MPY" "$MPY_SZ" "$(($MPY_SZ * 100 / $PY_SZ))"
    done
    )
}
#show_sz

# xxx.pyとxxx.mpyの両方が存在するとxxx.pyが読み込まれるのでxxx.pyは消す
find "$img_dir" -name "*.py" -print0 | xargs -0 rm

# uavroの*.mpyは著作権的にsinetstream-upythonに含めたくないので
# uavro/imgにコピーしてリリース時には$lib_dir/uavro/*.mpyを消す
uavro_img_dir="$top_dir/lib/uavro/img"
uavro_lib_dir="$uavro_img_dir/lib"
if [ -d "$uavro_lib_dir/uavro" ]; then
    cp "$lib_dir"/uavro/*.mpy "$uavro_lib_dir/uavro"
else
    echo "WARN: the directory $uavro_lib_dir/uavro doesn't exist"
fi

echo "done"
exit 0
