import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
if (!process.env.CI && existsSync(".git")) {
  let current = "";
  try {
    current = execFileSync(
      "git",
      ["config", "--local", "--get", "core.hooksPath"],
      { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] },
    );
  } catch (error) {
    if (error.status !== 1) throw error;
  }
  if (current.trim() && current.trim() !== ".githooks")
    throw new Error("Existing hooksPath detected; review before replacing it.");
  execFileSync("git", ["config", "--local", "core.hooksPath", ".githooks"], {
    stdio: "inherit",
  });
}
