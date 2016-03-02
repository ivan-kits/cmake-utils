@echo off
@rem
@rem cmake_generate_android_gradle.bat
@rem The purpose of this script is to setup the build directories
@rem for every build type and architecture for the cmake project
@rem under its own subfolder in the Android Studio project
@rem
@rem android_studio_project_root/
@rem |- imported_cmake_project_module/
@rem |  |- cmake/
@rem |  |  |- debug/
@rem |  |  |  |- armeabi/
@rem |  |  |  |  |- android_gradle_build.json
@rem |  |  |  |  `- ...
@rem |  |  |  |- x86/
@rem |  |  |  |  |- android_gradle_build.json
@rem |  |  |  |  `- ...
@rem |  |  |  `- ...
@rem |  |  `- release/
@rem |  |     `- ...
@rem |  |- build.gradle
@rem |  |- project/
@rem |  |  `- ...
@rem |  `- ...
@rem `- ...

@rem Path to new Android Studio module
set BUILD_ROOT=%~f1

@rem Path to CMake project source
set SOURCE=%~f2

@rem Target API level
@rem [ 3, 4, 5, 8, 9, 12, 13, 14, 15, 16, 17, 18, 19, 21 ]
set API=%~3

@rem All or comma delimited list of target ABIs for which to build
@rem [ arm64-v8a, armeabi,
@rem   armeabi-v6 with VFP,
@rem   armeabi-v7a, armeabi-v7a with NEON, armeabi-v7a with VFPV3,
@rem   mips, mips64,
@rem   x86, x86_64 ]
@rem E.g., "all"
@rem E.g., "armeabi-v7a with NEON,x86,mips"
set ABIS=%~4

@rem All remaining parameters will be passed to CMake as is
@rem E.g., "-DCMAKE_C_FLAGS=-foo" "-DCMAKE_CXX_FLAGS=-bar -baz"
set ARGS=
:loop
if [%5] == [] goto done
set ARGS=%ARGS% "%~5"
shift /5
goto loop
:done

set SDK=%~dp0..

set BUILD_TYPES=Debug Release
if "%ABIS%" == "all" (
    set ABIS=arm64-v8a,armeabi,armeabi-v7a,mips,mips64,x86,x86_64
)

@rem TODO: add multiprocessing to speed things up.
for %%B in (%BUILD_TYPES%) do (
    setlocal enabledelayedexpansion
    for %%A in ("%ABIS:,=","%") do (
        set BUILD=%BUILD_ROOT%\%%B\%%~A
        if not exist "!BUILD!" mkdir "!BUILD!"

        "%SDK%\cmake\bin\cmake" ^
            -H"%SOURCE%" ^
            -B"!BUILD!" ^
            -G "Android Gradle - Ninja" ^
            -DANDROID_ABI=%%A ^
            -DANDROID_NATIVE_API_LEVEL=%API% ^
            -DANDROID_NDK="%SDK%\ndk-bundle" ^
            -DCMAKE_BUILD_TYPE=%%B ^
            -DCMAKE_MAKE_PROGRAM="%SDK%\cmake\bin\ninja" ^
            -DCMAKE_TOOLCHAIN_FILE="%SDK%\cmake\android.toolchain.cmake" ^
            %ARGS%
    )
    setlocal disabledelayedexpansion
)

set ERROR=0

for %%B in (%BUILD_TYPES%) do (
    setlocal enabledelayedexpansion
    for %%A in ("%ABIS:,=","%") do (
        set JSON=%BUILD_ROOT%\%%B\%%A\android_gradle_build.json
        if not exist !JSON! (
            set ERROR=1
            echo "Configuring for %%B %%A failed!" >&2
        )
    )
    setlocal disabledelayedexpansion
)

exit %ERROR%
