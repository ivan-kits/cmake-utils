#!/bin/bash
# Build and test CMake deployed in Android Studio SDK
# Expected arguments:
# $1 = out_dir
# $2 = dest_dir
# $3 = build_number

echo Bash version:
uname -a

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

SOURCE=$ROOT_DIR/external/cmake
CMAKE_UTILS=$ROOT_DIR/tools/cmake-utils
ANDROID_CMAKE=$ROOT_DIR/external/android-cmake
PREBUILTS=$ROOT_DIR/prebuilts
NINJA_DIR=$PREBUILTS/ninja/$OS-x86
CMAKE=$PREBUILTS/cmake/$OS-x86/3.8.2/bin/cmake
CTEST=$PREBUILTS/cmake/$OS-x86/3.8.2/bin/ctest

BUILD=$OUT/cmake/build
INSTALL=$OUT/cmake/install
rm -rf "$BUILD" "$INSTALL"
mkdir -p "$BUILD" "$INSTALL"

# print commands for easier debugging
set -x

CONFIG=Release

CMAKE_OPTIONS+=(-G Ninja)
CMAKE_OPTIONS+=(-DCMAKE_BUILD_TYPE=$CONFIG)
CMAKE_OPTIONS+=(-DCMAKE_INSTALL_PREFIX=)

case "$OS" in
	linux|darwin)
		CMAKE_OPTIONS+=(-H"$SOURCE")
		CMAKE_OPTIONS+=(-B"$BUILD")
		if [ "$OS" == linux ]; then
			TOOLCHAIN=$PREBUILTS/gcc/linux-x86/host/x86_64-linux-glibc2.15-4.8
			CMAKE_OPTIONS+=(-DCMAKE_C_COMPILER="$TOOLCHAIN/bin/x86_64-linux-gcc")
			CMAKE_OPTIONS+=(-DCMAKE_CXX_COMPILER="$TOOLCHAIN/bin/x86_64-linux-g++")
			CMAKE_OPTIONS+=(-DCMAKE_USE_OPENSSL=ON)
			OPENSSL=$ROOT_DIR/external/openssl
			CMAKE_OPTIONS+=(-DOPENSSL_INCLUDE_DIR="$OPENSSL/include")
                        CMAKE_OPTIONS+=(-DOPENSSL_USE_STATIC_LIBS=ON)
                        CMAKE_OPTIONS+=(-DCMAKE_EXE_LINKER_FLAGS="-static-libstdc++ -static-libgcc")
		fi
		PATH=$NINJA_DIR:$PATH "$CMAKE" "${CMAKE_OPTIONS[@]}"
		DESTDIR=$INSTALL "$CMAKE" --build "$BUILD" --target install/strip
		;;
	windows)
		CMAKE_OPTIONS+=(-H"$(cygpath --windows "$SOURCE")")
		CMAKE_OPTIONS+=(-B"$(cygpath --windows "$BUILD")")
		CMAKE_OPTIONS+=(-DCMAKE_C_FLAGS_RELEASE=/MT)
		CMAKE_OPTIONS+=(-DCMAKE_CXX_FLAGS_RELEASE=/MT)
		cat > "$BUILD/android_build.bat" <<-EOF
		set PATH=$(cygpath --windows "$NINJA_DIR");C:\\Windows\\System32
		call "${VS140COMNTOOLS}VsDevCmd.bat"
		set CMAKE=$(cygpath --windows "$CMAKE.exe")
		set BUILD=$(cygpath --windows "$BUILD")
		set INSTALL=$(cygpath --windows "$INSTALL")
		%CMAKE% $(printf '"%s" ' "${CMAKE_OPTIONS[@]}")
		set DESTDIR=%INSTALL%
		%CMAKE% --build %BUILD% --target install
		EOF
		winpty "$(cygpath --windows "$BUILD/android_build.bat")"
		;;
esac

install "$NINJA_DIR/ninja"* "$INSTALL/bin/"

# Use the major and minor versions from CMake. E.g.,
# cmake version x.y.z => x.y
REVISION=$(
	"$INSTALL/bin/cmake" --version |
	sed -n 's/^cmake version \([0-9]*\.[0-9]*\)\..*$/\1/p'
)
# Use the build number for the micro version
cat > "$INSTALL/source.properties" <<-EOF
Pkg.Revision=$REVISION.$BNUM
Pkg.Desc=CMake $REVISION.$BNUM
Pkg.Path=cmake;$REVISION.$BNUM
EOF

install -m 644 "$CMAKE_UTILS/android.toolchain.cmake"   "$INSTALL/"
install -m 644 "$ANDROID_CMAKE/AndroidNdkModules.cmake" "$INSTALL/share/cmake-$REVISION/Modules/"
install -m 644 "$ANDROID_CMAKE/AndroidNdkGdb.cmake"     "$INSTALL/share/cmake-$REVISION/Modules/"

(cd "$INSTALL" && zip -FSry "$DEST/cmake-$OS-$BNUM.zip" .)

case "$OS" in
	linux|darwin)
		# If a test needs to be skipped:
		# EXCLUDE+=(-E '<insert test regex>')
		pushd "$BUILD"
		PATH=$NINJA_DIR:$PATH "$CTEST" "${EXCLUDE[@]}" \
			--force-new-ctest-process --output-on-failure
		popd
		;;
	windows)
		# Flaky test.
		EXCLUDE+=(-E '^CTestTestStopTime$')
		cat > "$BUILD/android_test.bat" <<-EOF
		set PATH=$(cygpath --windows "$NINJA_DIR");C:\\Windows\\System32
		call "${VS140COMNTOOLS}VsDevCmd.bat"
		set CTEST=$(cygpath --windows "$CTEST.exe")
		%CTEST% $(printf '"%s" ' "${EXCLUDE[@]}") ^
			--force-new-ctest-process --output-on-failure
		EOF
		pushd "$BUILD"
		cmd /c "$(cygpath --windows "$BUILD/android_test.bat")"
		popd
		;;
esac
