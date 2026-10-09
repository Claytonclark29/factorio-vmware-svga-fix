# Minimal vertex-ID reproducer and regression suite

`reproducer/vertex_id.py` is a standalone adaptation of the retained 180-case GLX fixture. It uses Python 3 standard-library ctypes/struct plus runtime libX11.so.6/libGL.so.1; no game asset or trace is needed. Requires an existing X display and GL 4 context supporting the entrypoints used by the original fixture. No GL context opens when importing the module or displaying help; rendering requires `--execute-rendering`.

The minimal selection is **one indexed draw**, uint16 indices `[0,1,2,2,1,3]`, index start 17 elements (34 bytes), base vertex 0, last provoking vertex. The shader compares `gl_VertexID` with an explicit unsigned vertex attribute. Expected covered-pixel IDs are 2 and 3; the retained unpatched SVGA result was 19 and 20 (exactly +17), while patched SVGA/software were 2 and 3. This reproduces the bias defect without Factorio.

`--suite regression` selects the original 180 application draws: widths 1/2/4 bytes, starts including 14994, base vertex 0/+5/-5 with valid effective indices, nonmonotonic indices, first/last provoking vertices, array first, instancing/base instance and state transitions. One context, two application shader compilations, one program link. Each case clears once, draws once, finishes once and reads one 64x64 RGBA32UI attachment. The minimal selection uses the same setup but one case.

The oracle compares covered-pixel tuples, identifying coverage by alpha. It does not assert the full background image or exact coverage count. The original high unsigned sentinel remains deliberately unchanged: a baseline pass must not be mistaken for a successful high-value clear. Clear-specific evidence lives in [unsigned-clear.json](../evidence/unsigned-clear.json). No indirect command is exercised by this standalone baseline suite.

Example **future rendering commands**, not run during publication:

```bash
stage="$PWD/stage-patched"
lib="$stage/usr/lib/x86_64-linux-gnu"
# Keep DISPLAY from the actual authorized session. Clear unrelated overrides first.
env -u LD_PRELOAD -u MESA_LOADER_DRIVER_OVERRIDE -u LIBGL_ALWAYS_SOFTWARE -u GALLIUM_DRIVER \
  LD_LIBRARY_PATH="$lib" LIBGL_DRIVERS_PATH="$lib/dri" \
  __GLX_VENDOR_LIBRARY_NAME=mesa MESA_SHADER_CACHE_DISABLE=true \
  timeout --signal=TERM --kill-after=5s 30s \
  python3 -B repository/reproducer/vertex_id.py --execute-rendering --suite minimal --expect-renderer SVGA
```

For a separately approved software control, use the same staged libraries with `LIBGL_ALWAYS_SOFTWARE=true GALLIUM_DRIVER=llvmpipe` and `--expect-renderer llvmpipe`. For the full baseline, change only `--suite regression`. Use an external owned-process timeout; this standalone fixture is not the research journal/controller. No automatic retry, supervisor, process inspection or host access is built in. On abnormal exit, explicit GL cleanup may not finish; process teardown is not a driver-hang guarantee. Capture stdout/stderr to a new local destination only if desired.

Publication changes remove private checkpoint/mapping exports, use standard sonames, add a main/consent guard and minimal selector, retain the rendering body/oracle, and return nonzero for failed cases. These changes were syntax/static checked only; **no GL rerun validates the adapted script**. Retained evidence came from the original fixture, whose source hash is privately mapped. Confirm actual library mapping separately before relying on a new result.

Safe publication checks (no fixture import, GL, children or build):

```bash
python3 -B tests/test_publication.py
```

They require the already available `jsonschema` Python package for Draft2020-12 validation; no automatic dependency installation occurs.
