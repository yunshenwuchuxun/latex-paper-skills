# Distribution and publishing

The public package is `skills/latex-paper-skills/`, version **0.1.0**. It contains
all eight source workflows, shared Python helpers, and templates. Nested
`SKILL.md` files become `workflow.md` to keep the installable package a single
skill. Source files remain under `.codex/skills/`.

Published releases:

| Channel | Published version | Page |
| --- | --- | --- |
| npm | `0.1.0` | [latex-paper-skills](https://www.npmjs.com/package/latex-paper-skills) |
| GitHub Release | `v0.1.0` | [Release and ZIP](https://github.com/yunshenwuchuxun/latex-paper-skills/releases/tag/v0.1.0) |
| ClawHub bundle plugin | `0.1.0` | [LaTeX Paper Skills](https://clawhub.ai/yunshenwuchuxun/plugins/latex-paper-skills) |
| LobeHub | Listing `1.0.2`, suite contents `0.1.0` | [LaTeX Paper Skills](https://lobehub.com/skills/yunshenwuchuxun-latex-paper-skills) |

## Build and verify

```bash
python3 scripts/build_distribution.py --archive
python3 scripts/build_distribution.py --check
```

The ZIP at `dist/latex-paper-skills-0.1.0.zip` has `SKILL.md` at its root, with
no showcase projects, datasets, local configuration, or Python cache files.
Commit the generated `skills/latex-paper-skills/` directory along with any
source changes so GitHub installers receive the same tested contents.

## GitHub installation and skills.sh

```bash
npx skills@latest add yunshenwuchuxun/latex-paper-skills --skill latex-paper-skills
```

The `skills` npm CLI installs the skill directly from GitHub. Per the
[skills.sh FAQ](https://skills.sh/docs/faq), the leaderboard tracks
real installations through CLI telemetry; there is no separate registry upload
step. Listing/indexing timing is controlled by skills.sh.

For a local verification without changing global skills:

```bash
npx skills@latest add /absolute/path/to/skills/latex-paper-skills --agent codex --copy --yes
```

Run this in a temporary test project.

## Platform licenses

The source bundle retains the repository's MIT license. `IEEEtran.cls` retains
its LPPL 1.3 license and source notices. Platform uploads must preserve both;
the entire bundle cannot be labelled MIT-0. See `THIRD_PARTY_NOTICES.md`.

## ClawHub / OpenClaw

Install the published bundle with:

```bash
openclaw plugins install clawhub:@yunshenwuchuxun/latex-paper-skills
```

Append `@0.1.0` to pin the first version. The explicit `clawhub:` prefix selects
ClawHub instead of npm; see [OpenClaw plugin installation](https://docs.openclaw.ai/cli/plugins/install#sources-and-locators).
Package page: [LaTeX Paper Skills](https://clawhub.ai/yunshenwuchuxun/plugins/latex-paper-skills).

Use the **bundle-plugin** package family to retain the existing licenses.
ClawHub's [ordinary skill publications](https://docs.openclaw.ai/clawhub/skill-format)
require MIT-0; that license does not cover the full suite's third-party template.
The plugin contains one installable `latex-paper-skills` entry and all its
resources, with Claude bundle and OpenClaw manifests.

```bash
python3 scripts/build_distribution.py --clawhub --clawhub-scope yunshenwuchuxun
npx clawhub@0.23.3 whoami
npx clawhub@0.23.3 package publish dist/clawhub-bundle \
  --family bundle-plugin \
  --name @yunshenwuchuxun/latex-paper-skills \
  --display-name "LaTeX Paper Skills" \
  --version 0.1.0 --bundle-format claude --host-targets openclaw \
  --source-repo https://github.com/yunshenwuchuxun/latex-paper-skills \
  --source-commit "<pushed-commit-sha>" --source-path . \
  --dry-run --json
```

For a new account, run `npx clawhub@0.23.3 login` first. Replace the scope with
the authenticated publisher's handle when necessary. Commit, verify, and push
the source before using its SHA. The root source path contains the build script
and tracked installable skill; `dist/clawhub-bundle` is generated from them.
After inspecting the dry-run, omit `--dry-run --json` to publish. Node.js 22+
is required by this CLI version. See the [ClawHub CLI documentation](https://docs.openclaw.ai/clawhub/cli).

## LobeHub

First request repository indexing through **Request a Skill** at
[LobeHub Skills](https://lobehub.com/skills), using the public GitHub URL.
The official `@lobehub/market-sdk` also exposes
`userPublish.submitRepo({gitUrl, type: 'skill'})` for the same submission.
Indexing is asynchronous: use the marketplace's ownership/claim flow after it
recognizes the skill. Do not guess its identifier.

Once the skill is indexed and claimed, upload the complete directory:

```bash
npx @lobehub/market-cli@0.0.41 skill publish \
  --dir skills/latex-paper-skills --identifier "<claimed-identifier>"
```

This CLI requires Node.js 22+ and a logged-in LobeHub account with GitHub
connected. `skill publish` updates a claimed listing; it cannot create a new
unindexed listing and does not provide `--dry-run`. Keep the root `SKILL.md`,
MIT `LICENSE`, and LPPL notices in the uploaded package.

**CLI 0.0.41 upload issue:** its SDK sends FormData with a JSON Content-Type
header. If it reports `Failed to parse form data`, use a native multipart
request to the same official endpoint and let `fetch` set the boundary. The
following method was used successfully for this repository's complete package:

```js
import { readFile } from 'node:fs/promises';
import { homedir } from 'node:os';
import { join } from 'node:path';

// Run the official CLI's skill list command first to refresh the login session.
const credentials = JSON.parse(await readFile(
  join(homedir(), '.lobehub-market/user-credentials.json'), 'utf8',
));
const identifier = 'yunshenwuchuxun-latex-paper-skills';
const zip = await readFile('dist/latex-paper-skills-0.1.0.zip');
const form = new FormData();
form.append('file', new Blob([zip], { type: 'application/zip' }), `${identifier}.zip`);
const response = await fetch(
  `${credentials.baseUrl}/api/v1/user/skills/${encodeURIComponent(identifier)}/versions`,
  {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${credentials.accessToken}`,
      'User-Agent': 'LobeHub-Market-CLI/0.0.41',
    },
    body: form,
  },
);
if (!response.ok) throw new Error(`LobeHub publication returned HTTP ${response.status}`);
console.log(await response.json());
```

After a timeout, inspect the owned listing and its downloadable version before
retrying; a timeout alone does not establish whether publication completed.
The marketplace assigns its own version numbers: the suite's source `0.1.0`
was published as platform version `1.0.2`. See the
[LobeHub listing](https://lobehub.com/skills/yunshenwuchuxun-latex-paper-skills).

## Standalone npm package

The public npm package [latex-paper-skills](https://www.npmjs.com/package/latex-paper-skills)
**0.1.0 is published**, with the `latex-paper-skills` executable. It ships the complete skill
directory and depends on the tested Skills CLI `1.7.2`; users need Node.js
`22.20.0` or newer to install it. There are no install lifecycle hooks, and skill
resources are already generated and included.

Install or inspect the published version:

```bash
npx latex-paper-skills@0.1.0 --agent codex --copy --yes
npx latex-paper-skills@0.1.0 --agent claude-code --global --copy --yes
npx latex-paper-skills@0.1.0 --version
npx latex-paper-skills@0.1.0 list
```

Without an agent flag, the Skills CLI handles agent discovery and selection.
An installation targets the current project by default; `--global` explicitly
selects a user-level installation. Codex project installations use
`.agents/skills/latex-paper-skills/`. The wrapper forwards official installer
options while always selecting the bundled `latex-paper-skills` entry.
Installing this npm package requires Node.js and npm; Python, Git, and LaTeX are
needed only for the maintainer build or the paper workflows that use them.

### Maintainer npm release workflow

Run these commands from a Git checkout of the repository root. The distribution
builder requires Python 3.10+ and Git. Before another release, choose an unused
version and coordinate the versions in `package.json`, `package-lock.json`,
`VERSION` in `scripts/build_distribution.py`, and `metadata.version` in
`distribution/latex-paper-skills.SKILL.md` before rebuilding. Bumping only the
npm package version leaves the ZIP and ClawHub bundle at the builder's old
version.
Version `0.1.0` is already published; npm does not allow overwriting a published
package version.

```bash
npm ci
npm run build:distribution
npm run check:distribution
npm test
npm pack --pack-destination dist
npm publish --dry-run --access public
```

`npm run build:distribution` generates the complete skill directory, ZIP, and
ClawHub bundle. Commit the generated skill directory with its source changes.
Review the npm pack file list: the allowlist includes the executable, complete
`skills/latex-paper-skills/` directory, license notices, both READMEs, and this
guide. Example projects, credentials, and `dist/` are excluded. The package has
no `prepack`, `prepare`, or install hooks; build and validation are explicit
maintainer steps.

Authenticate as the intended publisher, verify the username, then publish the
reviewed package from the repository root:

```bash
npm login --auth-type=web
npm whoami
npm publish --access public
```

Complete the npm browser verification for each command when prompted, using the
account's configured 2FA method, such as a passkey or security key. The normal
web authentication flow uses a short-lived login session and requires no
manually created access token or recovery code. See npm's
[publishing requirements](https://docs.npmjs.com/requiring-2fa-for-package-publishing-and-settings-modification/)
and [2FA configuration](https://docs.npmjs.com/configuring-two-factor-authentication/).

After publishing, confirm the registry version:

```bash
npm view latex-paper-skills version dist.tarball
```

### GitHub Release archive

For each new source version, commit and push the verified source and generated
skill directory, then create a matching GitHub Release and attach the ZIP
produced by `npm run build:distribution`:

```bash
gh release create "v<version>" "dist/latex-paper-skills-<version>.zip" \
  --title "LaTeX Paper Skills <version>" --generate-notes
```

Replace `<version>` with the new suite version. The existing `v0.1.0` release
already includes its ZIP; LobeHub's independently assigned listing version
should not be used as the GitHub tag or npm package version.
