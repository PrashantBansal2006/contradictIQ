# ContradictIQ — Design System & UI Spec

**Reference:** `prd.md` (what), `architecture.md` (how), this file (look & feel)

---

## 1. Visual Identity

**Theme:** Dark cyberpunk-financial — deep black backgrounds, neon magenta/fuchsia as the primary accent, monochromatic grays for content hierarchy, no blue. Inspired by the uploaded reference image.

**Tagline:** "The LLM proposes. The code disposes."

---

## 2. Color Tokens

| Token | Value | Use |
|---|---|---|
| `--bg` | `#080a0f` | Page background |
| `--surface` | `#0f1219` | Cards, panels |
| `--surface-hover` | `#161c28` | Hover state |
| `--surface-border` | `#1e2536` | Default border |
| `--border-glow` | `rgba(232,0,120,0.35)` | Active / focus border glow |
| `--primary` | `#e80078` | Neon magenta — CTAs, active states, key numbers |
| `--primary-dim` | `rgba(232,0,120,0.12)` | Button backgrounds, pill fills |
| `--primary-glow` | `rgba(232,0,120,0.25)` | Box-shadow glow |
| `--text-1` | `#f1f5f9` | Primary text |
| `--text-2` | `#94a3b8` | Secondary / caption |
| `--text-3` | `#4b5563` | Placeholder, disabled |
| `--verdict-consistent` | `#10b981` | Green |
| `--verdict-conflicting` | `#f43f5e` | Red |
| `--verdict-inconclusive` | `#f59e0b` | Amber |
| `--mono-font` | `JetBrains Mono, Fira Code, monospace` | Code, IDs, values |

---

## 3. Typography

- **Headings:** `Inter`, weight 700–800, tight tracking (`-0.02em`)
- **Body:** `Inter`, weight 400–500
- **Mono/data:** `JetBrains Mono` — all financial values, IDs, formulas, period strings, JSON
- **Label caps:** `text-[10px] uppercase tracking-widest font-mono text-text-2` used for section labels

---

## 4. Background & Cursor FX

### 4.1 Images (in `/public`)
| File | Use |
|---|---|
| `home color.png` | Home/Login/Register pages — color version background |
| `monochromo home.png` | Home/Login/Register pages — monochrome version layered on top |
| `Neon Magenta Cyberpunk Circuit Wall.png` | All inner app pages — color version |
| `Monochrome Cyberpunk Circuit Wall.png` | All inner app pages — monochrome version layered on top |

### 4.2 Cursor Reveal FX
On every page, two `<div>` layers are absolutely positioned (full bleed, `z-0`):
1. **Bottom layer:** color image, always visible
2. **Top layer:** monochrome image, full opacity, with CSS `mask-image: radial-gradient(circle 120px at <cursorX>px <cursorY>px, transparent 0%, black 100%)`

Effect: cursor moves → 120px circle punches through the monochrome layer, revealing the color image underneath.

Implementation: React state `cursorPos {x, y}`, `onMouseMove` on root container, inline `style` updates CSS properties `--cx --cy`.

### 4.3 Page wrapper
Every page has `position: relative; overflow: hidden; min-height: 100vh; background: #080a0f`.
Background layers: `position: absolute; inset: 0; background-size: cover; background-position: center; pointer-events: none; z-0`.
Content: `position: relative; z-10`.

---

## 5. Component Spec

### 5.1 Buttons
| Variant | Recipe |
|---|---|
| Primary | `bg-primary text-white hover:brightness-110 shadow-[0_0_16px_var(--primary-glow)]` |
| Ghost | `border border-surface-border text-text-2 hover:border-primary/50 hover:text-white` |
| Danger | `bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20` |

Border-radius: `rounded-lg` (8 px). No pill buttons except status badges.

### 5.2 Cards / Panels
```
bg-surface border border-surface-border rounded-xl
hover:border-primary/30 transition
```
Active/selected: `border-primary/60 shadow-[0_0_20px_rgba(232,0,120,0.1)]`

### 5.3 Input Fields
```
bg-[#080a0f] border border-surface-border rounded-lg
focus:border-primary/60 focus:shadow-[0_0_0_2px_rgba(232,0,120,0.15)]
text-text-1 placeholder-text-3
```

### 5.4 Verdict Badges
All: `px-2.5 py-0.5 rounded font-mono text-[11px] uppercase tracking-wider border`
- Consistent: `bg-emerald-500/10 border-emerald-500/30 text-emerald-400`
- Conflicting: `bg-rose-500/10 border-rose-500/30 text-rose-400`
- Inconclusive: `bg-amber-500/10 border-amber-500/30 text-amber-400`

### 5.5 Nav
- **TopNav:** `sticky top-0 z-50 bg-[#080a0f]/90 backdrop-blur-sm border-b border-surface-border h-16`
- Logo: `Contradict` white + `IQ` magenta
- Active nav link: left magenta border `border-l-2 border-primary` + text-primary

### 5.6 Investigation Tab Bar
Horizontal tabs. Active: `border-b-2 border-primary text-white`. Inactive: `text-text-2 hover:text-text-1`.

---

## 6. Page Inventory

| Route | Page | BG Set |
|---|---|---|
| `/login` | Login | Home |
| `/register` | Register | Home |
| `/investigations` | Investigations List | App |
| `/investigations/:id/dashboard` | Dashboard Tab | App |
| `/investigations/:id/documents` | Documents Tab | App |
| `/investigations/:id/documents/:docId` | Document Detail | App |
| `/investigations/:id/claims` | Claims Tab | App |
| `/investigations/:id/findings` | Findings Tab | App |
| `/investigations/:id/graph` | Evidence Graph | App |
| `/investigations/:id/history` | Ledger History | App |
| `/investigations/:id/compare` | Compare Tab | App |
| `/eval` | Eval Harness | App |
| `/shared/:token` | Shared / Judge View | App |

---

## 7. Layout Shell

```
┌─────────────────────────────────┐
│  TopNav (64px sticky, z-50)     │
├─────────────────────────────────┤
│  [Tab bar — inside inv/:id/*]   │
├─────────────────────────────────┤
│  <Outlet /> content             │
│  max-w-7xl mx-auto px-4 py-6   │
└─────────────────────────────────┘
Background layers at z-0, content at z-10.
```

---

## 8. Data Display Conventions

- **Financial values:** `font-mono text-primary` (magenta) for amounts; white for labels
- **Period strings:** `font-mono text-text-2` e.g. `FY2025`, `Q3 FY25`
- **Engine version badge:** `font-mono text-[11px]` `v0.1.0`
- **IDs / hashes:** `font-mono text-[11px] text-text-3`

---

## 9. Animations

| | Value |
|---|---|
| Base transition | `transition-all duration-200 ease-in-out` |
| Cursor mask | No lag — CSS `--cx/--cy` updated raw on `mousemove` |
| Glow pulse | `animate-pulse` on API health dot only |
| Card hover lift | `hover:shadow-[0_0_16px_rgba(232,0,120,0.08)]` |

---

## 10. Accessibility

- Min contrast 4.5:1 body text on dark surfaces
- Focus rings: `focus-visible:ring-2 focus-visible:ring-primary/60 outline-none`
- Keyboard navigation works on all interactive elements

