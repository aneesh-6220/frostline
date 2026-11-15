# Deploying Frostline

Status: **not deployed.** The machine used for the build has no GitHub credentials, so the implementation branch could not be pushed and no hosted application could be created or checked. No public URL exists yet. Do not write one into the submission until someone has opened it in a private browser window.

The repository stays private. Changing its visibility is the Captain's decision and is not needed for deployment.

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
- the sidebar shows "Data digest 7037c7be7383fe25" (the approved data at this commit);
- Atlas shows two markers (the dark background map needs internet; the location list works without it).

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
python3 -I -m unittest discover -s tests          # expect 150 or more tests, OK
python3 -I scripts/regenerate_all.py --check      # expect "regeneration is a no-op"
```
