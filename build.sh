#!/bin/bash
# Expected arguments:
# $1 = out_dir
# $2 = dest_dir
# $3 = build_number

# exit on error
set -e

# calculate the root directory from the script path
# this script lives two directories down from the root
# tools/cmake-utils/build.sh
ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)
cd "$ROOT_DIR"

function die() {
echo "$*" > /dev/stderr
    echo "Usage: $0 <out_dir> <dest_dir> <build_number>" > /dev/stderr
    exit 1
}

(($# > 3)) && die "[$0] Unknown parameter: $4"

OUT=$1
DEST=$2
BNUM=$3

[ ! "$OUT"  ] && die "## Error: Missing out folder"
[ ! "$DEST" ] && die "## Error: Missing destination folder"
[ ! "$BNUM" ] && die "## Error: Missing build number"

mkdir -p "$OUT" "$DEST"
OUT=$(cd "$OUT" && pwd -P)
DEST=$(cd "$DEST" && pwd -P)

cat <<END_INFO
## Building CMake ##
## Out Dir  : $OUT
## Dest Dir : $DEST
## Build Num: $BNUM

END_INFO

case "$(uname -s)" in
    Linux)  OS=linux;;
    Darwin) OS=darwin;;
    *_NT-*) OS=windows;;
esac

case "$OS" in
    windows)
        ROOT_DIR=$(cygpath -w "$ROOT_DIR")
        OUT=$(cygpath -w "$OUT")
        DEST=$(cygpath -w "$DEST")
        ;;
esac

SOURCE=$ROOT_DIR/external/cmake
CMAKE_UTILS=$ROOT_DIR/tools/cmake-utils
ANDROID_CMAKE=$ROOT_DIR/external/android-cmake
PREBUILTS=$ROOT_DIR/prebuilts
NINJA=$PREBUILTS/ninja/$OS-x86/ninja
CMAKE=("$PREBUILTS/cmake/$OS-x86/bin/cmake")

BUILD=$OUT/cmake/build
INSTALL=$OUT/cmake/install
rm -rf "$BUILD" "$INSTALL"
mkdir -p "$BUILD" "$INSTALL"

# print commands for easier debugging
set -x

CONFIG=Release

case "$OS" in
    linux)
        TOOLCHAIN=$PREBUILTS/gcc/linux-x86/host/x86_64-linux-glibc2.15-4.8
        CMAKE_OPTIONS+=(-DCMAKE_C_COMPILER="$TOOLCHAIN/bin/x86_64-linux-gcc")
        CMAKE_OPTIONS+=(-DCMAKE_CXX_COMPILER="$TOOLCHAIN/bin/x86_64-linux-g++")
        CMAKE_OPTIONS+=(-DCMAKE_USE_OPENSSL=ON)
        OPENSSL=$ROOT_DIR/external/openssl
        CMAKE_OPTIONS+=(-DOPENSSL_INCLUDE_DIR="$OPENSSL/include")
        ;;
    darwin)
        ;;
    windows)
        CMAKE_OPTIONS+=(-DCMAKE_C_FLAGS_RELEASE=/MT)
        CMAKE_OPTIONS+=(-DCMAKE_CXX_FLAGS_RELEASE=/MT)
        CMAKE=(env PATH=$(cygpath --unix 'C:\Windows\System32')
               cmd /c "${VS140COMNTOOLS}VsDevCmd.bat" '&&' "${CMAKE[@]}")
        ;;
esac

CMAKE_OPTIONS+=(-G Ninja)
CMAKE_OPTIONS+=("$SOURCE")
CMAKE_OPTIONS+=(-DCMAKE_MAKE_PROGRAM="$NINJA")
CMAKE_OPTIONS+=(-DCMAKE_BUILD_TYPE=$CONFIG)
CMAKE_OPTIONS+=(-DCMAKE_INSTALL_PREFIX=)

(cd $BUILD && "${CMAKE[@]}" "${CMAKE_OPTIONS[@]}")
"${CMAKE[@]}" --build "$BUILD"
# TODO: fix tests on the builders
# mostly caused by non-standard generator and compiler locations
# "${CMAKE[@]}" --build "$BUILD" --target test
DESTDIR="$INSTALL" "${CMAKE[@]}" --build "$BUILD" --target install

case "$OS" in
    windows)
        install "${NINJA}.exe" "$INSTALL/bin/"
        ;;
    *)
        install "$NINJA" "$INSTALL/bin/"
        ;;
esac

# Use the last column of first line of cmake --version for revision number:
# cmake version x.y.z
# then grab the major and minor versions:
# x.y
REVISION=$("$INSTALL/bin/cmake" --version |
           awk 'NR==1{print $NF}' |
           grep --only-matching '^[0-9]\+\.[0-9]\+')
# Use the build number for the micro version
# TODO: change Pkg.Path to cmake;$REVISION after preview 4 is available
cat > "$INSTALL/source.properties" <<EOF
Pkg.Revision=$REVISION.$BNUM
Pkg.Desc=CMake $REVISION
Pkg.Path=cmake
EOF

install -m 644 "$CMAKE_UTILS/android.toolchain.cmake"   "$INSTALL/"
install -m 644 "$ANDROID_CMAKE/AndroidNdkModules.cmake" "$INSTALL/share/cmake-$REVISION/Modules/"
install -m 644 "$ANDROID_CMAKE/AndroidNdkGdb.cmake"     "$INSTALL/share/cmake-$REVISION/Modules/"

(cd "$INSTALL" && zip -FSry "$DEST/cmake-${OS}-${BNUM}.zip" .)
