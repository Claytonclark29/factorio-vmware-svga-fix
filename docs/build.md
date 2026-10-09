# Reproduce the recorded private Mesa build

The original two builds completed previously. These publication instructions are a sanitized transcription of their configuration, not a newly executed rebuild. Tested source: **Mesa 25.2.8, Ubuntu 25.2.8-0ubuntu0.24.04.2**. Compiler GCC/G++ 13.3.0, Meson 1.7.0, Ninja 1.11.1, LLVM 20.1.2. Exact recorded package versions, Meson-resolved dependencies, source archive hashes and Ubuntu patch names/hashes are in [build-provenance.json](../evidence/build-provenance.json). It is not a full OS lockfile.

Obtain that exact Ubuntu source package in a fresh workspace using your distribution's authenticated source archive tooling (for example `apt source mesa=25.2.8-0ubuntu0.24.04.2` with the appropriate source repositories already configured). Verify both orig/debian archive SHA256 values against the provenance record. A correctly unpacked Ubuntu source package has its quilt series applied. If unpacking archives manually, apply the listed `debian/patches/series` exactly once. The repository does not vendor the source archives or distribution patches. Abort on a version/hash mismatch; do not silently use a newer Mesa release.

Provide the recorded dependencies before building. No installation commands are run by this repository. The retained minimal configuration resolves X11/XCB, GLVND, DRM, LLVM, expat, zlib/zstd and XML-related components; the package/version list documents the actual prerequisite transaction, while the resolved Meson list captures additional existing libraries. The complete distribution package build-dependency set may include components disabled by the minimal configuration.

In the following example, `mesa-src` is that verified unpacked source and `repository` is this repository. Use private absolute workspace paths for these local variables; do not publish personal path expansions. Do not use sudo or replace system libraries.

```bash
export PATH=/usr/lib/llvm-20/bin:/usr/bin:/bin
export CC=/usr/bin/gcc CXX=/usr/bin/g++
unset LD_LIBRARY_PATH LD_PRELOAD LIBGL_DRIVERS_PATH MESA_LOADER_DRIVER_OVERRIDE
unset LIBGL_ALWAYS_SOFTWARE GALLIUM_DRIVER DISPLAY WAYLAND_DISPLAY
meson setup build mesa-src \
  --prefix=/usr \
  --buildtype=release \
  --wrap-mode=nofallback \
  --libdir=lib/x86_64-linux-gnu \
  -Db_lto=false \
  -Db_ndebug=true \
  -Dgallium-drivers=svga,llvmpipe \
  '-Dvulkan-drivers=[]' \
  '-Dvulkan-layers=[]' \
  -Dplatforms=x11 \
  -Dglx=dri \
  -Dglx-direct=true \
  -Degl=enabled \
  -Dgbm=enabled \
  -Dglvnd=enabled \
  -Dopengl=true \
  -Dgles1=disabled \
  -Dgles2=disabled \
  -Dllvm=enabled \
  -Dshared-llvm=enabled \
  -Ddraw-use-llvm=true \
  -Dgallium-vdpau=disabled \
  -Dgallium-va=disabled \
  -Dgallium-rusticl=false \
  -Dgallium-mediafoundation=disabled \
  -Dgallium-d3d10umd=false \
  -Dmicrosoft-clc=disabled \
  -Dbuild-tests=false \
  '-Dtools=[]' \
  -Dhtml-docs=disabled \
  -Dlmsensors=disabled \
  -Dvalgrind=disabled \
  -Dlibunwind=disabled \
  -Dxlib-lease=disabled \
  -Dteflon=false \
  '-Dvideo-codecs=[]' \
  -Dzlib=enabled \
  -Dzstd=enabled \
  -Dxmlconfig=enabled
meson compile -C build -j 2
DESTDIR="$PWD/stage-unpatched" meson install -C build --no-rebuild
patch --directory=mesa-src --batch --forward -p1 --dry-run -i "$PWD/repository/patches/0001-svga-indexed-vertex-id-bias.patch"
patch --directory=mesa-src --batch --forward -p1 -i "$PWD/repository/patches/0001-svga-indexed-vertex-id-bias.patch"
meson compile -C build -j 2
DESTDIR="$PWD/stage-patched" meson install -C build --no-rebuild
```

Keep an unmodified source snapshot before applying the candidate. Only `src/gallium/drivers/svga/svga_pipe_draw.c` should change. Historical baseline file SHA256: `337cb4fa11ac9c965a4dd9e63e1472af851179ca72527047be47c9c163080d45`; patched: `2c7504896635b3afb953395e9e1a575830271cbea6accadae5428ecefdedb06a`. Publication verification applies the patch only to an isolated copy and compares those bytes; it does not compile Mesa.

Historical Gallium hashes are recorded for provenance, not promised as reproducible hashes on another compiler/path. Private GLX vendor selection and library-path staging are described in [reproduction.md](reproduction.md); establish the loaded-library identity in any independently approved reproduction. A wrong loader invalidates an A/B comparison.

A future build in the managed research VM needs separate scope: one fresh local Mesa source copy, exact verified Ubuntu patch stack, two builds with at most two build jobs, and private installation prefixes only; no driver loading, game, GL test or system install. Its global resource/deadline budget must be agreed before execution. None of that is part of this publication check.
