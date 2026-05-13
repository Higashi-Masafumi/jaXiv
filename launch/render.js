#!/usr/bin/env node
/**
 * Re-render all brand assets from SVG sources.
 *
 * Requires:  npm install sharp png-to-ico
 * Run from /tmp/asset-gen (or any dir with the two deps installed):
 *   node /home/user/jaXiv/launch/render.js
 */

const sharp = require('sharp');
const fs = require('fs');
const path = require('path');
const pngToIco = require('png-to-ico').default || require('png-to-ico');

const ROOT = path.resolve(__dirname, '..');
const SRC = path.join(ROOT, 'launch/src');
const PUB = path.join(ROOT, 'frontend/public');
const BRAND = path.join(PUB, 'brand');
const LAUNCH = path.join(ROOT, 'launch');
const PH = path.join(LAUNCH, 'product-hunt');

async function svgToPng(svgPath, outPath, size) {
  const svg = fs.readFileSync(svgPath);
  let img = sharp(svg, { density: 512 });
  if (size) {
    img = img.resize(size.w || size, size.h || size, {
      fit: 'contain',
      background: { r: 0, g: 0, b: 0, alpha: 0 },
    });
  }
  await img.png().toFile(outPath);
  console.log('✓', path.relative(ROOT, outPath));
}

async function main() {
  for (const d of [BRAND, PH]) fs.mkdirSync(d, { recursive: true });

  // Favicons: small uses simplified mark, large uses detailed mark
  await svgToPng(`${SRC}/logo-mark-small.svg`, `${BRAND}/icon-16.png`, 16);
  await svgToPng(`${SRC}/logo-mark-small.svg`, `${BRAND}/icon-32.png`, 32);
  await svgToPng(`${SRC}/logo-mark-small.svg`, `${BRAND}/icon-48.png`, 48);
  await svgToPng(`${SRC}/logo-mark.svg`, `${BRAND}/icon-180.png`, 180);
  await svgToPng(`${SRC}/logo-mark.svg`, `${BRAND}/icon-192.png`, 192);
  await svgToPng(`${SRC}/logo-mark.svg`, `${BRAND}/icon-512.png`, 512);

  const icoBuf = await pngToIco([
    `${BRAND}/icon-16.png`,
    `${BRAND}/icon-32.png`,
    `${BRAND}/icon-48.png`,
  ]);
  fs.writeFileSync(`${PUB}/favicon.ico`, icoBuf);
  console.log('✓ frontend/public/favicon.ico');
  fs.copyFileSync(`${SRC}/logo-mark.svg`, `${PUB}/favicon.svg`);
  console.log('✓ frontend/public/favicon.svg');

  // Previews (local QA, not shipped)
  await svgToPng(`${SRC}/logo-mark.svg`, `${LAUNCH}/preview-mark-512.png`, 512);
  await svgToPng(`${SRC}/logo-mark-small.svg`, `${LAUNCH}/preview-mark-small-512.png`, 512);
  await svgToPng(`${SRC}/logo-wordmark.svg`, `${LAUNCH}/preview-wordmark.png`, { w: 900, h: 240 });

  // Product Hunt
  await svgToPng(`${SRC}/logo-mark.svg`, `${PH}/logo-240.png`, 240);
  await svgToPng(`${SRC}/logo-mark.svg`, `${PH}/thumbnail-240.png`, 240);
  await svgToPng(`${SRC}/gallery-1-hero.svg`, `${PH}/gallery-1-hero.png`, { w: 1270, h: 760 });
  await svgToPng(`${SRC}/gallery-2-translate.svg`, `${PH}/gallery-2-translate.png`, { w: 1270, h: 760 });
  await svgToPng(`${SRC}/gallery-3-features.svg`, `${PH}/gallery-3-features.png`, { w: 1270, h: 760 });

  // OG image — shipped under /brand
  await svgToPng(`${SRC}/og-image.svg`, `${BRAND}/og-image.png`, { w: 1200, h: 630 });
  fs.copyFileSync(`${BRAND}/og-image.png`, `${LAUNCH}/preview-og.png`);
  console.log('✓ launch/preview-og.png');
}

main().catch(e => { console.error(e); process.exit(1); });
