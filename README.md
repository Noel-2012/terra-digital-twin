# TERRA — Planetary Digital Twin (Concept)

A single-page concept UI exploring the idea from the "Earth-system digital twin" write-up: a
software model that combines physics, satellites, and AI into one continuously self-correcting
representation of Earth, instead of dozens of siloed domain models.

**This is a design/UX concept, not a working scientific model.** There's no real satellite feed,
no physics engine, no AI backend — the "simulation readouts" are scripted, illustrative text.
The point is to make the *idea* (and the gap it's pointing at) tangible and explorable.

## What's inside

- **Hero** — an animated cross-section diagram (space/satellites → atmosphere → ocean/land →
  core) with orbiting nodes and pulsing "assimilation" threads, representing the convergence the
  source material describes.
- **System layers** — the compartmentalized models that exist today (ECMWF IFS, GraphCast, NEMO,
  CLM, GEOS-Chem, etc.), each with a one-line note on where it fits and its limits.
- **Scenario console** — pick or type a "what happens if X" scenario and get a scripted,
  clearly-labeled illustrative trace across atmosphere/ocean/land coupling.
- **Frontier ranking** — the five-tier ranking from the source material, most-mature to
  most-speculative.

## Run it locally

It's a single static HTML file — no build step, no dependencies.

```bash
open index.html        # macOS
xdg-open index.html    # Linux
start index.html       # Windows
```

Or serve it:

```bash
python3 -m http.server 8000
# then visit http://localhost:8000
```

## Push to your GitHub

I don't have write access to your GitHub account, so create the repo yourself and push this
folder:

```bash
cd terra-digital-twin
git init
git add .
git commit -m "feat: initial TERRA digital twin concept"
git branch -M main
git remote add origin https://github.com/<your-username>/terra-digital-twin.git
git push -u origin main
```

(Create the empty repo on GitHub first — via the web UI, or `gh repo create terra-digital-twin
--public --source=. --remote=origin` if you have the GitHub CLI installed.)

### Free hosting once it's pushed

GitHub Pages works well for this since it's static:
Settings → Pages → Deploy from branch → `main` / `/ (root)`.

## Credits / real-world references

The layers and ranking are drawn from real, ongoing efforts referenced in the source material:

- **Destination Earth (DestinE)** — ECMWF, ESA, EUMETSAT
- **NVIDIA Earth-2**
- **Google DeepMind GraphCast / GenCast**
- **ESA Digital Twin Earth**

None of their data or branding is used here — this is an independent concept design.
