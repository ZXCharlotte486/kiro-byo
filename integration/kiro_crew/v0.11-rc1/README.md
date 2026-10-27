# KiroCrew 0.11.0-rc.1 exact-source adapter — limited candidate

This adapter targets only KiroCrew `0.11.0-rc.1` / `0.11.0rc1` and
**pins the exact Python source bytes** checked from the user-provided RC1 source
archive. It is not a generic adapter for all builds carrying the same version
string. Crew 0.10 is no longer an installation target.

## What was checked

- `20` modified Crew Python source seams and `1` new BYO ACP Harness file.
- `37` upstream Python source files in a read-only ZIP contract audit; exact
  hashes are required for each modified upstream source.
- Proposed patched Python source compiles; basic selectable-backend and routing
  registration was observed in an isolated source copy.
- On an isolated extracted Crew source copy, install, repeat install, and
  uninstall completed, with 20 original files byte-for-byte restored and the
  created BYO harness file removed.

## Important limitations

- This is **not** a Windows desktop installation or end-to-end Provider test.
  The uploaded Crew source ZIP does not contain the installed application's
  complete compiled frontend / runtime dependencies. A full Crew Harness import
  in the test container was blocked by absent `croniter` dependency.
- BYO main mode enforces a BYO effective member backend for new sessions in the
  RC1 config loader and member routing selector. Conflicting explicit official
  session overrides are refused instead of silently consuming official credits.
  Stored member preferences are not rewritten; switching to official recovers
  Crew defaults. The Mate 2.0 Conductor/Worker end-to-end path still requires
  real Windows verification, including any routes outside the shared selector.
- The Crew 0.11 compiled dashboard is intentionally left untouched: the old
  0.10-built HTML/model-picker injection is not known safe for the RC1 bundle.
  Consequently BYO-specific model filtering in Crew's compiled UI may differ.
- Exact source/hash mismatch rejects modification. Do not bypass that guard.
  This adapter does not migrate, clear, or overwrite Crew's user data.

## Read-only checks

```shell
PYTHONPATH=src python scripts/audit_crew11_rc1_zip.py /path/to/KiroCrew-0.11.0-rc.1.zip
PYTHONPATH=src python scripts/verify_crew11_integration.py --crew-package /path/to/KiroCrew/src/kiro_crew --crew-version 0.11.0-rc.1
```

A passing preflight authorizes an **isolated installation attempt only**; it is
not production certification. Back up Crew and user data before any real-world
installation test. Do not delete or relocate the data directory as a shortcut.
