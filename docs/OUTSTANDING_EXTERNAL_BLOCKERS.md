# Outstanding external blockers (2026-11-15)

Each item needs a person, a credential or a decision that the audit could not supply. Ordered by impact on the Global Award.

| # | Blocker | Why it matters | Smallest action that clears it | Owner |
|---|---|---|---|---|
| 1 | **NASA listed-resource requirement not demonstrated.** All NASA data come from NASA POWER, which is not on the challenge Resources list. No Giovanni (listed) data exist in the repository. | Global Award eligibility risk. | Get a free Earthdata token (https://urs.earthdata.nasa.gov/ then Generate Token), put `EARTHDATA_TOKEN=...` in a git-ignored `.env`, run `python3 -I scripts/fetch_giovanni_monthly.py`, then steps 8 to 10 of `docs/CHALLENGE_ELIGIBILITY.md` (checksums, `regenerate_all.py`, record the header). If the ingest guard refuses the API file, use the manual Giovanni web route in the same document. The script is untested against the live service with a token. Until `giovanni_*` files exist in `UI/data_real/`, nothing may claim the requirement is met. | Cason |
| 2 | **Ask an organizer whether NASA POWER counts.** | Could make blocker 1 moot, or confirm it is required. | One question to the Halifax organizer; record the answer and who gave it in `CHALLENGE_ELIGIBILITY.md`. | Ethan / Captain |
| 3 | **No public application URL.** | Judges must reach a running app. | Push the audit branch (commands in `docs/RELEASE_VERIFICATION.md`), then follow `submission/DEPLOYMENT.md` section 2 (Streamlit Community Cloud, main file `UI/frostline_app.py`, Python 3.12, set app to public). Open the URL in a private window before submitting it. | Shaurya / repo owner |
| 4 | **Push and merge need authorization.** | The repaired release exists only locally. | Captain approves; push `frostline-global-audit`, open a pull request into `main` (do not force-push). | Captain |
| 5 | **No statistical sign-off.** Includes the family choice for 2001-2024 road results (F1, q = 0.085, used by the app, versus F3, q = 0.018). | Results must stay labelled exploratory. | Reviewer reads `docs/SCIENTIFIC_METHODS.md` and `FINAL_GLOBAL_AWARD_AUDIT.md` F7 and records a decision. | Yao |
| 6 | **Project Submission Guide not read; submission links blank.** | Submission validity. | Read the guide; fill links in `submission/SUBMISSION_DRAFT.md` only after they work. | Ethan |
| 7 | AI-use disclosure has team placeholders (`[has / has not]`). | Required by the FAQ. | Team states which parts were AI-generated and which were human-verified. | Team |
| 8 | Route data questions: Aklavik alignment and segment, 4 flagged road rows, Dettah 2024 opening date one day off a press report. | Shown as caveats; do not block release. | Confirm with GNWT if possible; otherwise keep the caveats. | Cason |
| 9 | Screenshots and slides predate the audit caveats and map labels. | Minor inconsistency in static materials. | Re-shoot from the running app. | Louie |

Deadline: NASA project submission closes 2026-11-15 23:59 local time. Halifax: presentation intent 14:00, judging 15:00 Atlantic (team-reported).
