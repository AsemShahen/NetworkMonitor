# Submit Network Monitor to AppImageHub

AppImageHub is a catalog, not a download host. It links to the upstream
repository and tests the newest AppImage from its GitHub Releases page.

## One-file pull request

1. Fork <https://github.com/AppImage/appimage.github.io>.
2. Add exactly one file at `data/Network_Monitor` with this content:

   ```text
   https://github.com/AsemShahen/NetworkMonitor
   ```

   The ready-to-copy file is
   [`Network_Monitor`](Network_Monitor) in this directory. If you already have
   a clone of the catalog, apply [`Network_Monitor.patch`](Network_Monitor.patch)
   with `git apply Network_Monitor.patch`.
3. Commit and push the branch to your fork.
4. Open a pull request against `AppImage/appimage.github.io:master` titled
   `Add Network_Monitor`.
5. The pull request must change **only** `data/Network_Monitor`; the automated
   test fails if it contains any other change.
6. Watch the automated comment. It downloads the newest release AppImage,
   starts it on Xvfb without network access, and captures a screenshot. If it
   asks for a retest, comment `/retest`.

## Notes for this application

- The default interface is English; Arabic is optional. This matches the
  catalog's language policy.
- The app reads `/proc` and can show its main window without an Internet
  connection.
- The catalog may warn that the default theme is dark. That is a warning, not a
  failure.
- The AppImage targets glibc 2.34+; the oldest supported Ubuntu LTS is newer
  than that, so it should pass the glibc check.
- Prefer the repository URL over a direct `.AppImage` URL. Use the direct URL
  only if the test picks the wrong release asset.

## Automated helper

If you already have a fork, [`submit.sh`](submit.sh) clones it, adds the one
file, commits, pushes a branch, and prints the compare URL. It never changes
the upstream repository directly.

```bash
GITHUB_USER=your-github-user ./packaging/appimagehub/submit.sh
```
