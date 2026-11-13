# ATL Startup Resources

An offline Buzz API v1 page for searching Atlanta startup programs, funding, workspaces, events, and community resources. The plugin embeds all resource data, makes no external requests, and requests no host permissions.

## Install from Git for update checks

Buzz Desktop must support Git-installed plugins and Git update checks. Browser installation is not supported.

1. Open **Settings → Plugins → Manage plugins → Add**.
2. Choose the Git repository option and enter `https://github.com/Letitia-Chang/atl-startup-resources.git`.
3. Select branch **`main`** (or the repository's configured default release branch).
4. Select folder **`dist`**. Buzz installs the checked-in build; it does not run install scripts or build the source on recipients' computers.
5. Review access and select **Install plugin**. Verify that **ATL Startup Resources** is enabled.
6. In the plugin's actions menu, leave **Check for updates automatically** enabled. This build defaults it to on for new installations.

The installed manifest includes:

```json
"updates": { "defaultEnabled": true }
```

Buzz checks eligible saved Git sources at startup and once per hour while the app is visible. A new compatible package offers **Update and reload**. Increased host access or a publisher change requires explicit review; checks never silently install an update. Recipients can disable automatic checks or update manually from Settings.

**Existing folder/file installations do not automatically become Git installations.** Install the plugin once from the Git repository (or use the available Update/source-selection flow on a compatible older installation) before Git update checks apply.

Direct Buzz Desktop deep link:

```text
buzz://plugin-install?repository=https%3A%2F%2Fgithub.com%2FLetitia-Chang%2Fatl-startup-resources.git&ref=main&path=dist
```

Opening the link only prepares an installation preview; each person still reviews and confirms installation.

## Maintainer workflow

Requirements: Node.js 24+ and pnpm 11.8.0.

```bash
pnpm install --frozen-lockfile
pnpm build
```

Commit updated source **and both checked-in artifacts** together:

```text
dist/manifest.json
dist/plugin.js
```

`pnpm build` runs the same TypeScript/Vite build contract used by `buzzodz plugin build`; the official local command is:

```bash
buzzodz plugin build /absolute/path/to/atl-startup-resources
```

The Vite contract emits exactly one self-contained JavaScript module and `manifest.json`, rejects runtime imports or extra assets, and provides host capabilities through the plugin context. The `@buzz/author` package is type-only build tooling. Its host-matched preview tarball is vendored under `vendor/` so the install works on other machines without an absolute workstation path. Provenance: `block/buzz-app` commit `6223ae596ba9bc14c601284df16ec746f36700b3`.

CI installs from the lockfile, rebuilds, validates the module and manifest, and fails if the committed artifacts differ from the source build. Do not hand-edit only `dist/plugin.js`; update `src/index.tsx`, rebuild, and commit both source and output.

## Updates and plugin identity

- Keep manifest ID `atl.startup-resources` stable. Updates match on this ID, not the repository name.
- Keep the selected Git branch and `dist` folder stable; changing sources is not an ordinary in-place update.
- Recipients retain their enabled/disabled state and their automatic-check preference across updates.
- Changed host permissions receive explicit review. Describe access changes prominently in the pull request.

## Optional signing

Unsigned plugins are accepted by default. If your Buzz profile requires signed plugins, sign the final build using your own saved Buzz identity after every change:

```bash
buzzodz plugin sign ./dist
```

Commit generated `plugin.artifact.json` and `plugin.signature.json` alongside the two build files when distributing a signed release. Signed installations cannot silently change publisher or downgrade to unsigned.

## Local verification

```bash
buzzodz plugin install ./dist
buzzodz plugin enable atl.startup-resources
buzzodz plugin list
```

New CLI installations start disabled. Git-based recipients should use the desktop installation flow above rather than the local folder CLI.
