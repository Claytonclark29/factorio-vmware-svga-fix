# SVGA-CLR-HYP-001: untested unsigned-clear hypothesis

This is a source-backed candidate, not a verified fix. No candidate patch, instrumentation, rebuild or new GL test has been performed.

In Mesa 25.2.8, `src/mesa/main/clear.c:465` (`clear_bufferuiv`) copies GLuint values to `ClearColor.ui`; `src/mesa/state_tracker/st_cb_clear.c:506` passes the union to `pipe->clear`. Both union layouts contain float, signed-int and unsigned-int arrays (`src/mesa/main/mtypes.h:226`, `src/util/format/u_formats.h:671`). Full write masks/no applicable scissor select the direct clear path; other state can select an internal quad.

`src/gallium/drivers/svga/svga_pipe_clear.c:75` detects an integer target without signed/unsigned distinction. At line97, `ints_fit_in_floats` only checks signed `color->i[n] <= 1<<24`. At line158, `try_clear` uses that result, then casts `color->i[n]` to float. On the tested platform, FFFFFFFF has signed value -1, passes the test, and predicts RGB floats -1.0 (bits BF800000). Small positive integers predict their correct positive floats. The check also lacks a negative precision bound. A fix would need format-aware eligibility and conversion, not merely one changed cast.

At `src/gallium/drivers/svga/svga_cmd_vgpu10.c:288`, `SVGA3D_vgpu10_ClearRenderTargetView` copies the floats to `cmd->rgba.value` and commits `SVGA_3D_CMD_DX_CLEAR_RENDERTARGET_VIEW`; `include/svga3d_dx.h:565` defines the float payload. The UINT format remains UINT in `svga_format.c:162`. The available source ends at guest command emission; the proprietary host renderer's conversion was not inspected.

The relevant API/state-tracker/SVGA clear and command files match the retained unpatched source byte-for-byte. The verified local vertex-ID patch affects only `svga_pipe_draw.c`.

Upload contrast: matching-format non-PBO `st_TexSubImage` (`st_cb_texture.c:2169`) uses `texture_subdata`; SVGA installs `u_default_texture_subdata` (`svga_resource.c:128`), which maps and byte-copies (`u_transfer.c:74`). SVGA then updates/transfers storage. This avoids the clear-color conversion; the exact live upload branch was not instrumented.

Alternatives: values failing the eligibility test take an internal quad (`svga_pipe_clear.c:55`); masks/scissor can select a state-tracker quad. The earlier `util_pack_color(color->f,...)` result feeds the legacy command path, not this VGPU10 payload. Its presence is not evidence that NaN conversion caused this result. Zero application draws does not exclude internal driver drawing/shaders. The two read APIs can share implementation; fixed order remains a limitation.

One possible future discriminator, requiring separate agreement: a single instrumented SVGA context/attachment with marker reseeding and one low plus one high clear, recording API union bits, selected branch and emitted float bits. Proposed image budget: two uploads, two clears, four readbacks, two Finish calls; no application draw/shader/link. H should emit -1.0 RGB under this candidate; a quad path, earlier corruption or different payload falsifies that path explanation. Correct command values followed by wrong pixels shift investigation downstream. This is a proposal only, not implemented or authorized here.

See [clear evidence](../evidence/unsigned-clear.json) and [source provenance](../evidence/build-provenance.json). Upstream source: https://gitlab.freedesktop.org/mesa/mesa/-/tree/mesa-25.2.8 (the measured build additionally used the listed Ubuntu patches).
