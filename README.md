# Meta test-user provisioning

Creates a requested number of **test users** for your own Meta app through the
official Graph API and records each one (name, id, email, password, login URL)
in an Excel tracker. Test users are sandboxed accounts that Meta provides for
testing an app; they cannot interact with real users.

## Setup

1. Create an app at <https://developers.facebook.com/apps> and note its App ID
   and App Secret.
2. In the GitHub repository, add the secrets `META_APP_ID` and
   `META_APP_SECRET` (Settings → Secrets and variables → Actions).
3. Optional: add a repository variable `META_GRAPH_VERSION` (e.g. `v24.0`) to
   pin the Graph API version. Unset, Meta picks the app's default version.

## Use from GitHub Actions

Actions → **Create test users** → Run workflow → enter the number of users.
The run uploads `test_users.xlsx` as an artifact (kept 14 days).

## Use locally

```bash
pip install -r requirements.txt
export META_APP_ID=... META_APP_SECRET=...
python -m testusers.cli create --count 5
python -m testusers.cli list
python -m testusers.cli delete --all
```

Locally the tracker is appended to on every run, so it holds every user ever
created, and names already used are never reused. Deleted users stay in the
sheet with status `deleted`.

## Limits to know about

- Each CI run starts from a fresh checkout, so its artifact lists only the
  users created in that run. `list` shows every test user the app has.
- Meta caps the number of test users per app and has at times disabled
  test-user creation; the tool then stops, reports Meta's error, and still
  saves the users it did create.
- Test users are Facebook-side accounts. Instagram has no API for creating
  test accounts: to test Instagram features, add an Instagram account you own
  as a tester under App roles in the app dashboard.
- The tracker contains credentials. `*.xlsx` is git-ignored; keep the repo
  private if you rely on workflow artifacts.

## Instagram posting bot

`igbot` posts a picture to an Instagram account you own, through the official
content publishing API.

Requirements:

- An Instagram **professional** (Business or Creator) account.
- A Meta app with the Instagram product, and a long-lived access token for
  that account with the `instagram_business_content_publish` permission.
- The picture must be a JPEG at a public HTTPS URL; Instagram downloads it.

```bash
export IG_USER_ID=... IG_ACCESS_TOKEN=...
python -m igbot.cli --image-url https://example.com/photo.jpg --caption "Hello"
```

From GitHub: add the secrets `IG_USER_ID` and `IG_ACCESS_TOKEN`, then run
Actions → **Post photo to Instagram**. If your token comes from Facebook Login
rather than Instagram Login, set the variable `IG_API_BASE` to
`https://graph.facebook.com`.

Long-lived tokens expire after 60 days unless refreshed, and Instagram limits
API publishing to 100 posts per 24 hours.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```
