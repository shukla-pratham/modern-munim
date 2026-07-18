

# FF Marketplace — Elite Interactive Command Center

## Overview
An AI-powered internal operations platform with premium depth, layered motion, and enterprise-grade visual polish. Built with Vite + React, Framer Motion, Recharts, and Shadcn UI. Dark theme default, mock data first.

---

## 1. Design System & Foundation

### Color System (Dark-first)
- **Base:** Deep Midnight Navy `#0B1120` with subtle noise texture overlay
- **Electric Blue `#2563EB`:** Primary buttons, active nav, focused states
- **Neon Cyan `#06B6D4`:** Data highlights, positive metrics, sparklines
- **Orange `#F97316`:** Risk alerts, warnings, action buttons only
- **Magenta `#EC4899`:** AI-driven components exclusively
- **Emerald `#10B981`:** High-performance vendor scores
- **Soft Red `#EF4444`:** Critical stockout / vendor issues
- **Rule:** Never mix orange + magenta in same component

### Depth & Layers
- Subtle background noise texture on base layer
- Radial gradient blobs behind KPI sections (soft cyan/blue glows)
- Floating blur glows behind AI alert cards
- 3-tier elevation system: base → raised → focus
- Ambient slow-moving gradient animation on dashboard background

### Global Motion Rules (Framer Motion)
- **Page transitions:** Fade + upward slide (250ms ease)
- **Staggered entry:** 60ms per element, scale 0.98→1 + fade
- **Numbers:** Count-up with easing curves
- **Buttons:** Subtle press scale (0.97) + ripple effect
- **Hover:** Soft lift (translateY -2px) + glow intensification
- **Skeleton loaders** on initial data load
- **Smooth page transitions** between routes

---

## 2. Layout & Navigation

### Sidebar
- Collapsible with smooth width animation (full ↔ icon-only mini mode)
- Active route: animated left border accent (Electric Blue)
- Hover: soft glow effect + tooltip in mini mode
- Nav items for all 7 planned pages; unbuilt pages show subtle "Coming Soon" badge
- Pages: Dashboard, Inventory (coming soon), Vendors, Purchase Orders (coming soon), Expenses (coming soon), AI Insights (coming soon)

### Top Bar
- Page title with breadcrumb
- Dark/light theme toggle with smooth transition
- Notification bell (static, for visual completeness)

### Responsive Behavior
- Desktop-first layout
- Tablet: sidebar auto-collapses, charts stack vertically, comparison mode becomes full-screen overlay

---

## 3. Page: Login

- Full-screen gradient background (navy → deep blue) with ambient animation
- Centered floating glass card with subtle blur backdrop
- Logo/brand area at top
- Email + password fields with focus glow
- Animated login button: loading spinner state, press animation
- Mock auth → redirects to dashboard
- Staggered fade-in for form elements

---

## 4. Page: Admin Dashboard (Main Intelligence Screen)

### Top KPI Row (Control Panel Feel)
5 animated stat cards in a row:
- **Inventory Health Score** — radial gauge, cyan accent
- **Monthly Expenses vs Budget** — progress bar with comparison
- **Vendor Reliability Average** — percentage with trend arrow
- **Stockout Risk Summary** — orange accent when high risk
- **Active AI Alerts** — magenta glowing border, pulsing animation

Each card includes:
- Count-up animated number
- Micro labels: "Updated 2h ago", "Trend ↑ 3.2%"
- Hover: glow intensifies, subtle scale
- AI alert card: border shimmer animation

### Charts Grid (2×2)
- **Sales Trend** — animated line chart drawing on mount
- **Inventory Movement** — bars grow upward smoothly
- **Expense Breakdown** — donut with progressive stroke draw
- **Vendor Performance Trend** — multi-line with animated entry

Each chart includes:
- Sub-header describing the metric
- Animated legend indicators
- Premium hover tooltips (glass-style)

### AI Alerts Section (Bottom)
- Darker glass container, visually distinct
- Neon magenta border glow
- Each alert card shows: title, risk level badge, confidence % (animated radial progress)
- Expandable "Why?" explanation drawer with smooth height transition
- Recommended action text
- Staggered card entry animation

### Background Effects
- Radial gradient blobs behind KPI section
- Subtle ambient gradient animation

---

## 5. Page: Vendor Intelligence (Star Screen)

### Vendor Grid
Cards with premium design showing:
- **Large animated overall score** (prominent, count-up)
- **Reliability & Cost sub-scores** with colored bars
- Mini trend sparkline (last 6 months)
- Risk level badge (color-coded: emerald/cyan/orange/red)
- Lead time indicator
- **Rank #1 vendor:** animated glowing ring on badge

Card interactions:
- Hover: subtle 3D tilt effect (Framer Motion)
- Selected state: animated gradient border
- Staggered grid entry

### Search & Filtering
- Search bar with smooth filtering animation
- Sorting dropdown (animated open/close)
- Filter chips by risk level (animated add/remove)

### Comparison Mode
When 2 vendors selected:
- Background blurs slightly
- Comparison panel slides up from bottom
- Side-by-side animated score bars
- Radar chart comparing dimensions
- Price volatility mini sparkline
- On-time delivery rate gauge
- Animated transitions when switching vendor selection
- Close button returns to grid with reverse animation

---

## 6. Data & Architecture

### Mock Data Services
- `src/data/mockDashboard.ts` — KPI values, chart data, AI alerts
- `src/data/mockVendors.ts` — vendor profiles, scores, history
- `src/data/types.ts` — TypeScript interfaces for all entities

### Reusable Components
- `AnimatedNumber` — count-up with easing
- `GlassCard` — frosted glass effect card
- `StatCard` — KPI card with icon, trend, micro-label
- `ChartWrapper` — consistent styled Recharts container
- `RadialProgress` — animated confidence/score gauge
- `StatusBadge` — color-coded risk/status badges
- `SkeletonCard` — loading placeholder
- `RippleButton` — button with ripple + press animation

### Folder Structure
- `src/components/layout/` — Sidebar, TopBar, MainLayout
- `src/components/dashboard/` — KPI cards, charts, alerts
- `src/components/vendors/` — vendor cards, comparison panel
- `src/components/shared/` — reusable animated components
- `src/data/` — mock data + types
- `src/pages/` — Login, Dashboard, VendorIntelligence

---

## 7. Micro-Interactions & Polish
- Button ripple effect on click
- Soft hover lift on all interactive cards
- Subtle click press animation (scale 0.97)
- Skeleton loaders before data renders
- Animated empty states
- Smooth loading transitions between pages
- Theme toggle with crossfade transition

