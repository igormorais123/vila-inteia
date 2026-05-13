const { spawnSync } = require("node:child_process");
const path = require("node:path");

process.env.ESLINT_USE_FLAT_CONFIG = "false";

const eslintPkg = require.resolve("eslint/package.json");
const eslintBin = path.join(path.dirname(eslintPkg), "bin", "eslint.js");
const result = spawnSync(
  process.execPath,
  [eslintBin, "-c", ".eslintrc.json", ".", "--ext", ".ts,.tsx"],
  {
    cwd: path.resolve(__dirname, ".."),
    env: process.env,
    stdio: "inherit",
  },
);

process.exit(result.status ?? 1);
