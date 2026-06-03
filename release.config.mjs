// Versionamento SemVer da Conventional Commits.
// NIENTE pubblicazione su PyPI: si genera CHANGELOG + release GitHub e si
// sincronizza la versione in pyproject.toml, plugin.json e marketplace.json.

let dryRun = (process.env.RELEASE_DRY_RUN || "false").toLowerCase() === "true";

import config from 'semantic-release-preconfigured-conventional-commits' with { type: 'json' };

// Bump versione: pyproject (poetry) + manifest del plugin e del marketplace.
const prepareCmd =
  "poetry version -- ${nextRelease.version} && node sync-version.mjs ${nextRelease.version}";

config.plugins.push(
  ["@semantic-release/exec", { prepareCmd }]
);

if (!dryRun) {
  config.plugins.push(
    ["@semantic-release/github", {}],
    ["@semantic-release/git", {
      assets: [
        "CHANGELOG.md",
        "pyproject.toml",
        ".claude-plugin/marketplace.json",
        "plugins/fs-analysis/.claude-plugin/plugin.json"
      ],
      message: "chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}"
    }]
  );
}

export default config;
