## Fix Light Mode Contrast

**Date:** 2026-05-30
**Files changed:** `frontend/style.css`, `frontend/index.html`, `run.sh`
**Summary:** Light mode UI components were nearly invisible due to near-identical background/surface/border colours (`#f8fafc`/`#ffffff`/`#e2e8f0`). Fixed by darkening `--background` to `#e8eef4`, increasing `--border-color` to `#94a3b8` (slate-400), and adding an explicit border on assistant message bubbles in light mode. Also bumped the CSS cache-bust version and updated `run.sh` to pick a random free port so the worktree server doesn't clash with the main dev server on 1234.

## Dark/Light Mode Toggle Button
**Date:** 2026-05-30  
**Files changed:** `frontend/index.html`, `frontend/style.css`, `frontend/script.js`  
**Summary:** Added a fixed-position circular icon button in the top-right corner that toggles between dark and light themes. The button uses animated sun/moon SVG icons with a smooth CSS transition (opacity + rotate/scale), persists the preference in `localStorage`, and is fully keyboard-navigable with a `:focus-visible` ring.
