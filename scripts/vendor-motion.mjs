import { build } from "esbuild";
await build({ entryPoints: ["static/src/motion-entry.js"], bundle: true, minify: true, format: "iife", target: "es2020", outfile: "static/vendor/motion.js" });
console.log("motion bundle built");
