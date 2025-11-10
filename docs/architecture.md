# Abstract Data Organization Profile Architecture

## Repository Topology
- `profile/README.md` renders the organization landing experience. It is the only file GitHub reads for the profile page.
- `assets/` houses animated SVG headers, dividers, badge artwork, and any future motion graphics referenced from the profile.
- `scripts/` contains automation utilities used by scheduled workflows to keep metrics and badges current.
- `.github/workflows/` orchestrates scheduled maintenance via GitHub Actions.
- `docs/` (this directory) stores operational documentation for Abstract Data maintainers.

## Visual System
- **Palette:** `#AC2D21` (primary red), `#E7AE59` (gold accent), `#0A0E27` (command deck background), `#11183C` (secondary depth), `#FFFFFF` (contrast text).
- **Typography:** Prioritize `Fira Code`, `JetBrains Mono`, or `IBM Plex Mono`. Fall back to system monospace fonts only when necessary.
- **Animations:** SVG keyframes drive glows, pulses, and scanlines. Keep cycles between 3‑5 seconds for subtlety and accessibility. Avoid JavaScript in profile/README.md—GitHub blocks it.

## Automation Workflows
- `update-profile.yml`
  - Runs daily at 09:00 UTC and on demand.
  - Generates `profile/stats.json` via `scripts/generate-stats.js`, which pulls live metrics from the GitHub API using the repository’s `GITHUB_TOKEN`.
  - Executes markdown linting and validates that every referenced asset exists.
  - Commits updates only when the stats payload changes.
- `badge-generator.yml`
  - Runs weekly on Mondays, on manual dispatch, and on new releases.
  - Executes `scripts/generate-badges.js` when present; otherwise verifies existing badge assets.
  - Commits updated SVG badges under `assets/badges/` when changes are detected.

## Stats Generation (`scripts/generate-stats.js`)
- Resolves the output path (`profile/stats.json`) and ensures the directory exists.
- Calls the GitHub REST API to gather organization metadata:
  - Repository counts (public + private)
  - Followers and public members
  - Aggregate stars and forks
  - The most recently pushed repository and timestamp
- Emits structured JSON consumed by downstream tooling or future UI enhancements.
- Handles API failures gracefully by logging a warning and emitting zeroed metrics.

## Badge and Asset Guidelines
- Prefer shields.io for lightweight badges that need to display dynamic numbers or vendor logos.
- Store custom SVGs in `assets/badges/`; keep file sizes under 100 KB for fast loading.
- When introducing new animated assets, test in Chromium and Safari to verify animation compatibility.
- Reference assets from `profile/README.md` using relative paths (`../assets/...`) so GitHub resolves them correctly.

## Update Checklist
1. Preview `profile/README.md` in GitHub or a markdown renderer to confirm layout.
2. Run `node scripts/generate-stats.js` locally (or via the scheduled workflow) to verify API credentials and payload shape.
3. If new dependencies are required for scripts, document them and update workflows accordingly.
4. Ensure new sections maintain the command-deck aesthetic: dark backgrounds, glowing accents, and accessible contrast.
5. Keep automation credentials scoped to `GITHUB_TOKEN`; secrets beyond that must be approved by Abstract Data operations.

Maintainers should treat this repository as production-facing infrastructure. Ship iteratively, keep the automation flowing, and preserve the premium neural-command visual identity. 

