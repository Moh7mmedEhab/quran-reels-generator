---
name: Serene Studio Light
colors:
  surface: '#faf8ff'
  surface-dim: '#d2d9f4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e2e7ff'
  surface-container-highest: '#dae2fd'
  on-surface: '#131b2e'
  on-surface-variant: '#464555'
  inverse-surface: '#283044'
  inverse-on-surface: '#eef0ff'
  outline: '#777587'
  outline-variant: '#c7c4d8'
  surface-tint: '#4d44e3'
  primary: '#3525cd'
  on-primary: '#ffffff'
  primary-container: '#4f46e5'
  on-primary-container: '#dad7ff'
  inverse-primary: '#c3c0ff'
  secondary: '#006591'
  on-secondary: '#ffffff'
  secondary-container: '#39b8fd'
  on-secondary-container: '#004666'
  tertiary: '#005338'
  on-tertiary: '#ffffff'
  tertiary-container: '#006e4b'
  on-tertiary-container: '#67f4b7'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e2dfff'
  primary-fixed-dim: '#c3c0ff'
  on-primary-fixed: '#0f0069'
  on-primary-fixed-variant: '#3323cc'
  secondary-fixed: '#c9e6ff'
  secondary-fixed-dim: '#89ceff'
  on-secondary-fixed: '#001e2f'
  on-secondary-fixed-variant: '#004c6e'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#faf8ff'
  on-background: '#131b2e'
  surface-variant: '#dae2fd'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.025em
  display-lg-mobile:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 38px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 30px
    letterSpacing: -0.015em
  headline-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 26px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 26px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: -0.005em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.03em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.25rem
  gutter-mobile: 0.75rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style
The design system embodies a serene, uncluttered, and deeply focused environment tailored for creators producing reverent, high-impact vertical video content (Reels, Shorts, TikTok). It pairs contemporary SaaS precision with an airy, contemplative atmosphere.

### Core Philosophy
- **Reverence Meets Utility:** The creation workflow treats sacred texts with dignity while delivering lightning-fast, intuitive tooling. UI chrome steps back; typography, audio waveforms, and video viewports take precedence.
- **Airy Clarity:** Interfaces leverage expansive breathing room, pure white elevations, and crisp slate contrasts. Surfaces feel featherlight, eliminating cognitive fatigue during prolonged timeline and subtitle editing sessions.
- **Precision Modernism:** High legibility, structural alignment, subtle translucent dividers, and fluid transitions create an immediate sense of software craftsmanship and reliability.

## Colors
The palette is built upon radiant, clean daylight foundations paired with a focused, authoritative indigo.

### Palette Architecture
- **Primary (`#4f46e5` / `#4338ca` hover):** Vibrant Indigo anchor used for major call-to-actions, active timeline cursors, generation triggers, and key interactive states.
- **Secondary (`#0ea5e9`):** Luminous Sky Blue, utilized for secondary workflow highlights, audio stem indicators, and processing progress states.
- **Tertiary (`#10b981`):** Calming Emerald, reserved for completion badges, export success confirmations, and active audio sync states.
- **Neutrals & Surfaces:**
  - **Canvas Background:** Soft off-white (`#f8fafc` / `#f9fafb`) creating subtle natural contrast against elevated workspaces.
  - **Surface Container (Base):** Pure White (`#ffffff`) for cards, inspector sidebars, dialog sheets, and top navigations.
  - **Structural Borders:** Subtle slate dividers (`#e2e8f0` to `#e5e7eb`), providing structure without visual noise.
- **Text & Hierarchy:**
  - **Headings & Emphasized Text:** Deep slate (`#0f172a` / `#111827`) for authoritative contrast and readability.
  - **Body & Controls:** Slate gray (`#475569` / `#4b5563`) for effortless, long-session scanning.
  - **Muted & Meta:** Slate mist (`#94a3b8`) for timeline timecodes, shortcut badges, and secondary audio metadata.

## Typography
Typography is crisp, neutral, and meticulously spaced to provide effortless clarity across dense audio/video studio controls and expansive Arabic calligraphy displays.

### Typographic Guidelines
- **Systematic Font Selection:** `Inter` handles all Latin chrome, numbers, timing sequences, and UI metadata with high-performance tabular figures (`tnum`) enabled on counters and timestamps.
- **Arabic Script Pairing:** When Quranic verses, transliterations, or surah names are rendered in the video viewport or inspector, pair cleanly with high-fidelity Naskh typography (such as Amiri or Scheherazade New) without altering the Latin UI scale.
- **Hierarchy Management:** UI labels prioritize tight vertical rhythms (`lineHeight` close to base size) to maintain alignment inside toolbar buttons, inspector rows, and track strips.

## Layout & Spacing
The layout employs an expansive 3-column studio architecture engineered for horizontal precision, with fixed side tools and a flexible canvas.

### Layout Hierarchy
1. **Left Rail / Navigation (Fixed 72px or 240px expanded):** Houses media assets, reciter libraries, translation pickers, and video template selections.
2. **Central Studio Canvas (Flexible):** Holds the 9:16 vertical phone viewport preview, surrounded by generous atmospheric breathing space and bottom playback controls.
3. **Right Inspector Panel (Fixed 340px to 380px):** Typography controls (font weight, glow, shadow, outline), motion pacing, ayah range pickers, and export resolutions.
4. **Bottom Timeline Drawer (Collapsible 160px):** Audio waveform, synchronized word-by-word subtitle blocks, and visual background overlays.

### Responsive Behavior
- **Desktop (>= 1280px):** Full 3-column studio with persistent timeline and unobstructed 9:16 phone canvas.
- **Tablet (768px – 1279px):** Inspector panels collapse into floating overlay drawers; canvas centers automatically with touch-friendly scrubbers.
- **Mobile (< 768px):** Single-column stacked mode with tabbed navigation: Preview, Audio/Reciter, Subtitles, and Export.

## Elevation & Depth
Depth in the design system is communicated through atmospheric daylight layering rather than heavy shadows, ensuring a tranquil, weightless aesthetic.

### Elevation Tiers
- **Surface Level 0 (Canvas):** Soft off-white base (`#f8fafc`). Non-interactive, grounding backdrop.
- **Surface Level 1 (Workplace & Sidebars):** Pure white (`#ffffff`) bounded by a hairline border (`1px solid #e2e8f0`). Flat, crisp, and anchored.
- **Surface Level 2 (Floating Cards, Studio Canvas Viewport):** Pure white with diffuse ambient occlusion: `0 4px 6px -1px rgba(15, 23, 42, 0.04), 0 2px 4px -2px rgba(15, 23, 42, 0.03)` and soft outline `1px solid #e2e8f0`.
- **Surface Level 3 (Modals, Reciter Selection Menus, Export Flyouts):** Suspended white with expanded soft shadow: `0 20px 25px -5px rgba(15, 23, 42, 0.06), 0 8px 10px -6px rgba(15, 23, 42, 0.04)`.
- **Glassmorphic Accents:** Used sparingly for in-canvas floating video control pills (`rgba(255, 255, 255, 0.85)` with `backdrop-filter: blur(12px)` and a subtle `rgba(255, 255, 255, 0.4)` top edge highlight).

## Shapes
The visual identity embraces soft, organic geometry to reinforce warmth and modern elegance across all touchpoints.

### Corner Curvature Rules
- **Base Elements (Buttons, Inputs, Badges):** Smooth rounded corners (`rounded-lg` / 8px – 12px) for structured tactile targets.
- **Cards & Panes:** `rounded-xl` (16px) to `rounded-2xl` (24px) for visual comfort and distinct segregation of workflow panels.
- **Vertical Video Preview Frame:** `rounded-3xl` (32px) simulating real mobile devices with smooth corner masking.
- **Toolbars & Playback Pills:** Full pill radius (`rounded-full`) for central media actions, time scrubbers, and category tags.

## Components

### Buttons
- **Primary Studio Button:** Background `#4f46e5`, text `#ffffff`, border radius `12px`, padding `10px 20px`. Hover transitions to `#4338ca` with a faint indigo glow (`0 8px 20px -4px rgba(79, 70, 229, 0.35)`).
- **Secondary / Action Button:** Pure white background, `1px solid #e2e8f0`, text `#0f172a`. Hover transitions to background `#f8fafc` and border `#cbd5e1`.
- **Ghost Action Button:** Transparent background, text `#475569`, hover background `#f1f5f9`, text `#0f172a`.

### Cards & Canvas Containers
- **Preview Canvas Container:** High-contrast pure white card with `24px` radius, encapsulated by a subtle `1px solid #e2e8f0` border and `shadow-md`. Houses the simulated 9:16 vertical viewport centered with letterbox buffers.
- **Inspector Section Cards:** Clean white containers with subtle top dividers, `16px` padding, containing segmented toggle buttons and slider tracks.

### Input Fields & Selectors
- **Form Controls:** Background `#ffffff`, border `1px solid #e2e8f0`, text `#0f172a`, placeholder text `#94a3b8`, radius `10px`, padding `10px 14px`.
- **Focus State:** Crisp 2px outer ring with `#4f46e5` at 20% opacity and border colored `#4f46e5`.
- **Verse & Reciter Search:** Left-adorned icon in `#94a3b8`, clear indicator on right, full tabular auto-complete dropdown.

### Chips & Filter Pills
- **Active State:** Background `#eef2ff`, border `1px solid #c7d2fe`, text `#4338ca`, font weight `500`.
- **Default State:** Background `#f8fafc`, border `1px solid #e2e8f0`, text `#475569`, font weight `500`. Hover brings border `#cbd5e1` and text `#0f172a`.

### Checkboxes, Radios, & Switches
- **Toggles (Aspect Ratio, Audio Normalization, Auto-Captions):** Smooth pill track (`#e2e8f0` when off, `#4f46e5` when on) with a pure white circular thumb elevated by a micro-shadow (`0 2px 4px rgba(0,0,0,0.1)`).
- **Checkboxes:** 20px square with 6px border radius, border `1px solid #cbd5e1`. Checked state transitions instantly to `#4f46e5` fill with a sharp white checkmark.

### Domain-Specific Components
- **Vertical Video Viewport (9:16):** Framed with a 1px boundary, subtle drop shadow, and floating aspect-ratio badges (`Reels 9:16`, `Shorts 9:16`, `Square 1:1`).
- **Waveform & Subtitle Scrub Strip:** Light slate track (`#f1f5f9`), indigo audio peaks (`#818cf8`), and high-contrast draggable scrub playhead with active timestamps in micro tabular typography.
- **Word-by-Word Caption Block:** Elevated white pills on the timeline with editable syllable boundaries, allowing instant click-to-edit transcription corrections.