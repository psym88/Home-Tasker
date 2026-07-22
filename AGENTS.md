# Repository Instructions

- Write GitHub release notes in English. GitHub Releases are the only changelog; do not add a repository changelog.
- Keep versions aligned in `manifest.json`, `const.py`, and `frontend/panel.js`.
- Keep `README.md` user-focused; update it only for installation or usage changes. Document only stable contracts and component boundaries in `ARCHITECTURE.md`, never styling tweaks or release history.
- Add focused tests for recurrence changes and important regressions.
- Work on `dev` and update it from `origin/dev` before editing. Do not commit feature or fix work directly to `main`.
- Publish each new `dev` version first as a GitHub pre-release tagged `vX.Y.Z`; it must not be latest.
- Create a final release only when explicitly requested. Integrate the tested commit into `main`, reuse its existing tag and GitHub release, and summarize all changes since the previous final release.
- Never move, overwrite, or reuse a published tag. If testing fails, fix it and publish a new patch version and pre-release.
