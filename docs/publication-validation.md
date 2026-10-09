# Publication validation

Performed without a rendering run, fixture import, driver loading, Mesa rebuild or system installation:

- All six non-GL repository tests passed: findings schema/links, allowlist/hashes/JSON, historical baseline oracle, clear histograms, indirect-failure retention and fixture AST guard checks.
- The patch passed `git apply --check` on an isolated copy of the exact baseline file. Applying it to that copy produced bytes identical to the retained verified patched file. Original Mesa sources were untouched.
- The explicit publication allowlist was scanned for private machine/user paths, message references, email addresses, credential-like strings and disallowed binaries/archives. A private source mapping and source-retention checks live outside this tree.
- This standalone reproducer was syntax checked, not imported or GL-run after adaptation. Build instructions were transcribed from retained configuration, not executed again.

The local clean tree contains no Git metadata. Existing history and the connected account's normal commit identity are approved; final remote commit verification remains separate. The artifact manifest binds this exact file set; no claim of remote publication is made by this record.
