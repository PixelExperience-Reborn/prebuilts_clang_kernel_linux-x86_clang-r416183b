#!/usr/bin/env python3
"""Archive-only compiler ownership gate: AOSP17 is the ONLY ROM platform base.

This does not compile LLVM, the Android platform or the mondrian 5.10 kernel.
Use sparse Git checkout so the 90 MB old clang executable is NOT downloaded.
Set PE_AOSP17_MANIFEST and PE_AOSP17_SOONG_GLOBAL to checked-out/pinned AOSP17
source files for the CI cross-repo ownership assertions.
"""
from pathlib import Path
import os
import re
import subprocess
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_COMMIT = "54220fd601050b350b2af7adc913089ebf0e7aed"
LEGACY_BINARY_SHA = "ee798bcd148c4217507edb1e91874c472a6f52be"
OFFICIAL_CLANG = "clang-r584948"
PLATFORM_PROJECT = "platform/prebuilts/clang/host/linux-x86"


class LegacyKernelClangBoundary(unittest.TestCase):
    def test_archive_identifies_itself_as_clang_12_not_android17(self):
        text = (ROOT / "AndroidVersion.txt").read_text(encoding="utf-8")
        self.assertEqual(text.strip().splitlines(), [
            "12.0.5", "based on r416183b",
        ])
        self.assertNotIn(OFFICIAL_CLANG, text)
        source = (ROOT / "BUILD.bazel").read_text(encoding="utf-8")
        self.assertIn('srcs = glob([', source)
        self.assertIn('"bin/*"', source)
        self.assertIn('"lib64/*"', source)
        self.assertNotIn("toolchain(", source)

    def test_immutable_archived_clang_binary_kept_for_history(self):
        # Read tree OBJECT metadata only. Never execute/download legacy Clang.
        result = subprocess.run(
            ["git", "-C", str(ROOT), "ls-tree", "-r", "HEAD", "--", "bin/clang-12"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = f"100644 blob {LEGACY_BINARY_SHA}\tbin/clang-12"
        self.assertEqual(result.stdout.strip(), expected)
        history = subprocess.run(
            ["git", "-C", str(ROOT), "merge-base", "--is-ancestor",
             ARCHIVE_COMMIT, "HEAD"],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(history.returncode, 0, history.stderr)

    def test_aosp17_manifest_uses_official_host_clang_owner(self):
        path = os.environ.get("PE_AOSP17_MANIFEST")
        self.assertTrue(path and Path(path).is_file(),
                        "must supply pinned official AOSP17 aosp17_reference.xml")
        root = ET.parse(path).getroot()
        self.assertEqual(root.find("default").get("revision"),
                         "refs/tags/android-17.0.0_r1")
        found = root.findall(".//project[@path='prebuilts/clang/host/linux-x86']")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].get("name"), PLATFORM_PROJECT)
        self.assertEqual(found[0].get("groups"), "pdk,sysui-studio")
        self.assertFalse(root.findall(
            ".//project[@path='prebuilts/clang/kernel/linux-x86/clang-r416183b']"))
        self.assertFalse(any(
            "prebuilts_clang_kernel_linux-x86_clang-r416183b"
            in (x.get("name") or "") for x in root.iter("project")
        ))

    def test_pinned_android17_soong_keeps_modern_compiler_default(self):
        path = os.environ.get("PE_AOSP17_SOONG_GLOBAL")
        self.assertTrue(path and Path(path).is_file(),
                        "must supply pinned AOSP17 cc/config/global.go")
        source = Path(path).read_text(encoding="utf-8")
        names = re.findall(
            r'(?m)^\s*ClangDefaultVersion\s*=\s*"([^"]+)"', source
        )
        self.assertEqual(names, [OFFICIAL_CLANG])
        self.assertIn('pctx.StaticVariable("ClangPath",', source)
        self.assertIn('return ctx.Config().ReleaseBuildClangVersion(ClangDefaultVersion)', source)
        self.assertNotIn('ClangDefaultVersion = "clang-r416183b"', source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
