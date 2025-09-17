// scripts/generate-icons.mjs
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";
import pngToIco from "png-to-ico";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const PUBLIC = path.join(ROOT, "public");

const BRAND = {
  name: "Empathize360",
  description: "Practice empathetic interviews with realistic AI personas.",
  theme: "#008080",
  bg: "#ffffff"
};

// Simple, crisp teal rounded-square with white heart mark.
// Scales cleanly down to 16px.
const baseSVG = `
<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
  <rect width="512" height="512" rx="112" fill="${BRAND.theme}"/>
  <path fill="#ffffff" d="M256 368c-5 0-10-2-14-6l-22-19c-71-63-118-104-118-164 0-39 31-70 70-70 27 0 51 15 64 38 13-23 37-38 64-38 39 0 70 31 70 70 0 60-47 101-118 164l-22 19c-4 4-9 6-14 6z"/>
</svg>
`;

async function ensureDir(dir) {
  await fs.mkdir(dir, { recursive: true });
}

async function writeFile(p, content) {
  await ensureDir(path.dirname(p));
  await fs.writeFile(p, content);
}

async function main() {
  await ensureDir(PUBLIC);

  // 1) Write the base SVG
  await writeFile(path.join(PUBLIC, "favicon.svg"), baseSVG);

  // 2) Generate PNG variants
  const pngDefs = [
    { size: 16,  file: "favicon-16x16.png" },
    { size: 32,  file: "favicon-32x32.png" },
    { size: 48,  file: "icon-48.png" },
    { size: 180, file: "apple-touch-icon.png" },
    { size: 192, file: "android-chrome-192x192.png" },
    { size: 512, file: "android-chrome-512x512.png" },
    { size: 512, file: "maskable-icon.png" }
  ];

  const svgBuffer = Buffer.from(baseSVG);

  await Promise.all(
    pngDefs.map(({ size, file }) =>
      sharp(svgBuffer).resize(size, size).png().toFile(path.join(PUBLIC, file))
    )
  );

  // 3) Generate favicon.ico (16/32/48)
  const icoBuf = await pngToIco([
    path.join(PUBLIC, "favicon-16x16.png"),
    path.join(PUBLIC, "favicon-32x32.png"),
    path.join(PUBLIC, "icon-48.png")
  ]);
  await writeFile(path.join(PUBLIC, "favicon.ico"), icoBuf);

  // 4) Generate Web App Manifest
  const manifest = {
    name: BRAND.name,
    short_name: BRAND.name,
    description: BRAND.description,
    start_url: "/",
    display: "standalone",
    background_color: BRAND.bg,
    theme_color: BRAND.theme,
    icons: [
      { src: "/android-chrome-192x192.png", sizes: "192x192", type: "image/png" },
      { src: "/android-chrome-512x512.png", sizes: "512x512", type: "image/png" },
      { src: "/maskable-icon.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
      { src: "/favicon.svg", sizes: "any", type: "image/svg+xml" }
    ]
  };
  await writeFile(path.join(PUBLIC, "manifest.webmanifest"), JSON.stringify(manifest, null, 2));

  console.log("✓ Icons and manifest generated in /public");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
