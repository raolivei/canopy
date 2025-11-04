# LedgerLight Brand Assets

This folder contains the bespoke brand visuals generated for LedgerLight. Assets are exported as resolution-independent SVG so they scale cleanly at any size.

## Files

- `ledgerlight-icon.svg` – Standalone icon for avatars or app tiles.
- `ledgerlight-icon-32.png`, `...-64.png`, `...-180.png`, `...-192.png`, `...-256.png`, `...-512.png`, `...-1024.png` – Raster exports sized for favicons, PWA manifests, and store listings.
- `ledgerlight-logo-dark.svg` – Horizontal lockup optimised for dark or transparent backgrounds.
- `ledgerlight-logo-light.svg` – Horizontal lockup for light backgrounds.
- `ledgerlight-banner-dark.svg` / `.png` – 1600×900 hero banner with dark treatment.
- `ledgerlight-banner-light.svg` / `.png` – 1600×900 hero banner for light surfaces.
- `ledgerlight-banner-dark-og.png`, `ledgerlight-banner-light-og.png` – 1200×630 crops for social/Open Graph previews.

## Palette

- Navy core: `#0B1C2C`, `#102B52`, `#071223`
- Warm gold: `#D6A85B`, `#B88728`, `#F0DCA8`
- Teal accent: `#7FD1C9`, `#31799B`
- Soft neutrals: `#FDFBF6`, `#F2E6D7`

## Usage notes

- The icon set covers favicons through store artwork; use `ledgerlight-icon-512.png` for desktop installers and `ledgerlight-icon-1024.png` for app marketplaces.
- The banners are laid out for hero sections; use the `*-og.png` variants when configuring social cards (OG/Twitter).
- Text in the logos uses `Poppins` (semibold). If that font is unavailable, system sans-serif fallbacks maintain the intended weight.
- Feel free to recolour the text layer in the SVGs when integrating with themes, keeping the gold for emphasis to preserve the finance/luxury impression.
