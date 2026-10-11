// Copies third-party browser assets from node_modules into static/vendor so the app works offline.
import { cpSync, mkdirSync, existsSync } from "node:fs";

const out = "static/vendor";
mkdirSync(`${out}/fonts`, { recursive: true });
mkdirSync(`${out}/leaflet`, { recursive: true });

const copy = (from, to) => {
  if (!existsSync(from)) throw new Error(`missing ${from} (run npm install)`);
  cpSync(from, `${out}/${to}`, { recursive: true });
};

copy("node_modules/alpinejs/dist/cdn.min.js", "alpine.min.js");
// motion.js is built (tree-shaken) by scripts/vendor-motion.mjs
copy("node_modules/leaflet/dist/leaflet.js", "leaflet/leaflet.js");
copy("node_modules/leaflet/dist/leaflet.css", "leaflet/leaflet.css");
copy("node_modules/leaflet/dist/images", "leaflet/images");
copy("node_modules/@fontsource-variable/fraunces/files/fraunces-latin-wght-normal.woff2", "fonts/fraunces.woff2");
copy("node_modules/@fontsource-variable/fraunces/files/fraunces-latin-wght-italic.woff2", "fonts/fraunces-italic.woff2");
copy("node_modules/@fontsource-variable/inter-tight/files/inter-tight-latin-wght-normal.woff2", "fonts/inter-tight.woff2");
copy("node_modules/@fontsource-variable/jetbrains-mono/files/jetbrains-mono-latin-wght-normal.woff2", "fonts/jetbrains-mono.woff2");
console.log("vendor assets copied");
