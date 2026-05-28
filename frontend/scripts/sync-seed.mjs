// Copies backend/fixtures/seed_demo.csv into frontend/public/seed_demo.csv
// so the auto-prime flow has a static asset to POST back to /import/seed.
//
// Usage: pnpm sync:seed (run from the frontend/ directory).

import { copyFile, mkdir, stat } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const source = resolve(__dirname, "../../backend/fixtures/seed_demo.csv");
const target = resolve(__dirname, "../public/seed_demo.csv");

async function main() {
  try {
    await stat(source);
  } catch {
    console.error(`[sync-seed] Source CSV not found at ${source}`);
    process.exit(1);
  }

  await mkdir(dirname(target), { recursive: true });
  await copyFile(source, target);
  console.log(`[sync-seed] Copied seed_demo.csv -> ${target}`);
}

main().catch((err) => {
  console.error("[sync-seed] Failed:", err);
  process.exit(1);
});
