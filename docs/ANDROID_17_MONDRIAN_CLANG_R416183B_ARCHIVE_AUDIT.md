# Stage 188 — historical PixelExperience kernel Clang r416183b vs clean AOSP 17

**Target:** Independent PixelExperience-Reborn based **only on official Android Open Source Project Android 17**, with the POCO F5 Pro / Redmi K60 (`mondrian`, Qualcomm SM8475) as the eventual device. The previous PixelExperience team's project layout, manifests, build choices, revision provenance and commit history are compatibility references. LineageOS/CLO/other ROM sources are **not** a base and are **not** imported.

## What the PE history actually says

- PE `seventeen`, `fourteen` and `thirteen` branches of this archived repository resolve to Git commit **`54220fd601050b350b2af7adc913089ebf0e7aed`** (2022-11-01), import message: **`Import r416183b from android-13.0.0_r0.20`**.
- `AndroidVersion.txt` is **`12.0.5`** followed by **`based on r416183b`**. The tree has **5,969 Git entries** and includes large ELF toolchain binaries and runtimes; `bin/clang-12` is the historical compiler binary, object SHA **`ee798bcd148c4217507edb1e91874c472a6f52be`**, ~91,448,808 bytes in the Git tree. Preserve it for archival reproducibility; never modify its bytes or pretend it is LLVM 17/18/Android 17.
- `BUILD.bazel` exposes a `filegroup(name = "binaries")` over `bin/*` and `lib64/*`. That filegroup **does not declare a modern device kernel toolchain** or prove source/build compatibility.
- The historic PE manifest `seventeen` is **AOSP Android 14 tag `android-14.0.0_r22`**, with a PixelExperience-specific project graph on top of **AOSP**, using `repo` projects and ordinary AOSP build/Soong pieces. Its historical organization is informative; none of its older platform tags or toolchains should override the new baseline.

## Verified clean AOSP 17 platform toolchain

- This PE-Reborn AOSP 17 project's `aosp17_reference.xml` is grounded in the official **`refs/tags/android-17.0.0_r1`** manifest and selects **`prebuilts/clang/host/linux-x86`** from official `platform/prebuilts/clang/host/linux-x86`.
- The pinned PE-Reborn AOSP17 `build_soong` commit **`6215d41c790a463b7795ce81ac77204c238cbf48`**, file `cc/config/global.go`, declares **`ClangDefaultVersion = "clang-r584948"`**. This is the Android *platform* default at the audited AOSP17 pin, **not** a confirmed kernel build toolchain for mondrian.
- Official AOSP Android17-release's Clang prebuilt repository exposes modern `clang-r584948` alongside other sanctioned versions. The platform version is read from Soong/release config. We do **not** invent or hardcode a newer revision, nor override `ClangDefaultVersion` to make an archival kernel compile.
- **Platform** and **kernel** source trees have separate build constraints. The kernel must be compiled with a revision demonstrated compatible with the specific Linux 5.10 Qualcomm/Xiaomi source, Clang/LLD integrated assembler, KCFI/CFI/LTO, binary output and all vendor modules/devicetrees. A globally newer compiler is not necessarily a compatible compiler for an older 5.10 vendor kernel.

Official references:
- https://android.googlesource.com/platform/prebuilts/clang/host/linux-x86/+/refs/heads/android17-release
- https://android.googlesource.com/platform/prebuilts/clang/host/linux-x86/
- https://source.android.com/docs/setup/build/building-kernels
- https://source.android.com/docs/core/architecture/kernel/stable-kmi

## Stage 188 actual code / manifest changes

1. This **archive repository** adds an independently testable, non-invasive `tests/check_aosp17_legacy_clang_boundary.py`. CI checks its exact original compiler version text, Bazel artifact declaration, exact **Git blob SHA** of the unmodified `bin/clang-12` and ancestry of the original PE archive import. **No historic compiler executable or runtime is changed, copied or executed.**
2. The tests also assert that a separately fetched/pinned official AOSP17 baseline manifest still selects the canonical `prebuilts/clang/host/linux-x86` owner and **does not add the archived `prebuilts/clang/kernel/linux-x86/clang-r416183b` path**.
3. The tests parse `cc/config/global.go` at the exact audited AOSP17 `build_soong` pin and verify `ClangDefaultVersion` remains `clang-r584948` and uses the upstream Soong version resolver, not a locally fabricated override.
4. The manifest validation script now rejects this old kernel Clang path or its historical repository aliases from **all active and candidate AOSP17 source graphs**, with negative tests. `default.xml` is intentionally unchanged.
5. GitHub Actions uses **partial/sparse checkout**, meaning a CI run does **not download hundreds of megabytes of obsolete toolchain binaries**. It verifies the immutable Git tree object IDs and the AOSP17 source ownership contracts, not the behavior of the old binary.

**No new compiler is added:** doing so would require fetching trustworthy, released, verifiable prebuilt toolchains through the official AOSP17 `repo` manifest, with exact commit pinned. This stage does not create an untrusted or hand-rolled compiler distribution.

## What is still required before mondrian kernel/toolchain integration

- Select a proven Clang revision for **the exact** SM8475 Xiaomi Linux 5.10 kernel variant; check the kernel `Makefile` LLVM and `LLVM_IAS` support, all old vendor toolchain-specific flags and version assumptions.
- Verify the actual build command and output, preserve artifact SHA and `clang --version`, and test whether `LLVM=1`, `LLVM_IAS=1` plus host tools work. No blanket dependency on obsolete GCC4.9 and no automatic forced migration to the newest mainline kernel LLVM.
- Build kernel image, DTBO, modules and vendor modules with **coherent Clang/LLD settings** and verify their ABI, Android17 module loading, vendor boot/recovery and secure boot integration. This is separate from AOSP Soong platform compiler selection; don't import any other ROM kernel source as the project base.
- Analyze kernel GKI/KMI/FCM/SELinux, KASAN, CFI/LTO, relevant vendor drivers and how out-of-tree modules link. Check the actual running device and its factory/vendor ABI; use read-only existing device source for reference, not wholesale copy.
- Full AOSP17 `repo sync`, Soong+Make, kernel build, boot, kernel module ABI and CTS/VTS **have not been performed**. The host source/manifest tests can only prevent an incorrect source ownership override.

**Status:** historical clang12 archive preserved and audited; clean AOSP17 host LLVM owner independently verified at source level; fail-closed manifest/source gates. No claim that Clang r584948 is the right toolchain for the Xiaomi Linux 5.10 kernel.
