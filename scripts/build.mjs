import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";

const target = process.argv[2] ?? "web";
let build;

if (target === "web") {
    build = spawnSync(".venv/bin/python", ["scripts/export_web.py"], { stdio: "inherit" });
} else if (target === "ios") {
    if (!existsSync("mobile/package.json")) {
        console.error("The iOS target needs the Expo app planned for phase 3.");
        process.exit(1);
    }
    build = spawnSync("npm", ["--prefix", "mobile", "run", "export:ios"], { stdio: "inherit" });
} else {
    console.error("Choose web or ios as the build target.");
    process.exit(2);
}

if (build.error) {
    console.error(build.error.message);
}
process.exit(build.status ?? 1);
