# factorio-vmware-svga-fix
Diagnosing and fixing Factorio coastline corruption on Linux guests using VMware SVGA: a Mesa patch, minimal reproducer, test evidence, and known remaining issues.

This research repository documents a verified **indexed vertex-ID bias correction** in Mesa's VMware SVGA driver and the defects that remain. The patch removed repeated shoreline spikes in a retained Factorio replay, but it is not a complete Factorio/VMware graphics fix.

## Findings

| ID | Result | Scope |
|---|---|---|
| SVGA-VID-001 | Verified in tested scope | Indexed draws must use base vertex, not index-buffer start, for the vertex-ID bias. Patched SVGA passed 180/180 baseline covered-pixel cases versus 57/180 unpatched. |
| FACTORIO-VIS-001 | Observed improvement | Large shoreline-region pixel differences versus software fell from 14221 to 88 in retained replay; residual differences remain. |
| SVGA-IND-001 | Unresolved | Indirect cases still fail, including uint8 indirect with no coverage in the fixed reduction. |
| SVGA-CLR-001 | Observed, unresolved | High unsigned RGBA32UI uploads pass, while high clears read back zero; low clears and software controls pass. |
| SVGA-CLR-HYP-001 | Untested hypothesis | Source uses signed clear-union values before a float SVGA command. No fix for this candidate has been implemented. |

[Structured findings](findings.json) link to accessible sanitized numeric evidence. [Data format](docs/data-format.md) documents stable IDs, statuses, oracles, limits and hashes. [Build provenance](evidence/build-provenance.json) records the exact Mesa source and dependencies; [environment](evidence/environment.json) records relevant sanitized versions.

## Patch and reproduction

- [Mesa patch](patches/0001-svga-indexed-vertex-id-bias.patch): indexed bias becomes base vertex; non-indexed bias retains first. Only one Mesa file changes.
- [Build instructions](docs/build.md): private staging only; no system-driver replacement.
- [Minimal reproducer and 180-case suite](reproducer/vertex_id.py), with [usage and limits](docs/reproduction.md). This standalone publication adaptation has not been GL-retested. Retained results came from its original fixture.
- [Safe non-GL verification](tests/test_publication.py): validates data/schema, checksums, links and historical numeric oracles without importing the GL fixture.

Read the [unsigned-clear source analysis](docs/unsigned-clear-candidate.md) before interpreting zero backgrounds. Baseline tuple success is not complete-image correctness. Zero **application** draws/compiles/links in the clear controls does not establish zero internal driver draws or shader work. Host renderer/capability changes were not a controlled single-variable experiment.

## Preservation and licensing

The explicit [artifact manifest](artifact-manifest.json) covers only reviewed source, documentation and sanitized records. No game assets/binaries, driver binaries, API traces, archives, private session logs, credentials or approval receipts are included. Original evidence is preserved separately; hashes of private artifacts identify evidence but are not public download links.

See [licensing and attribution](LICENSES/README.md). Mesa-derived patch material retains its MIT notice. Original test code and documentation use the root MIT license; upstream notices remain intact.
