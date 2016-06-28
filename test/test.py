#!/usr/bin/env python

import json
import os
import shlex
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

    def check_json_library(self, key, value, toolchain_key):
        split_key = key.split('-', 2)
        self.assertEqual(len(split_key), 3)
        [name, build_type, abi] = split_key
        self.assertEqual(build_type, self.build_type)
        self.assertEqual(abi, self.abi)
        self.assertEqual(value['abi'], abi)
        self.assertEqual(value['artifactName'], name)
        self.assertEqual(value['buildCommand'],
                         '%s --build %s --target %s' %
                         (cmake, self.cmake_build, name))
        self.assertEqual(value['buildType'], build_type)
        files = value['files']
        self.assertEqual(len(files), 1)
        flags = files[0]['flags']
        self.assertTrue(flags)
        tokenized_flags = shlex.split(flags)
        self.assertTrue('-DANDROID' in tokenized_flags)
        self.assertEqual('-DNONE' in tokenized_flags,
                         self.stl == 'none')
        self.assertEqual('-DSYSTEM' in tokenized_flags,
                         self.stl == 'system')
        self.assertEqual('-DNEON' in tokenized_flags,
                         self.abi == 'armeabi-v7a' and
                         name.startswith('neon_'))
        split_name = name.split('_', 2)
        if 'neon' in split_name:
            self.assertEqual(len(split_name), 3)
            split_name.remove('neon')
        self.assertEqual(len(split_name), 2)
        split_name.reverse()
        source = '.'.join(split_name)
        if 'exe' not in split_name:
            source = os.path.join(split_name[0], source)
        source = os.path.join(project, source)
        self.assertEqual(files[0]['src'], source)
        self.assertEqual(files[0]['workingDirectory'], self.cmake_build)
        if name.endswith('_exe'):
            output = name
        elif name.endswith('_shared'):
            output = 'lib%s.so' % name
        elif name.endswith('_static'):
            output = 'lib%s.a' % name
        self.assertEqual(value['output'],
                         os.path.join(self.cmake_build, output))
        self.assertEqual(value['toolchain'], toolchain_key)

    def check_json(self, json_file):
        json_obj = json.load(open(json_file))
        libraries = ['c_exe', 'c_shared', 'c_static', 'cpp_exe']
        c_file_extensions = ['c']
        cpp_file_extensions = ['cpp']
        if self.stl not in ['none', 'system']:
            libraries += ['cpp_shared', 'cpp_static']
        if self.abi == 'armeabi-v7a':
            libraries += ['neon_c_exe', 'neon_cpp_exe']
        self.assertEqual(json_obj['buildFiles'],
                         [os.path.join(project, 'CMakeLists.txt')])
        self.assertEqual(json_obj['cFileExtensions'],
                         c_file_extensions)
        self.assertEqual(json_obj['cppFileExtensions'],
                         cpp_file_extensions)
        self.assertEqual(json_obj['cleanCommands'],
                         ['%s --build %s --target clean' %
                          (cmake, self.cmake_build)])
        self.assertEqual(len(json_obj['toolchains']), 1)
        toolchain_key = json_obj['toolchains'].keys()[0]
        toolchain = json_obj['toolchains'].values()[0]
        self.assertTrue(toolchain['cCompilerExecutable'].startswith(
            os.path.join(ndk, 'toolchains')))
        self.assertTrue(toolchain['cppCompilerExecutable'].startswith(
            os.path.join(ndk, 'toolchains')))
        self.assertTrue(toolchain['cppCompilerExecutable'].endswith('++'))
        self.assertEqual(len(json_obj['libraries']), len(libraries))
        for library in libraries:
            key = '%s-%s-%s' % (library, self.build_type, self.abi)
            self.assertTrue(key in json_obj['libraries'])
        for key, value in json_obj['libraries'].iteritems():
            self.check_json_library(key, value, toolchain_key)

    def compile_cmake(self):
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
        json_file = os.path.join(self.cmake_build, 'android_gradle_build.json')
        self.check_json(json_file)
        command = [cmake, '--build', self.cmake_build]
        self.run_and_assert_success(command)

    def compile_ndk(self):
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
                        setattr(TestCMake, name, test)


if __name__ == '__main__':
    generate_all_tests()
    unittest.main()
