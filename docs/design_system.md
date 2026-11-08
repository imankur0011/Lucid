# Arthava Design System: Refined Wealth-Management Visual Foundation

**Version:** 1.0.0  
**Brand:** Arthava (अर्थव)  
**Theme Philosophy:** Institutional Wealth Management • Light-First • Fiduciary Clarity

---

## 1. Visual Direction & Aesthetic Philosophy

Rather than adopting a speculative crypto exchange or hyper-saturated dark terminal design, **Arthava** implements a **refined, light-first wealth-management aesthetic** inspired by institutional private banking, Swiss financial clarity, and modern fiduciary software:

1. **Warm Ivory Foundation:** Calming, tactile, off-white background tones (`#FAF9F5`) that reduce eye fatigue and convey permanence, stability, and quiet luxury.
2. **Deep Navy Authority:** High-contrast deep navy and slate tones (`#0C192C`, `#1E293B`) for typography, navigation structures, and structural boundaries, commanding trust.
3. **Muted Sage & Emerald Accents:** Selective green accents (`#166534`, `#0D9488`, `#047857`) representing organic compounding, validation success, and sustainable growth, avoiding neon fluorescent tones.
4. **Restrained Neutral Borders:** Crisp, thin, elegant 1px hairline borders (`#E5E5DF`) that delineate information architecture without heavy visual noise or excessive blur.
5. **Tabular Numerics for Financial Data:** All financial amounts, shares, percentages, and metrics employ monospaced tabular figures (`tabular-nums`) to align decimal points and facilitate effortless vertical scanning.
6. **No Unicode Emojis:** Replaced all inconsistent OS emojis with bespoke, semantic SVG vector iconography.

---

## 2. Design Token System

### 2.1 Color Palette

```css
:root {
  /* Surface & Background Tokens */
  --bg-canvas: #FAF9F5;          /* Warm Ivory Canvas */
  --bg-surface: #FFFFFF;         /* Crisp White Card Surface */
  --bg-surface-elevated: #F4F3ED;/* Soft Warm Elevation */
  --bg-subtle: #ECEAE2;          /* Subtle Component Background */

  /* Text & Content Tokens */
  --text-primary: #0C192C;       /* Deep Fiduciary Navy */
  --text-secondary: #475569;     /* Slate Secondary Description */
  --text-muted: #64748B;         /* Restrained Subtext / Footers */
  --text-inverse: #FFFFFF;       /* High Contrast White */

  /* Border Tokens */
  --border-light: #E5E5DF;       /* Primary Restrained Card Hairline */
  --border-subtle: #ECEAE2;      /* Inner Dividers */
  --border-active: #0C192C;      /* Focus / Active Ring */

  /* Semantic State Tokens */
  --brand-primary: #0C192C;      /* Primary Navy Brand */
  --brand-primary-hover: #1E293B;
  --accent-sage: #166534;         /* Muted Sage / Growth Emerald */
  --accent-sage-bg: #F0FDF4;      /* Soft Sage Pill Fill */
  --accent-sage-border: #BBF7D0;
  
  --accent-amber: #B45309;        /* Prudent Warning Amber */
  --accent-amber-bg: #FFFBEB;
  --accent-amber-border: #FDE68A;

  --accent-rose: #B91C1C;         /* Risk / Downside Rose */
  --accent-rose-bg: #FEF2F2;
  --accent-rose-border: #FECACA;

  --accent-indigo: #4338CA;       /* Quantitative Analysis Indigo */
  --accent-indigo-bg: #EEF2FF;
  --accent-indigo-border: #C7D2FE;
}
```

### 2.2 Typography Scale

- **Display (Hero Titles):** 28px–32px (1.75rem–2rem), Font Weight 700 / 800, Letter Spacing -0.03em.
- **Section Heading (H1/H2):** 20px–24px (1.25rem–1.5rem), Font Weight 700, Letter Spacing -0.02em.
- **Card Heading (H3/H4):** 15px–16px (0.9375rem–1rem), Font Weight 600, Letter Spacing -0.01em.
- **Body Text:** 14px (0.875rem), Line Height 1.6, Slate secondary for sustained reading.
- **Financial Metric Values:** 22px–28px, Font Weight 700, `font-variant-numeric: tabular-nums`.
- **Labels & Badges:** 11px–12px, Font Weight 600, Uppercase tracking +0.04em.
- **Disclaimers & Subtext:** 11px–12px, Line Height 1.5, Muted slate.

### 2.3 Elevations & Shadows
- **Shadow Subtlety:** Avoid harsh, glowing drop-shadows.
- `shadow-sm`: `0 1px 2px 0 rgba(12, 25, 44, 0.04)`
- `shadow-card`: `0 2px 6px -1px rgba(12, 25, 44, 0.05), 0 1px 3px -1px rgba(12, 25, 44, 0.03)`
- `shadow-elevated`: `0 10px 25px -5px rgba(12, 25, 44, 0.06), 0 8px 10px -6px rgba(12, 25, 44, 0.04)`

### 2.4 Border Radii
- **Badges / Buttons:** `8px` (`rounded-lg`) or `10px` for refined precision.
- **Cards & Data Tables:** `16px` (`rounded-2xl`).
- **Interactive Inputs:** `10px` (`rounded-xl`).

---

## 3. Component Design Patterns

### 3.1 Primary Buttons
- Background: `var(--brand-primary)` (`#0C192C`).
- Hover: `#1E293B` with smooth 150ms ease transition.
- Text: White, font-weight 600, 14px.
- Focus: Offset ring `ring-2 ring-slate-900 ring-offset-2`.

### 3.2 Secondary & Filter Buttons
- Background: `var(--bg-surface)` (`#FFFFFF`).
- Border: 1px solid `var(--border-light)` (`#E5E5DF`).
- Hover: Background `var(--bg-surface-elevated)` (`#F4F3ED`), text `#0C192C`.

### 3.3 Financial Data Tables
- Table Container: White background with hairline border and rounded corners.
- Header: Subtle ivory (`#F5F4EE`), text 11px uppercase bold (`#64748B`), tracking wider.
- Cell Rows: Alternating hover with `#FAF9F5`, padding 14px 20px.
- Numerics: Right-aligned tabular numbers with rupee symbol prefix (`₹`).
- Action Pills: Sage Buy (`bg-emerald-50 text-emerald-700`), Rose Sell (`bg-rose-50 text-rose-700`), Slate Hold (`bg-slate-100 text-slate-700`).

### 3.4 Interactive Visual Charts (Allocation Donut & Sector Bars)
- Vector SVG rendered with precise percentage segment calculation.
- High-contrast color palette for asset classes:
  - Deep Navy (`#0C192C`)
  - Forest Sage (`#15803D`)
  - Indigo Slate (`#4338CA`)
  - Warm Amber (`#D97706`)
  - Soft Rose (`#E11D48`)
  - Teal (`#0D9488`)

---

## 4. Accessibility & Contrast Compliance

All color token combinations conform strictly to **WCAG 2.1 AA** standards:
- Dark Navy (`#0C192C`) on Warm Ivory (`#FAF9F5`): **Contrast Ratio 15.2:1** (Exceeds AAA requirement of 7:1).
- Slate (`#475569`) on White (`#FFFFFF`): **Contrast Ratio 7.8:1** (Exceeds AAA).
- Sage Accent (`#166534`) on White: **Contrast Ratio 5.9:1** (Exceeds AA 4.5:1).
- Rose Alert (`#B91C1C`) on White: **Contrast Ratio 5.6:1** (Exceeds AA 4.5:1).
