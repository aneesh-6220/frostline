# Deploying Frostline

Status: **not deployed.** No public URL exists yet. Do not write one into the submission until someone has opened it in a private browser window.

Current facts (checked 2026-11-15, 11:55 Atlantic): the repository is **`aneesh-6220/frostline`** (renamed from `nasa-space-apps-2026`; GitHub redirects the old name) and it is **public**. Branch `frostline-map-giovanni-release` (`fe04f73`, 198 tests passing) is already pushed and can be deployed now. The final-qualification branch `frostline-final-qualification` (204 tests, landing/demo/map fixes, team documents) is local only; pushing it, or fast-forwarding the deployed branch to it, needs the Captain's approval. The app needs no secrets: NASA POWER needs no key, Giovanni data are committed files, and the map tiles need no key.

## Fastest path (about 7 minutes, needs the repository owner's GitHub login)

1. https://share.streamlit.io, sign in with GitHub, **Create app**, **Deploy a public app from GitHub**.
2. Repository `aneesh-6220/frostline`, branch `frostline-map-giovanni-release` (or the approved final branch), main file path `UI/frostline_app.py`.
3. Advanced settings: Python **3.12**. No secrets.
4. Deploy, then set sharing to public and run the checklist in section 3 from a private window.
5. To ship later approved commits: `git push origin frostline-final-qualification:frostline-map-giovanni-release` (a fast-forward; never force-push). Streamlit redeploys on push.

The sections below are the earlier, longer instructions; where they name the old repository or say it is private, the facts above take precedence.

## 1. Push the branch (about 2 minutes, needs a GitHub login with write access)

```bash
cd "<path to the repository>"
gh auth login                                   # or use any configured git credential
git fetch origin                                # confirm nothing newer than 4fefedc is on fable-ready
git log --oneline origin/fable-ready -3
git push -u origin frostline-implementation
```

If `fable-ready` has moved, merge it into `frostline-implementation`, rerun the two verification commands at the end of this file, then push. Never force-push.

## 2. Create the app on Streamlit Community Cloud (about 5 minutes, needs the repository owner's GitHub OAuth)

1. Sign in at https://share.streamlit.io with a GitHub account that can read the private repository, and grant access to it when asked.
2. Create app, then "Deploy a public app from GitHub".
3. Repository `aneesh-6220/nasa-space-apps-2026`, branch `frostline-implementation`, main file path `UI/frostline_app.py`.
4. Advanced settings: Python version **3.12**. No secrets are needed. The app reads `UI/requirements.txt` and `.streamlit/config.toml` from the repository.
5. Deploy. After the build, open Settings, Sharing, and set the app to **public** ("This app is public and searchable" or the equivalent), so judges do not need to log in. A private repository does not prevent a public app.

Alternative hosts (Render, Hugging Face Spaces with the Streamlit SDK, a university server) work with the same two settings: start command `streamlit run UI/frostline_app.py --server.port $PORT --server.address 0.0.0.0` and Python 3.12.

## 3. Verify before sharing the link

Open the URL in a private or logged-out browser window and check:

- the Observatory loads with a chart and four indicators, with no login prompt;
- Begin an Investigation runs through all six demo stages and the Evidence Brief downloads;
- the sidebar shows "Data digest a1f1cd6387875487" (approved data plus the Giovanni files at the release-candidate commit);
- Map shows the Esri basemap with place labels and two coloured case-study markers; clicking an empty spot inside the dashed area selects a white-ringed point, and "Retrieve NASA POWER daily data for this point" returns a trend, a chart and a downloadable Evidence Brief (needs outbound HTTPS to power.larc.nasa.gov from the host);
- Giovanni record shows 1980 to 2025 monthly data with a trend, and its Evidence Brief downloads.

Then record the URL in `submission/SUBMISSION_DRAFT.md` and in the slide deck.

## 4. Fallback for local judging

If hosting is not ready, run the app on the presenter's laptop. It needs no internet connection except for the optional map background and web fonts.

```bash
pip install -r UI/requirements.txt     # Python 3.12
streamlit run UI/frostline_app.py      # from the repository root
```

Static fallbacks that need nothing at all: `submission/frostline_slides.pdf`, the images in `submission/screenshots/` and `submission/sample_evidence_brief_dettah_opening_day.html`.

## Verification commands

```bash
python3 -I -m unittest discover -s tests          # expect 198 tests, OK
python3 -I scripts/regenerate_all.py --check      # expect "regeneration is a no-op"
```

## Release candidate 2026-11-15 (map, Giovanni, live NASA POWER)

Push and deploy only with the Captain's authorization:

```bash
git push -u origin frostline-map-giovanni-release
# Streamlit Community Cloud: repository aneesh-6220/nasa-space-apps-2026, branch frostline-map-giovanni-release
# (or main after a reviewed merge), main file UI/frostline_app.py, Python 3.12, no secrets; then set the app to public.
```

New runtime dependencies (pinned in `UI/requirements.txt`): folium 1.0.0, streamlit-folium 0.27.4, branca 0.8.2, xyzservices 2026.9.1. `requirements-dev.txt` adds h5py for the offline NetCDF check only.

If the host blocks outbound requests or NASA POWER is down, the Map view shows the error and the curated case studies, guided demo, Giovanni record and all briefs keep working from committed files.
