#!/usr/bin/env python

import os
import shutil
import subprocess
import sys
import unittest

test_root = os.path.realpath(os.path.dirname(__file__))
repo_root = os.path.realpath(os.path.join(test_root, '..', '..', '..'))

if 'NDK' in os.environ:
    ndk = os.environ.get('NDK')
elif 'ANDROID_NDK_HOME' in os.environ:
    ndk = os.environ.get('ANDROID_NDK_HOME')
else:
    print('Usage: NDK=/path/to/ndk %s' % ' '.join(sys.argv))
    exit()
if not os.path.isdir(ndk):
    raise Exception('Invalid NDK: %s' % ndk)
ndk = os.path.realpath(ndk)
if 'OUT' in os.environ:
    out = os.environ.get('OUT')
else:
    out = os.path.join(repo_root, 'out')
if not os.path.isdir(out):
    raise Exception('Invalid build directory: %s' % out)

tmp = os.path.join(out, 'cmake', 'test')
cmake_root = os.path.join(out, 'cmake', 'install')
cmake = os.path.join(cmake_root, 'bin', 'cmake')
ninja = os.path.join(cmake_root, 'bin', 'ninja')
ndk_build = os.path.join(ndk, 'ndk-build')

# toolchain_file = os.path.join(cmake_root, 'android.toolchain.cmake')
toolchain_file = os.path.join(test_root, '..', 'android.toolchain.cmake')
ndk_toolchain_file = os.path.join(ndk, 'build', 'cmake',
                                  'android.toolchain.cmake')
if os.path.isfile(ndk_toolchain_file):
    toolchain_file = ndk_toolchain_file
if not os.path.isfile(toolchain_file):
    raise Exception('Invalid toolchain file: %s' % toolchain_file)

if os.name == 'nt':
    cmake += '.exe'
    ninja += '.exe'
    ndk_build += '.cmd'


class TestCMake(unittest.TestCase):
    def make_build_directories(self):
        build = os.path.join(tmp, self.toolchain, self.abi,
                             self.platform, self.stl, self.build_type)
        if os.path.isdir(build):
            shutil.rmtree(build)
        self.cmake_build = os.path.join(build, 'cmake')
        self.ndk_build = os.path.join(build, 'ndk')
        os.makedirs(self.cmake_build)
        os.makedirs(self.ndk_build)

    def run_and_assert_success(self, command):
        popen = subprocess.Popen(command,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        stdout = popen.stdout.read()
        stderr = popen.stderr.read()
        self.assertEqual(stderr, '',
                         msg='\n%s\n%s\n%s' %
                         (str.join(' ', command), stdout, stderr))
        self.assertEqual(popen.wait(), 0,
                         msg='\n%s\n%s\n%s' %
                         (str.join(' ', command), stdout, stderr))

    def compile_cmake(self):
        project = os.path.join(test_root, 'project')
        command = [cmake,
                   '-H%s' % project,
                   '-B%s' % self.cmake_build,
                   '-GNinja',
                   '-DCMAKE_TOOLCHAIN_FILE=%s' % toolchain_file,
                   '-DCMAKE_MAKE_PROGRAM=%s' % ninja,
                   '-DANDROID_NDK=%s' % ndk,
                   '-DANDROID_TOOLCHAIN=%s' % self.toolchain,
                   '-DANDROID_ABI=%s' % self.abi,
                   '-DANDROID_PLATFORM=%s' % self.platform,
                   '-DANDROID_STL=%s' % self.stl,
                   '-DCMAKE_BUILD_TYPE=%s' % self.build_type]
        self.run_and_assert_success(command)
        command = [cmake, '--build', self.cmake_build]
        self.run_and_assert_success(command)

    def compile_ndk(self):
        project = os.path.join(test_root, 'project')
        toolchain = self.toolchain
        if toolchain == 'gcc':
            toolchain = '4.9'
        if self.abi == 'armeabi':
            ldflags = '-latomic'
        else:
            ldflags = ''
        command = [ndk_build,
                   '-C', project,
                   'NDK_TOOLCHAIN_VERSION=%s' % toolchain,
                   'APP_ABI=%s' % self.abi,
                   'APP_PLATFORM=%s' % self.platform,
                   'APP_STL=%s' % self.stl,
                   'APP_OPTIM=%s' % self.build_type,
                   'NDK_OUT=%s' % os.path.join(self.ndk_build, 'obj'),
                   'NDK_LIBS_OUT=%s' % os.path.join(self.ndk_build, 'libs'),
                   'APP_LDFLAGS=%s' % ldflags]
        self.run_and_assert_success(command)

    def test_response_file(self):
        response_file = os.path.join(test_root, 'response_file')
        build = os.path.join(tmp, 'response_file')
        if os.path.isdir(build):
            shutil.rmtree(build)
        os.makedirs(build)

        command = [cmake,
                   '-H%s' % response_file,
                   '-B%s' % build,
                   '-GNinja',
                   '-DCMAKE_TOOLCHAIN_FILE=%s' % toolchain_file,
                   '-DCMAKE_MAKE_PROGRAM=%s' % ninja,
                   '-DANDROID_NDK=%s' % ndk,
                   '-DCMAKE_NINJA_FORCE_RESPONSE_FILE=TRUE']
        self.run_and_assert_success(command)
        command = [cmake, '--build', build]
        self.run_and_assert_success(command)

    def test_neon(self):
        neon = os.path.join(test_root, 'neon')
        build = os.path.join(tmp, 'neon')
        if os.path.isdir(build):
            shutil.rmtree(build)
        os.makedirs(build)

        command = [cmake,
                   '-H%s' % neon,
                   '-B%s' % build,
                   '-GNinja',
                   '-DCMAKE_TOOLCHAIN_FILE=%s' % toolchain_file,
                   '-DCMAKE_MAKE_PROGRAM=%s' % ninja,
                   '-DANDROID_NDK=%s' % ndk,
                   '-DANDROID_ABI=armeabi-v7a',
                   '-DANDROID_ARM_NEON=TRUE']
        self.run_and_assert_success(command)
        command = [cmake, '--build', build]
        self.run_and_assert_success(command)

    def compare(self):
        self.make_build_directories()
        self.compile_cmake()
        # self.compile_ndk()
        # TODO: compare the build output or build artifacts


def generate_test(toolchain, abi, platform, stl, build_type):
    def test(self):
        self.toolchain = toolchain
        self.abi = abi
        self.platform = platform
        self.stl = stl
        self.build_type = build_type
        self.compare()
    return test


def generate_all_tests():
    toolchains = ['clang', 'gcc']
    abis = ['armeabi', 'armeabi-v7a', 'arm64-v8a',
            'x86', 'x86_64', 'mips', 'mips64']
    platform_levels = [8, 9, 10, 16, 20, 21, 24]
    stls = ['none', 'system', 'stlport_static', 'stlport_shared',
            'gnustl_static', 'gnustl_shared', 'c++_static', 'c++_shared']
    build_types = ['debug', 'release']
    for toolchain in toolchains:
        for abi in abis:
            for platform_level in platform_levels:
                for stl in stls:
                    for build_type in build_types:
                        platform = 'android-%d' % platform_level
                        name = 'test_%s_%s_%s_%s_%s' % (toolchain, abi,
                                                        platform, stl,
                                                        build_type)
                        test = generate_test(toolchain, abi, platform,
                                             stl, build_type)
                        setattr(TestCMake, name, test)


if __name__ == '__main__':
    generate_all_tests()
    unittest.main()
