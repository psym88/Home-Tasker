# Repository Instructions

- Release notes and `CHANGELOG.md` entries must always be written in English, regardless of the language used by the frontend.
- Keep the versions in `manifest.json`, `const.py`, and `frontend/panel.js` aligned for every release.
- Update `README.md`, `ARCHITECTURE.md`, and the changelog whenever user-visible behavior changes.
- Add or update focused tests for recurrence changes and important regression fixes.
- Publish every new version as a GitHub pre-release first, using the tag format `vX.Y.Z` and the exact version stored in the source files.
- Do not mark a pre-release as the latest release.
- Promote the same GitHub release and tag to a final/latest release only after the user explicitly confirms successful testing.
- Never move, overwrite, or reuse a published tag. If testing fails, create a fix pull request and publish a new patch version as a new pre-release.
