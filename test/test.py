#!/usr/bin/env python

import os
import shutil
import subprocess
import unittest

project = os.path.realpath(os.path.dirname(__file__))
repo_root = os.path.realpath(os.path.join(project, '..', '..', '..'))

ndk = os.path.realpath(os.environ.get('ANDROID_NDK_HOME'))
if 'OUT' in os.environ:
    out = os.environ.get('OUT')
else:
    out = os.path.join(repo_root, 'out')

tmp = os.path.join(out, 'cmake', 'test')
cmake_root = os.path.join(out, 'cmake', 'install')
cmake = os.path.join(cmake_root, 'bin', 'cmake')
ninja = os.path.join(cmake_root, 'bin', 'ninja')
toolchain_file = os.path.join(cmake_root, 'android.toolchain.cmake')
ndk_build = os.path.join(ndk, 'ndk-build')


class TestToolchainFile(unittest.TestCase):
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

    def compile_cmake(self, target):
        command = [cmake,
                   '-H%s' % project,
                   '-B%s' % self.cmake_build,
                   '-GAndroid Gradle - Ninja',
                   '-DCMAKE_TOOLCHAIN_FILE=%s' % toolchain_file,
                   '-DCMAKE_MAKE_PROGRAM=%s' % ninja,
                   '-DANDROID_NDK=%s' % ndk,
                   '-DANDROID_TOOLCHAIN=%s' % self.toolchain,
                   '-DANDROID_ABI=%s' % self.abi,
                   '-DANDROID_PLATFORM=%s' % self.platform,
                   '-DANDROID_STL=%s' % self.stl,
                   '-DCMAKE_BUILD_TYPE=%s' % self.build_type]
        self.run_and_assert_success(command)
        command = [cmake, '--build', self.cmake_build, '--target', target]
        self.run_and_assert_success(command)

    def compile_ndk(self, target):
        toolchain = self.toolchain
        if toolchain == 'gcc':
            toolchain = '4.9'
        if self.abi == 'armeabi':
            ldflags = '-latomic'
        else:
            ldflags = ''
        command = [ndk_build,
                   target,
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

    def compare(self):
        self.make_build_directories()
        if self.stl in ['none', 'system']:
            target = 'c_exe'
        else:
            target = 'all'
        self.compile_cmake(target)
        # self.compile_ndk(target)
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
    platform_levels = [9, 16, 21, 24]
    stls = ['none', 'system', 'stlport_static', 'stlport_shared',
            'gnustl_static', 'gnustl_shared', 'c++_static', 'c++_shared']
    build_types = ['debug', 'release']
    for toolchain in toolchains:
        for abi in abis:
            for platform_level in platform_levels:
                if (platform_level < 21 and
                        abi in ['arm64-v8a', 'x86_64', 'mips64']):
                    continue
                for stl in stls:
                    for build_type in build_types:
                        platform = 'android-%d' % platform_level
                        name = 'test_%s_%s_%s_%s_%s' % (toolchain, abi,
                                                        platform, stl,
                                                        build_type)
                        test = generate_test(toolchain, abi, platform,
                                             stl, build_type)
                        setattr(TestToolchainFile, name, test)


if __name__ == '__main__':
    generate_all_tests()
    unittest.main()
