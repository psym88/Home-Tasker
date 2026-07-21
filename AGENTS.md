# Repository Instructions

- Release notes and `CHANGELOG.md` entries must always be written in English, regardless of the language used by the frontend.
- Keep the versions in `manifest.json`, `const.py`, and `frontend/panel.js` aligned for every release.
- Update `README.md`, `ARCHITECTURE.md`, and the changelog whenever user-visible behavior changes.
- Add or update focused tests for recurrence changes and important regression fixes.
- Perform all development work on the `dev` branch. Before editing, switch to `dev` and update it from `origin/dev`; do not commit feature or fix work directly to `main`.
- Publish every new version from `dev` as a GitHub pre-release first, using the tag format `vX.Y.Z` and the exact version stored in the source files.
- Do not mark a pre-release as the latest release.
- Create a final release only when the user explicitly instructs you to create a new final release. First integrate the tested `dev` changes into `main` and push `main`, then publish the normal/latest GitHub release from `main`.
- Reuse the tested pre-release's existing commit, tag, and GitHub release when promoting it to final; never create a different tag for identical release contents.
- Final release notes must summarize all changes and fixes since the previous final release, including every intervening pre-release, rather than only the most recent commit or pre-release.
- Never move, overwrite, or reuse a published tag. If testing fails, create a fix pull request and publish a new patch version as a new pre-release.
