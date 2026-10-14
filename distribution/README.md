# Distribution and publishing

The public package is `skills/latex-paper-skills/`, version **0.1.0**. It contains
all eight source workflows, shared Python helpers, and templates. Nested
`SKILL.md` files become `workflow.md` to keep the installable package a single
skill. Source files remain under `.codex/skills/`.

## Build and verify

```bash
python3 scripts/build_distribution.py --archive
python3 scripts/build_distribution.py --check
```

The ZIP at `dist/latex-paper-skills-0.1.0.zip` has `SKILL.md` at its root, with
no showcase projects, datasets, local configuration, or Python cache files.
Commit the generated `skills/latex-paper-skills/` directory along with any
source changes so GitHub installers receive the same tested contents.

## npx and skills.sh

```bash
npx skills@latest add yunshenwuchuxun/latex-paper-skills --skill latex-paper-skills
```

No npm publication is required. The `skills` npm CLI installs the skill from
GitHub. Per the [skills.sh FAQ](https://skills.sh/docs/faq), the leaderboard tracks
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
