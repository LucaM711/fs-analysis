// Sincronizza la versione SemVer nei manifest del plugin e del marketplace.
// Uso: node sync-version.mjs <version>
import { readFileSync, writeFileSync } from "node:fs";

const version = process.argv[2];
if (!version) {
  console.error("usage: node sync-version.mjs <version>");
  process.exit(1);
}

const targets = [
  {
    path: "plugins/fs-analysis/.claude-plugin/plugin.json",
    apply: (json) => { json.version = version; },
  },
  {
    path: ".claude-plugin/marketplace.json",
    apply: (json) => {
      for (const plugin of json.plugins || []) {
        if (plugin.name === "fs-analysis") plugin.version = version;
      }
    },
  },
];

for (const { path, apply } of targets) {
  const json = JSON.parse(readFileSync(path, "utf8"));
  apply(json);
  writeFileSync(path, JSON.stringify(json, null, 2) + "\n");
  console.log(`synced ${path} -> ${version}`);
}
