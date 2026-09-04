# Pythia

Query Google Search Console performance data via a service account — no
third-party OAuth-consent MCP server, no browser login required once set up.
Includes an optional systemd timer for a recurring weekly report.

## Setup (from scratch, no Python experience needed)

Linux and macOS — the commands below work as-is (Windows users: use WSL and
follow the same Linux steps, there's no native Windows path documented here).

You need Python 3 installed (`python3 --version` to check — most Linux
distros and macOS already have it).

```bash
git clone https://github.com/Agundur-KDE/Pythia.git
cd Pythia

# Create an isolated environment for this project's dependencies
# (this creates a venv/ folder here — it's not part of the repo, that's normal)
python3 -m venv venv
```

If that fails with something like `ensurepip is not available`, your distro
ships `venv` as a separate package — e.g. on Debian/Ubuntu:
`sudo apt install python3-venv`, then retry.

```bash
# Install the required packages into that environment
venv/bin/pip install -r requirements.txt
```

## Get a service account key

1. In the [Google Cloud Console](https://console.cloud.google.com), create a
   project and enable the **Google Search Console API**.
2. Under **IAM & Admin -> Service Accounts**, create a service account (skip
   the optional "grant access" steps).
3. Open the service account -> **Keys** tab -> **Add Key** -> **Create new
   key** -> JSON. This downloads a `.json` file.
4. Save that file somewhere **outside** this folder — e.g.
   `~/.config/google-search-console/service-account.json` — and symlink it
   in instead of copying it here:
   ```bash
   ln -s ~/.config/google-search-console/service-account.json service-account.json
   ```
   `.gitignore` matches by filename, so it treats a symlink the same as a
   real file — but a symlink is strictly safer: even in a worst case like
   `git add -f`, Git stores a symlink as just the target *path* it points
   to, never the file's actual content. So an accidental force-add would at
   most leak a local path, not your key. Placing the real key directly in
   this folder works too and is still gitignored, just without that extra
   safety margin.
5. Copy the service account's email address (ends in
   `...iam.gserviceaccount.com`) and add it as a user in
   **Search Console -> Settings -> Users and permissions** for the site you
   want to query. "Restricted" (read-only) permission is enough.

**Note on `.gitignore`:** it excludes `service-account.json` and a few common
secret-file names/patterns by name — it does **not** protect a key saved
under a different filename, and `git add -f` bypasses it entirely. Treat it
as a safety net, not a guarantee.

## Run it

```bash
venv/bin/python query.py "https://www.example.com/" --days 7 --dimensions page --limit 25
```

- `sc-domain:example.com` for a Domain property, or `https://www.example.com/`
  (with the trailing slash) for a URL-prefix property — use whichever
  matches how your property is set up in Search Console.
- `--dimensions` accepts a comma-separated list: `query,page,country,device,date,searchAppearance`
- `--days N` covers N+1 calendar days (both start and end date inclusive),
  and Search Console data usually lags 1-3 days behind today.

If something's missing (dependencies, the key file, permissions, an unknown
dimension), the script tells you in plain English what to fix instead of a
Python traceback.

## Recurring weekly report (optional)

`weekly-report.sh` + the two systemd unit files run this on a schedule and
write a markdown report to `~/search-console-reports/`.

**Extra requirement for this part only:** the [Claude Code CLI](https://claude.com/claude-code)
(`claude`), installed and logged in — the script uses it to analyze the
query results and write the report. Desktop notifications need an active
desktop session (they're skipped silently otherwise, e.g. under a headless
server).

**Security note:** this script gives Claude Bash and Write access, scoped to
this folder and the report directory, and feeds it search-query text that
ultimately comes from whoever searched Google for your site — not data you
control. That's a low but non-zero prompt-injection surface. Fine for
personal/self-hosted use on your own machine; don't run it with broader tool
access than the two flags shown above.

Before installing, edit `search-console-weekly.service`:
- `SITE_URL` — your property, same syntax as above
- `ExecStart` — the absolute path to `weekly-report.sh` in your clone

```bash
mkdir -p ~/.config/systemd/user
cp search-console-weekly.service search-console-weekly.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now search-console-weekly.timer
```

Check it's scheduled with `systemctl --user list-timers`. If your user isn't
normally logged in when the timer should fire (e.g. a server), enable
lingering so the timer runs anyway: `loginctl enable-linger $USER`.

### Troubleshooting the timer

- Test the script manually first: `SITE_URL="https://www.example.com/" ./weekly-report.sh`
- `systemctl --user status search-console-weekly.timer` — is it scheduled?
- `journalctl --user -u search-console-weekly.service` — what happened on the last run?
- No report file appears: check the journal output above for the actual error
  from `claude` or from `query.py`.
