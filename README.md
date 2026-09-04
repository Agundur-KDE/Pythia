# Pythia

Query Google Search Console performance data via a service account — no
third-party OAuth-consent MCP server, no browser login required once set up.
Includes an optional systemd timer for a recurring weekly report.

## Setup (from scratch, no Python experience needed)

You need Python 3 installed (`python3 --version` to check — most Linux
distros and macOS already have it; on Windows install it from
[python.org](https://www.python.org/downloads/)).

```bash
git clone <this-repo-url>
cd Pythia

# Create an isolated environment for this project's dependencies
# (this creates a venv/ folder here — it's not part of the repo, that's normal)
python3 -m venv venv

# Install the two required packages into that environment
venv/bin/pip install -r requirements.txt
```

## Get a service account key

1. In the [Google Cloud Console](https://console.cloud.google.com), create a
   project and enable the **Google Search Console API**.
2. Under **IAM & Admin -> Service Accounts**, create a service account (skip
   the optional "grant access" steps).
3. Open the service account -> **Keys** tab -> **Add Key** -> **Create new
   key** -> JSON. This downloads a `.json` file.
4. Save that file as `service-account.json` in this same folder (it's
   gitignored, so it will never accidentally get committed).
5. Copy the service account's email address (ends in
   `...iam.gserviceaccount.com`) and add it as a user in
   **Search Console -> Settings -> Users and permissions** for the site you
   want to query. "Restricted" (read-only) permission is enough.

## Run it

```bash
venv/bin/python query.py "https://www.example.com/" --days 7 --dimensions page --limit 25
```

- `sc-domain:example.com` for a Domain property, or `https://www.example.com/`
  (with the trailing slash) for a URL-prefix property — use whichever
  matches how your property is set up in Search Console.
- `--dimensions` accepts a comma-separated list: `query,page,country,device,date`

If something's missing (dependencies, the key file, permissions), the script
tells you in plain English what to fix instead of a Python traceback.

## Recurring weekly report (optional)

`weekly-report.sh` + the two systemd unit files run this on a schedule and
write a markdown report. See the comments in `search-console-weekly.service`
for the `SITE_URL` and path you need to fill in, then:

```bash
mkdir -p ~/.config/systemd/user
cp search-console-weekly.service search-console-weekly.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now search-console-weekly.timer
```

Check it's scheduled with `systemctl --user list-timers`.
