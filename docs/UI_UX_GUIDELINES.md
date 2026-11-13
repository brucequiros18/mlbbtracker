# UI/UX Guidelines

Design direction: **Competitive Minimalism** — modern, professional, premium,
gaming-oriented. Dark-first. Original branding; nothing copied from Tracker.gg,
OP.GG or Mobile Legends.

Core principle: **information without confusion** — find an answer fast.

## Color tokens (`AppPalette`)

| Token | Dark (default) | Light | Use |
|---|---|---|---|
| Background | `#111318` | `#F6F7FB` | app canvas |
| Background secondary | `#171A22` | `#FFFFFF` | nav bar, sheets |
| Card | `#1B1F29` | `#FFFFFF` | surfaces |
| Elevated | `#242936` | `#EEF0F6` | inputs, chips |
| Accent | `#8B7CFF` | `#6C5CE7` | primary actions, selected state |
| Positive | `#39D6A3` | `#149E77` | win rate, wins |
| Negative | `#EF6464` | `#D64545` | losses, weak-against |
| Warning | `#F5B85B` | `#B7791F` | caveats (player-data notice) |
| Text primary | `#F5F5F7` | `#14161C` | headings, values |
| Text secondary | `#A4A8B4` | `#4B5162` | body |
| Text muted | `#747B8B` | `#8A90A2` | labels, captions |
| Border | `#262B38` | `#E2E5EE` | hairlines |

Contrast targets WCAG AA. Positive/negative are never the *only* signal
(icons/labels accompany them).

## Typography

- **Manrope** — headings/titles (weights 600–800).
- **Inter** — body and statistics; numeric styles use `tabularFigures()` so
  columns of stats align.
- Scale exposed via `AppTypography.textTheme(palette)`; large numbers via
  `AppTypography.statNumber(palette)`.

## Spacing & shape

- 8-point scale: `2,4,8,12,16,24,32,48`. Page gutter `16`.
- Radii: cards `14`, large `18`, controls `10`, chips pill.
- Minimum touch target `48`. Hairline borders instead of shadows.

## Components (`shared/widgets`)

`AppCard` · `AppPrimaryButton` · `AppTextField` · `StatTile` · `SectionHeader` ·
`HeroAvatar` + `RoleTag` · `LoadingView` / `EmptyView` / `ErrorView`.

## Information architecture — 5 tabs

1. **Home** — search entry, trending heroes (real win-rate leaders), explore, dev notice.
2. **Players** — Player ID + Zone ID search, validation, recent searches, profile/unavailable states.
3. **Heroes** — role-filtered grid → hero detail.
4. **Ranks** — meta rankings with sort + window chips.
5. **Saved** — favourited heroes + theme toggle.

## States & accessibility

- Every list has loading, empty, error (with retry), and — for players — an
  explicit **"not available from public data"** state.
- Progressive disclosure: overview first, detail on demand.
- Semantic labels on inputs; contrast-checked colors; large touch targets;
  layouts reflow for narrow screens.

## Motion

Restrained: Material ripple, `RefreshIndicator`, subtle chip/selection changes.
No gratuitous glow or animation that competes with data.
