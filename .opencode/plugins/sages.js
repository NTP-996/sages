// Registers the Sages skills folder with opencode. Nothing else is configured.

import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const skillsPath = join(here, "..", "..", "skills");

export const SagesPlugin = async () => ({
  config(config) {
    config.skills ??= {};
    config.skills.paths ??= [];
    if (!config.skills.paths.includes(skillsPath)) {
      config.skills.paths.push(skillsPath);
    }
  },
});
