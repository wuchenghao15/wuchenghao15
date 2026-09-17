# Axon Web UI — Frontend Specification

> A terminal-inspired, keyboard-driven graph exploration interface for Axon's code intelligence engine.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Design System](#3-design-system)
4. [Views & Navigation](#4-views--navigation)
5. [Explorer View](#5-explorer-view)
6. [Analysis Dashboard](#6-analysis-dashboard)
7. [Cypher Console](#7-cypher-console)
8. [Command Palette](#8-command-palette)
9. [Keyboard Shortcuts](#9-keyboard-shortcuts)
10. [State Management](#10-state-management)
11. [API Endpoints](#11-api-endpoints)
12. [Live Reload](#12-live-reload)
13. [Implementation Phases](#13-implementation-phases)

---

## 1. Overview

### 1.1 What This Is

A local web UI for Axon that launches via `axon ui`. It visualizes the full knowledge graph, surfaces all analysis features (dead code, coupling, impact, execution flows, communities), and provides every capability available in the CLI — but visual and interactive.

### 1.2 Design Philosophy

**Terminal power tool, not a consumer app.** Data-dense, keyboard-driven, monospace-everything. Think htop meets a graph database visualizer. Distinctly different from GitNexus's sleek void/cyan aesthetic.

### 1.3 Non-Goals (v1)

- AI/LLM chat panel (MCP server already provides this via Claude Code/Cursor)
- Browser-only WASM mode (we run a real Python backend)
- Multi-user / remote deployment
- Real-time collaboration

---

## 2. Architecture

### 2.1 Serving Model

```
┌─────────────────────────────────────────────┐
│  axon ui [--port 8420] [--watch] [--no-open]│
│                                             │
│  ┌─────────────┐    ┌────────────────────┐  │
│  │  FastAPI     │    │  React SPA         │  │
│  │  REST API    │◄──►│  (static bundle)   │  │
│  │  /api/*      │    │  Vite build output │  │
│  └──────┬───────┘    └────────────────────┘  │
│         │                                    │
│  ┌──────▼───────┐                            │
│  │  KuzuDB      │                            │
│  │  .axon/kuzu/ │                            │
│  └──────────────┘                            │
└─────────────────────────────────────────────┘
```

- **New CLI command**: `axon ui`
  - Starts FastAPI on `localhost:8420` (configurable via `--port`)
  - Serves the REST API + static frontend bundle
  - Auto-opens the browser (disable with `--no-open`)
  - Optional `--watch` flag enables live file watching + auto-reindex
  - Reads from existing `.axon/kuzu/` storage (read-only)
- Separate from `axon serve` (MCP stdio server) — different concerns

### 2.2 Code Organization

```
src/axon/
├── web/
│   ├── __init__.py
│   ├── app.py                  # FastAPI app factory
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── graph.py            # GET /api/graph, GET /api/node/:id
│   │   ├── search.py           # POST /api/search
│   │   ├── analysis.py         # GET /api/dead-code, /api/coupling, /api/health
│   │   ├── files.py            # GET /api/file, GET /api/tree
│   │   ├── cypher.py           # POST /api/cypher
│   │   ├── diff.py             # POST /api/diff
│   │   ├── processes.py        # GET /api/processes, /api/process/:name
│   │   └── events.py           # SSE /api/events (live reload)
│   └── frontend/               # React app
│       ├── package.json
│       ├── vite.config.ts
│       ├── tsconfig.json
│       ├── tailwind.css
│       ├── components.json     # shadcn/ui config
│       ├── index.html
│       ├── public/
│       └── src/
│           ├── main.tsx
│           ├── App.tsx
│           ├── index.css
│           ├── api/            # API client (ky-based)
│           ├── components/
│           │   ├── ui/         # shadcn/ui primitives
│           │   ├── graph/      # Sigma.js canvas, minimap, controls
│           │   ├── explorer/   # File tree, filters, sidebar tabs
│           │   ├── analysis/   # Dashboard cards, heatmap, trees
│           │   ├── cypher/     # Query editor, results table
│           │   └── shared/     # Header, status bar, palette
│           ├── hooks/          # Custom React hooks
│           ├── stores/         # Zustand stores
│           ├── lib/            # Utilities, constants, adapters
│           └── types/          # TypeScript type definitions
```

### 2.3 Frontend Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Framework | React 18 + TypeScript | Largest ecosystem for graph viz libs |
| Build | Vite | Fast HMR, ESM-native |
| Styling | Tailwind CSS v4 | Utility-first, pairs with shadcn |
| Components | shadcn/ui | Composable primitives (tabs, dialogs, tooltips, tables, etc.) |
| State | Zustand | Lightweight, no boilerplate, works with refs |
| Graph Viz | Sigma.js v3 + Graphology | WebGL, handles 10k+ nodes, ForceAtlas2 |
| Graph Layout | graphology-layout-forceatlas2 + noverlap | Physics layout + overlap cleanup |
| Code Highlighting | Shiki | Terminal-grade themes, fits aesthetic |
| HTTP Client | ky | Tiny fetch wrapper, cleaner than axios |
| Icons | Lucide React | Consistent, tree-shakeable |
| Fonts | JetBrains Mono, IBM Plex Mono | Monospace-first design |

### 2.4 shadcn/ui Components Used

These shadcn primitives form the UI foundation (customized to match terminal theme):

| Component | Usage |
|-----------|-------|
| `Tabs` | Sidebar tabs, right panel tabs, top-level view switcher |
| `Command` | Command palette (⌘K) — built on cmdk |
| `Dialog` | Modals (branch diff input, settings) |
| `Table` | Cypher results, dead code report, coupling list |
| `Tooltip` | Node hover info, button descriptions |
| `ScrollArea` | All scrollable panels (file tree, results, code) |
| `Badge` | Node type badges, confidence tags, status indicators |
| `Button` | Actions, controls |
| `Input` | Search inputs, branch name inputs |
| `Separator` | Panel dividers |
| `Slider` | Depth control |
| `Toggle` | Filter toggles for node/edge types |
| `ToggleGroup` | Layout mode selector (Force/Tree/Radial) |
| `Resizable` | Panel resizing (left sidebar, right panel) |
| `Sheet` | Mobile/narrow viewport fallback panels |
| `Collapsible` | File tree folders, community member lists |
| `DropdownMenu` | Query history, preset queries |
| `Kbd` | Keyboard shortcut hints |

---

## 3. Design System

### 3.1 Visual Identity — "Terminal Power Tool"

The UI should feel like a sophisticated terminal application that happens to run in a browser. Every pixel should reinforce the developer-tool identity.

**What this is NOT:**
- Not sleek/minimal like Linear
- Not void/cyan like GitNexus
- Not Material/corporate like Jira
- Not playful/rounded like Notion

**What this IS:**
- Dense like htop/btop
- Sharp like a terminal emulator
- Grid-lined like a database tool
- Monospace like a code editor

### 3.2 Color Tokens

```css
:root {
  /* Backgrounds */
  --bg-primary:     #0a0e14;    /* Deep navy-black — main background */
  --bg-surface:     #131820;    /* Elevated surfaces (panels, cards) */
  --bg-elevated:    #1a2030;    /* Higher elevation (modals, dropdowns) */
  --bg-hover:       #1e2a3a;    /* Interactive hover state */
  --bg-active:      #0d2818;    /* Active/selected state (green tint) */

  /* Borders */
  --border:         #1e2530;    /* Default borders — subtle, grid-like */
  --border-focus:   #39d353;    /* Focused elements — terminal green */
  --border-muted:   #151b24;    /* Very subtle separators */

  /* Text */
  --text-primary:   #c5ced6;    /* Body text — cool gray */
  --text-secondary: #6b7d8e;    /* Muted/helper text */
  --text-bright:    #e6edf3;    /* Headings, emphasis */
  --text-dimmed:    #3d4f5f;    /* Disabled, de-emphasized */

  /* Accent — Terminal Green (primary) */
  --accent:         #39d353;    /* Primary accent — terminal green */
  --accent-dim:     #1a4d2e;    /* Green tinted backgrounds */
  --accent-muted:   #238636;    /* Less intense green */

  /* Semantic */
  --info:           #58a6ff;    /* Blue — informational, links */
  --warning:        #e5a839;    /* Amber — warnings, coupling */
  --danger:         #f85149;    /* Red — errors, dead code, breaking */
  --purple:         #a371f7;    /* Purple — communities, types, inheritance */
  --cyan:           #3fb8af;    /* Teal — processes, flows */
  --orange:         #f0883e;    /* Orange — depth 2, indirect impact */
  --yellow:         #d4a72c;    /* Yellow — depth 3+, transitive impact */

  /* Graph Node Colors */
  --node-function:  #39d353;    /* Green */
  --node-class:     #58a6ff;    /* Blue */
  --node-method:    #a371f7;    /* Purple */
  --node-interface: #3fb8af;    /* Teal */
  --node-typealias: #56d4dd;    /* Cyan */
  --node-enum:      #f0883e;    /* Orange */
  --node-file:      #6b7d8e;    /* Gray */
  --node-folder:    #4d5969;    /* Dark gray */
  --node-community: #a371f7;    /* Purple (hull fill at 10% opacity) */
  --node-process:   #3fb8af;    /* Teal */
}
```

### 3.3 Typography

- **Body / Data / Labels**: JetBrains Mono, 12px, weight 400
- **Section Headings**: IBM Plex Mono, 13px, weight 600, letter-spacing 0.5px
- **View Titles**: IBM Plex Mono, 14px, weight 700, uppercase, letter-spacing 1px
- **Code**: JetBrains Mono, 12px (same as body — monospace everywhere)
- **Tiny Labels**: JetBrains Mono, 10px, weight 400, `--text-secondary`
- **Counts / Badges**: JetBrains Mono, 11px, weight 500

### 3.4 Spacing & Borders

- Border radius: **2px** maximum. No rounded corners > 4px. Terminal-sharp.
- Panel padding: 8px (compact)
- List item padding: 4px vertical, 8px horizontal
- Section gaps: 12px
- All panel edges: 1px solid `--border`
- Panel dividers: draggable resize handles (3px hit area, 1px visible line)
- No shadows anywhere. No gradients. Flat surfaces.

### 3.5 Interaction States

| State | Visual |
|-------|--------|
| Hover | `--bg-hover` background, optional `--accent` left-border flash (2px) |
| Focus | `--border-focus` ring (1px green outline) |
| Active/Selected | `--bg-active` background + `--accent` left-border (2px solid) |
| Disabled | `--text-dimmed` text, no interaction |
| Loading | Pulsing green dot + `--text-secondary` status text |

### 3.6 shadcn/ui Theme Overrides

All shadcn components are re-themed to match the terminal aesthetic:
- Remove all default rounded corners (set to 2px)
- Replace the default blue accent with `--accent` (terminal green)
- Set all dialog/dropdown backgrounds to `--bg-elevated`
- Monospace font on all components (override Inter/sans-serif defaults)
- Remove box shadows, use 1px borders instead
- Reduce default padding by ~30% for data density

---

## 4. Views & Navigation

Three top-level views, accessible via tabs in the header.

### 4.1 Header Bar

```
┌────────────────────────────────────────────────────────────────────────┐
│  ⬡ AXON    [Explorer]  [Analysis]  [Cypher]        1,247 ● 3,482 ─  [⌘K]  [⟳]  │
└────────────────────────────────────────────────────────────────────────┘
```

- **Left**: Axon logo (hexagonal graph icon) + "AXON" in IBM Plex Mono, uppercase, 14px
- **Center**: View tabs — `Explorer`, `Analysis`, `Cypher`
  - Active tab: `--accent` underline (2px) + `--text-bright` text
  - Inactive tabs: `--text-secondary` text
- **Right**:
  - Live stats: `1,247 ●` (nodes, green dot) + `3,482 ─` (edges, dash) — monospace, small
  - Command palette trigger: `⌘K` in a `<Kbd>` component
  - Reindex button: `⟳` icon, pulses green when reindexing
- **Height**: 40px. Compact, single-row.

### 4.2 Status Bar (Bottom)

```
┌────────────────────────────────────────────────────────────────────────┐
│  ● indexed 2m ago    │  python    │  12 communities    │  3 dead    │  health: 87    │
└────────────────────────────────────────────────────────────────────────┘
```

- **Height**: 24px. Minimal, terminal-style.
- All text: JetBrains Mono, 10px, `--text-secondary`
- Status dot: `●` green (up to date), amber (reindexing), red (stale/error)
- Pipe separators (`│`) between sections
- Click "health: 87" → navigates to Analysis dashboard
- Click "3 dead" → opens Dead Code tab in sidebar

---

## 5. Explorer View (Primary)

The main graph exploration workspace. Three resizable panels.

### 5.1 Layout

```
┌────────────────────────────────────────────────────────────────┐
│  Header                                                        │
├────────────┬──────────────────────────────────┬────────────────┤
│            │                                  │                │
│  Left      │       Graph Canvas               │  Right Panel   │
│  Sidebar   │       (Sigma.js WebGL)           │                │
│            │                                  │                │
│  260px     │       (fills remaining)          │  340px         │
│  resizable │                                  │  resizable     │
│            │                          [mini]  │                │
├────────────┴──────────────────────────────────┴────────────────┤
│  Status Bar                                                    │
└────────────────────────────────────────────────────────────────┘
```

- **Left sidebar**: 260px default, resizable 200-400px, collapsible (`⌘1`)
- **Graph canvas**: fills all remaining horizontal space
- **Right panel**: 340px default, resizable 280-500px, collapsible (`⌘3`)
- **Resizing**: use shadcn `Resizable` component for panel dividers

### 5.2 Left Sidebar — Multi-Tab

Four tabs indicated by icons at the top of the sidebar. Use shadcn `Tabs` component.

#### Tab 1: Explorer (folder icon)

Hierarchical file/folder tree built from the graph's Folder and File nodes.

- **Search filter**: text input at top, filters tree by file name
- **Folder nodes**: collapsible (shadcn `Collapsible`), show child count badge
- **File nodes**: show language-colored dot + symbol count badge
- **Expand file**: shows symbols defined in that file (Function, Class, Method, etc.) as children
- **Click file** → highlights all symbols from that file on the graph
- **Click symbol** → selects that specific node on the graph, loads context in right panel
- **Auto-expand**: when a node is selected on the graph, the tree auto-expands to show its file
- **Indentation**: 12px per level
- **Icons**: folder icon (collapsed/expanded), file icons by language, symbol type icons

#### Tab 2: Filters (sliders icon)

Controls what's visible on the graph canvas.

**Node type toggles** (shadcn `Toggle` with color swatch):
```
  [✓] ● Function      [✓] ● Class
  [✓] ● Method         [✓] ● Interface
  [ ] ● TypeAlias      [ ] ● Enum
  [ ] ● File           [ ] ● Folder
  [ ] ● Community      [ ] ● Process
```
- Each toggle has a colored dot matching `--node-*` colors
- Toggling hides/shows those node types on the graph

**Edge type toggles**:
```
  [✓] ── CALLS         [✓] ╌╌ IMPORTS
  [ ] ── EXTENDS        [ ] ── IMPLEMENTS
  [ ] ── USES_TYPE      [ ] ── COUPLED_WITH
```
- Solid line swatch for each, colored by edge type

**Depth control** (shadcn `Slider` + number buttons):
```
  Focus depth:  [1]  [2]  [3]  [5]  [All]
```
- When a node is selected, depth limits the visible neighborhood
- Grayed out with "select a node first" hint when nothing selected
- `All` shows the full graph

**Layout selector** (shadcn `ToggleGroup`):
```
  Layout:  [Force]  [Tree]  [Radial]
```
- Force: ForceAtlas2 (default)
- Tree: dagre hierarchical layout (top-down based on CALLS/DEFINES)
- Radial: radial layout from selected node (or most-connected node)

#### Tab 3: Communities (grid icon)

List of all detected community clusters.

- Each entry: colored swatch + community name + member count + cohesion score bar
- **Click community** → highlights all members on graph + draws convex hull
- **Expand community** (shadcn `Collapsible`) → shows member symbols with type badges
- **Click member** → selects that node on graph
- **Sort by**: name, member count, cohesion (dropdown)
- **"Highlight all"** button → draws all community hulls simultaneously

#### Tab 4: Dead Code (skull icon)

List of all `is_dead = true` symbols, grouped by file.

- **Header**: "Dead Code (N symbols)" with danger badge
- **Grouped by file**: file path as section header, symbols as items below
- Each item: type badge (`ƒ`, `C`, `M`) + symbol name + `:line`
- **Click symbol** → selects on graph, node pulses red
- **"Show all on graph"** button → dims everything except dead nodes (red glow)
- **"Clear highlight"** button → restores normal view

### 5.3 Graph Canvas

Sigma.js v3 over Graphology, WebGL-rendered. The core visual element.

#### 5.3.1 Data Loading

1. On mount: `GET /api/graph` → parse JSON → create Graphology instance
2. Apply node/edge attributes (color, size, label, type metadata)
3. Start ForceAtlas2 in a web worker
4. Show progress: "Optimizing layout..." with elapsed time
5. After layout converges (20-45s depending on graph size), run noverlap pass
6. Display "Layout complete" in status bar

#### 5.3.2 Node Rendering

- **Shape**: circles (Sigma default — most performant)
- **Size**: proportional to degree (connection count)
  - Min: 4px, Max: 20px
  - Formula: `4 + Math.min(16, Math.sqrt(degree) * 2)`
- **Color**: by node type, using `--node-*` tokens
- **Label**: symbol name
  - Shown on hover always
  - Shown when zoomed in past threshold (Sigma adaptive label rendering)
  - Font: JetBrains Mono, 11px
- **Dead nodes**: additional dashed red border ring (always visible, regardless of zoom)
- **Entry points**: small green diamond indicator overlay

#### 5.3.3 Edge Rendering

| Edge Type | Style | Color | Opacity |
|-----------|-------|-------|---------|
| CALLS | Solid line | `--text-dimmed` | `confidence * 0.6` |
| IMPORTS | Dashed line | `--text-dimmed` | 0.3 |
| EXTENDS | Solid arrow | `--purple` | 0.5 |
| IMPLEMENTS | Dashed arrow | `--purple` | 0.4 |
| USES_TYPE | Dotted line | `--cyan` | 0.3 |
| COUPLED_WITH | Thick solid | `--warning` | `strength * 0.8` |

- Default: very low opacity (edges are noise until needed)
- **On hover/select**: connected edges brighten to full opacity + thicken
- **Unrelated edges**: fade to near-invisible when a node is selected

#### 5.3.4 Community Convex Hulls

- Each community gets a distinct color (cycled from a palette of 12 colors)
- Hull: translucent fill (8% opacity) + 1px border (30% opacity)
- Label: community name in small monospace text, positioned at hull centroid
- Toggleable: `L` key or Filter tab toggle
- Hulls are computed from the positions of member nodes after layout

#### 5.3.5 Interactions

| Action | Behavior |
|--------|----------|
| **Hover node** | Highlight node + all direct neighbors + connecting edges. Tooltip: name, type, file:line |
| **Click node** | Select. Right panel loads context. Neighbors highlighted. Others dim to 20% opacity |
| **Click canvas** | Deselect all, restore full view |
| **Drag node** | Reposition + pin in place |
| **Scroll wheel** | Zoom in/out |
| **Drag canvas** | Pan |
| **Double-click node** | Zoom to fit that node's neighborhood (depth 2) |

#### 5.3.6 Minimap

- Position: bottom-right corner of the graph canvas
- Size: 160x120px
- Shows: full graph as tiny dots (simplified render)
- Viewport rectangle: shows current visible area, outlined in `--accent`
- Drag rectangle to navigate
- Toggle with `M` key
- Background: `--bg-surface` with `--border` outline

#### 5.3.7 Zoom Controls

Floating button group, bottom-left of graph canvas:
- `+` zoom in
- `−` zoom out
- `⟐` fit to screen
- `▶/⏸` play/pause layout engine

Style: `--bg-surface` background, `--border` outline, `--accent` on hover. Small (24px buttons).

#### 5.3.8 Impact Analysis — Animated Ripple

Triggered when user clicks "Analyze Impact" in the right panel or presses `I`.

1. Call `GET /api/impact/:id?depth=3`
2. **Target node**: white glow, scale 2x
3. **Depth 1 nodes** (direct callers): animate to `--danger` red, scale 1.5x — immediately
4. **Depth 2 nodes**: animate to `--orange`, scale 1.3x — after 300ms delay
5. **Depth 3+ nodes**: animate to `--yellow`, scale 1.1x — after 600ms delay
6. **All other nodes**: dim to 15% opacity
7. **Edges in blast path**: glow with matching depth color, thicken
8. Animation runs once then **holds** until user clicks canvas to reset
9. A banner at the top of the graph shows: "Impact: {name} — {total} affected symbols"

#### 5.3.9 Execution Flow — Animated Trace

Triggered when user clicks a process in the right panel's Processes tab.

1. Load process steps in order
2. **Particle animation**: a small green circle (6px) starts at the entry point node
3. Particle travels along each CALLS edge, following the step order
4. Speed: ~400ms per step (configurable)
5. Each node lights up `--accent` green as the particle reaches it, with a brief scale-up pulse
6. **Trail effect**: edges glow `--accent` behind the particle, fading over 1 second
7. Cross-community transitions: hull boundary flashes briefly
8. **Controls**: "Replay" and "Pause" buttons appear as a floating overlay
9. On completion: all flow nodes stay highlighted, rest dimmed

#### 5.3.10 Live Reload Animations

When the file watcher detects changes (via SSE):

| Change | Animation |
|--------|-----------|
| New node | Fade-in + green glow pulse (3 cycles, 500ms each) |
| Removed node | Red flash + fade-out (1s) |
| Modified node | Amber flash pulse (2 cycles, 400ms each) |

After change animations, ForceAtlas2 runs a short settling pass (~5s) to accommodate new/removed nodes.

### 5.4 Right Panel — Detail Tabs

Four tabs: **Context** | **Impact** | **Code** | **Processes**

Use shadcn `Tabs` component. Auto-populated when a node is selected. Empty state: "Select a node on the graph" hint text.

#### Tab: Context (default, auto-loaded on node select)

Equivalent to `axon context <symbol>`. Calls `GET /api/node/:id`.

```
┌─────────────────────────────────┐
│  ƒ run_pipeline                 │
│  Function · pipeline.py:45-120  │
│  Community: Ingestion           │
│  ● ENTRY POINT                  │
├─────────────────────────────────┤
│  SIGNATURE                      │
│  def run_pipeline(              │
│    graph: KnowledgeGraph,       │
│    repo_path: Path              │
│  ) -> PipelineResult            │
├─────────────────────────────────┤
│  CALLERS (8)            ▼ expand│
│  ├ analyze()     pipeline.py    │
│  ├ reindex()     watcher.py   ~ │
│  └ test_pipe()   test.py      ? │
│    + 5 more                     │
├─────────────────────────────────┤
│  CALLEES (5)            ▼ expand│
│  ├ walk_repo()   walker.py      │
│  ├ process_..()  parser.py      │
│  └ bulk_load()   kuzu.py        │
│    + 2 more                     │
├─────────────────────────────────┤
│  TYPE REFS (2)                  │
│  ├ KnowledgeGraph  graph.py     │
│  └ FileEntry       walker.py    │
├─────────────────────────────────┤
│  [Analyze Impact]  [Show Code]  │
└─────────────────────────────────┘
```

- **Symbol header**: type icon + name, type badge, file:line range
- **DEAD CODE** badge (red, prominent) if `is_dead = true`
- **Community membership**: community name, clickable → highlights hull on graph
- **Confidence tags**: none (>=0.9), `~` (0.5-0.9), `?` (<0.5)
- **Click any caller/callee** → navigates to that node on graph, loads its context
- **Collapsible sections**: initially show top 3, "show all" expands (shadcn `Collapsible`)
- **Action buttons**: "Analyze Impact" (→ switches to Impact tab), "Show Code" (→ switches to Code tab)

#### Tab: Impact

Shows blast radius for the selected node.

- Header: "Impact Analysis: {name}" + total affected count
- Depth sections, each collapsible:
  - **Depth 1 — Direct callers (will break)** — `--danger` red accent
  - **Depth 2 — Indirect (may break)** — `--orange` accent
  - **Depth 3+ — Transitive (review)** — `--yellow` accent
- Each entry: type badge + name + file:line + confidence (for depth 1)
- Click entry → navigates to that node
- **"Visualize on Graph"** button → triggers animated ripple (section 5.3.8)
- **Depth slider**: adjust 1-10 (re-fetches from API)

#### Tab: Code

Syntax-highlighted source code of the selected node's file.

- **File breadcrumb** at top: `src / axon / core / ingestion / pipeline.py`
- **Full file** with line numbers, rendered via Shiki
  - Theme: custom terminal-dark matching `--bg-primary` and `--accent` colors
- **Symbol highlight**: the selected symbol's line range gets:
  - Green left-border (2px, `--accent`)
  - Translucent green background (`--accent-dim` at 15%)
- **Auto-scroll**: scrolled to the symbol's start line on load
- **Line numbers**: clickable (no-op for now, future: set breakpoint / annotation)
- Wrapped in shadcn `ScrollArea` for smooth scrolling

#### Tab: Processes

Execution flows involving the selected symbol.

- **Header**: "Processes involving {name}" + count
- **Two groups** (shadcn `Collapsible`):
  - **Cross-community flows**: flows that span multiple communities
  - **Intra-community flows**: flows within a single community
- Each entry:
  - Process name (truncated with tooltip for long names)
  - Kind badge: `cross` (purple) or `intra` (teal)
  - Step count: `{N} steps`
  - **"Trace"** button → triggers animated flow trace (section 5.3.9)
  - **"Highlight"** button → highlights all steps on graph (no animation, just static glow)
- Click process name → scrollable step list expands inline
  - Each step: `{step_number}. {type_badge} {name} → {file:line}`
  - Click step → navigates to that node on graph

---

## 6. Analysis Dashboard

A dedicated view for code quality analysis. Data-dense dashboard layout.

### 6.1 Layout

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Header  [Explorer]  [█Analysis█]  [Cypher]                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌── Health Score ─────┐  ┌── Quick Stats ─────────────────────────────┐ │
│  │                     │  │                                            │ │
│  │   87 / 100          │  │  files: 124       symbols: 1,247          │ │
│  │   ██████████░░       │  │  relationships: 3,482                     │ │
│  │                     │  │  communities: 12  processes: 34            │ │
│  │  dead:    95/100    │  │  dead: 3          coupled: 18 pairs        │ │
│  │  coupling: 82/100   │  │  avg confidence: 0.87                      │ │
│  │  modularity: 78/100 │  │  entry points: 22                          │ │
│  │  confidence: 87/100 │  │                                            │ │
│  │  coverage: 91/100   │  │                                            │ │
│  └─────────────────────┘  └────────────────────────────────────────────┘ │
│                                                                          │
│  ┌── Dead Code Report ──────────────┐  ┌── Coupling Heatmap ──────────┐ │
│  │                                  │  │                              │ │
│  │                                  │  │                              │ │
│  │  (see 6.3)                       │  │  (see 6.4)                   │ │
│  │                                  │  │                              │ │
│  │                                  │  │                              │ │
│  └──────────────────────────────────┘  └──────────────────────────────┘ │
│                                                                          │
│  ┌── Inheritance Hierarchy ─────────┐  ┌── Branch Diff ───────────────┐ │
│  │                                  │  │                              │ │
│  │                                  │  │                              │ │
│  │  (see 6.5)                       │  │  (see 6.6)                   │ │
│  │                                  │  │                              │ │
│  │                                  │  │                              │ │
│  └──────────────────────────────────┘  └──────────────────────────────┘ │
│                                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│  Status Bar                                                              │
└──────────────────────────────────────────────────────────────────────────┘
```

Cards use `--bg-surface` background with `--border` outline, 2px radius. Section headers in IBM Plex Mono, 13px, uppercase.

### 6.2 Code Health Score

Composite score 0-100, computed server-side at `GET /api/health`.

| Metric | Weight | Calculation |
|--------|--------|-------------|
| Dead code ratio | 25% | `100 - (dead_symbols / total_symbols * 100)` |
| Coupling health | 20% | `100 - (high_coupling_pairs / total_pairs * 200)` where high = strength > 0.7 |
| Community modularity | 20% | `modularity_score * 100` (from Leiden) |
| Call confidence | 20% | `avg(confidence) * 100` across all CALLS edges |
| Process coverage | 15% | `symbols_in_processes / callable_symbols * 100` |

**Display**:
- Large number (48px, IBM Plex Mono, bold)
- Circular progress ring behind the number
- Ring color: green (80+), amber (50-79), red (<50)
- Below: 5 horizontal bars showing individual metric scores
- Each bar: metric name (left), score (right), filled bar (center)

### 6.3 Dead Code Report

A table/list card showing all dead symbols. Uses shadcn `Table`.

| Column | Content |
|--------|---------|
| Type | Badge: `ƒ` Function, `C` Class, `M` Method |
| Symbol | Name (clickable → navigates to Explorer + selects node) |
| File | Relative path |
| Line | Start line number |

- Grouped by file (collapsible sections)
- Header shows total: "Dead Code — 3 symbols in 2 files"
- Row hover: `--bg-hover` with `--danger` left border
- Empty state: "No dead code detected" with green checkmark

### 6.4 Coupling Heatmap

Interactive matrix visualization of COUPLED_WITH relationships.

**Matrix layout:**
- Rows and columns: file paths (shortened to filename if unique)
- Cell color: `--warning` (amber) at varying opacity proportional to strength
  - 0.3 strength → 20% opacity
  - 0.7 strength → 60% opacity
  - 1.0 strength → 100% opacity
- Diagonal: empty (self-coupling is meaningless)
- Files clustered by parent directory for readability

**Interactions:**
- Hover cell: tooltip — `fileA ↔ fileB | strength: 0.72 | co-changes: 8`
- Click cell: expands a detail panel below showing the two file paths, strength, and co-change count
- Sort button: sort files by path (default), max coupling strength, or total coupling count

**Size limits:**
- If >50 coupled files: show top 50 by max strength
- Note at bottom: "Showing top 50 of {N} coupled files"

**Implementation:** Render as an HTML `<canvas>` element for performance with large matrices. Tooltip and click handlers via hit-testing on the canvas coordinates.

### 6.5 Inheritance Hierarchy

Collapsible tree view of class hierarchies, built from EXTENDS and IMPLEMENTS edges.

- **Multiple root trees**: each base class (no parents) starts a tree
- Displayed in a scrollable grid (multiple trees side by side if space allows)
- **Each tree node**:
  - Class name + file:line
  - Method count badge
  - Solid connector line for `EXTENDS`
  - Dashed connector line for `IMPLEMENTS`
- **Click node** → navigates to Explorer view, selects that class on graph
- **Interface nodes**: teal colored, italic name
- Empty state: "No class hierarchies detected"

### 6.6 Branch Diff

Input card for structural branch comparison.

**Input:**
- Two text inputs: "Base branch" + "Compare branch"
- Or single input: `main..feature` range format
- "Compare" button → calls `POST /api/diff`

**Results — Single merged graph:**
- Mini Sigma.js instance embedded in the card (fills card width, ~400px height)
- Color coding:
  - Added nodes: `--accent` green + green edges
  - Removed nodes: `--danger` red + dashed red edges
  - Modified nodes: `--warning` amber
  - Unchanged: dimmed (20% opacity)
- Toggle: "Show all" ↔ "Changes only" (shadcn `ToggleGroup`)
- Summary stats bar: `+12 added  −3 removed  ~8 modified`
- **"Open in Explorer"** button → switches to Explorer view with diff overlay active on the main graph

---

## 7. Cypher Console

A full-screen query workbench for raw graph queries.

### 7.1 Layout

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Header  [Explorer]  [Analysis]  [█Cypher█]                            │
├────────────────────────────────────┬─────────────────────────────────────┤
│                                    │                                     │
│  Query Editor                      │   Graph Preview                     │
│                                    │   (Sigma.js mini instance)          │
│  MATCH (n:Function)                │                                     │
│  WHERE n.is_dead = true            │   ● matching nodes highlighted      │
│  RETURN n.name, n.file_path        │   ○ all other nodes dimmed          │
│                                    │                                     │
│  [▶ Run ⌘↵]  [History ▼]  [📋]   │                                     │
├────────────────────────────────────┤                                     │
│                                    │                                     │
│  Results Table                     │                                     │
│  ┌────────────┬──────────────────┐ │                                     │
│  │ name       │ file_path        │ │                                     │
│  ├────────────┼──────────────────┤ │                                     │
│  │ old_func   │ src/utils.py     │ │                                     │
│  │ unused_cls │ src/models.py    │ │                                     │
│  └────────────┴──────────────────┘ │                                     │
│  12 rows · 23ms                    │                                     │
├────────────────────────────────────┴─────────────────────────────────────┤
│  Status Bar                                                              │
└──────────────────────────────────────────────────────────────────────────┘
```

- **Left half**: Query editor (top) + Results table (bottom), split vertically
- **Right half**: Graph preview (Sigma.js mini instance, shows full graph dimmed)

### 7.2 Query Editor

- Multi-line textarea with monospace font
- Basic Cypher syntax highlighting (keywords: `MATCH`, `WHERE`, `RETURN`, `WITH`, `ORDER BY`, etc.)
- **Auto-complete** (basic): node labels (`Function`, `Class`, etc.) and property names (`name`, `file_path`, etc.)
- `⌘+Enter` or click "Run" to execute
- Error display: red monospace text below editor area

### 7.3 Preset Queries

Dropdown (shadcn `DropdownMenu`) with common queries:

| Label | Query |
|-------|-------|
| All dead code | `MATCH (n:Function) WHERE n.is_dead = true RETURN n.name, n.file_path, n.start_line` |
| Most called | `MATCH ()-[r:CodeRelation]->(t:Function) WHERE r.rel_type = 'calls' RETURN t.name, count(r) AS calls ORDER BY calls DESC LIMIT 20` |
| Import map | `MATCH (a:File)-[r:CodeRelation]->(b:File) WHERE r.rel_type = 'imports' RETURN a.name AS from, b.name AS to` |
| Coupled files | `MATCH (a:File)-[r:CodeRelation]->(b:File) WHERE r.rel_type = 'coupled_with' RETURN a.name, b.name, r.strength ORDER BY r.strength DESC` |
| Entry points | `MATCH (n:Function) WHERE n.is_entry_point = true RETURN n.name, n.file_path` |
| Largest classes | `MATCH (c:Class)<-[r:CodeRelation]-(m:Method) WHERE r.rel_type = 'defines' RETURN c.name, count(m) AS methods ORDER BY methods DESC LIMIT 10` |
| Cross-community calls | `MATCH (a)-[r:CodeRelation]->(b) WHERE r.rel_type = 'calls' AND a.id <> b.id MATCH (a)-[:CodeRelation]->(c1:Community), (b)-[:CodeRelation]->(c2:Community) WHERE c1.id <> c2.id RETURN a.name, b.name, c1.name, c2.name LIMIT 50` |

### 7.4 Query History

- Dropdown showing last 20 queries with timestamps
- Click to load back into editor
- Persisted in `localStorage`
- Each entry: truncated query text (first 60 chars) + timestamp

### 7.5 Results Table

- shadcn `Table` component
- Column headers: from Cypher `RETURN` clause aliases
- Sortable: click column header to sort
- Row hover: `--bg-hover`
- Click row: if a `name` or `id` column exists, highlights matching node on graph preview
- **Footer**: row count + query execution time
- **Export**: "Copy CSV" and "Copy JSON" buttons (clipboard)
- **Pagination**: 50 rows per page, if more than 50 results

### 7.6 Graph Preview

- Mini Sigma.js instance (right half of the view)
- Shows the full graph, dimmed (20% opacity on all nodes)
- Nodes matching query results: highlighted in `--accent` green glow
- Click highlighted node: tooltip with name + type + file
- **"Open in Explorer"** button on each highlighted node → navigates to Explorer with that node selected

---

## 8. Command Palette

Triggered by `⌘K`. Centered overlay, 520px wide. Uses shadcn `Command` component (built on cmdk).

### 8.1 Search Mode (default)

Type a symbol name → instant results from hybrid search (calls `POST /api/search`).

```
┌───────────────────────────────────────┐
│  🔍 run_pipeline                      │
├───────────────────────────────────────┤
│  ƒ  run_pipeline                      │
│     pipeline.py:45  ·  8 callers      │
│───────────────────────────────────────│
│  M  run_pipeline_async                │
│     server.py:12  ·  3 callers        │
│───────────────────────────────────────│
│  ƒ  run_full_pipeline                 │
│     e2e.py:8  ·  1 caller             │
│───────────────────────────────────────│
│  > type '>' for commands              │
└───────────────────────────────────────┘
```

- Debounced search (200ms)
- Results: type badge + name + file:line + caller count
- Max 10 results
- `↑↓` to navigate, `Enter` to select (focuses node on graph + loads context)
- `Escape` to close

### 8.2 Command Mode (prefix `>`)

Type `>` to switch to command mode. Shows available commands.

| Command | Action |
|---------|--------|
| `>impact <name>` | Run impact analysis on a symbol |
| `>dead-code` | Open Dead Code tab in sidebar |
| `>communities` | Open Communities tab in sidebar |
| `>cypher` | Switch to Cypher view |
| `>analysis` | Switch to Analysis view |
| `>explorer` | Switch to Explorer view |
| `>reindex` | Trigger manual reindex |
| `>fit` | Fit graph to screen |
| `>layout force` | Switch to ForceAtlas2 layout |
| `>layout tree` | Switch to dagre tree layout |
| `>layout radial` | Switch to radial layout |
| `>hulls` | Toggle community hulls |
| `>minimap` | Toggle minimap |
| `>filter calls` | Toggle CALLS edge visibility |
| `>filter imports` | Toggle IMPORTS edge visibility |
| `>theme` | Future: toggle light/dark (v2) |

Commands are fuzzy-matched as the user types.

---

## 9. Keyboard Shortcuts

Full keyboard navigation for power users.

### 9.1 Global Shortcuts

| Shortcut | Action |
|----------|--------|
| `⌘K` | Open/close command palette |
| `⌘1` | Toggle left sidebar |
| `⌘2` | Focus graph canvas |
| `⌘3` | Toggle right panel |
| `⌘/` | Switch to Cypher view |
| `⌘E` | Switch to Explorer view |
| `⌘D` | Switch to Analysis (Dashboard) view |
| `Escape` | Deselect node / close palette / close modal |

### 9.2 Graph Shortcuts (when canvas focused)

| Shortcut | Action |
|----------|--------|
| `F` | Fit graph to screen |
| `M` | Toggle minimap |
| `L` | Toggle community hulls |
| `I` | Run impact analysis on selected node |
| `P` | Show processes for selected node |
| `+` / `=` | Zoom in |
| `-` | Zoom out |
| `Tab` | Cycle through neighbors of selected node |
| `Shift+Tab` | Cycle backwards through neighbors |
| `1` | Switch right panel to Context tab |
| `2` | Switch right panel to Impact tab |
| `3` | Switch right panel to Code tab |
| `4` | Switch right panel to Processes tab |

### 9.3 Cypher View Shortcuts

| Shortcut | Action |
|----------|--------|
| `⌘Enter` | Execute query |
| `⌘↑` | Previous query from history |
| `⌘↓` | Next query from history |

---

## 10. State Management

Zustand stores — lightweight, no boilerplate, works well with Sigma.js refs.

### 10.1 Graph Store

```typescript
interface GraphStore {
  // Data
  nodes: GraphNode[];
  edges: GraphEdge[];
  communities: Community[];
  overview: OverviewStats | null;

  // Selection
  selectedNodeId: string | null;
  hoveredNodeId: string | null;

  // Visual overlays
  highlightedNodeIds: Set<string>;
  blastRadiusNodes: Map<string, number>;  // nodeId → depth level
  flowTraceNodeIds: string[];             // ordered step node IDs
  diffOverlay: DiffOverlay | null;        // added/removed/modified sets

  // Filters
  visibleNodeTypes: Set<string>;
  visibleEdgeTypes: Set<string>;
  depthLimit: number | null;              // null = show all
  layoutMode: 'force' | 'tree' | 'radial';

  // Display toggles
  hullsVisible: boolean;
  minimapVisible: boolean;

  // Actions
  selectNode: (id: string | null) => void;
  setBlastRadius: (nodes: Map<string, number>) => void;
  clearBlastRadius: () => void;
  setFlowTrace: (nodeIds: string[]) => void;
  clearFlowTrace: () => void;
  toggleNodeType: (type: string) => void;
  toggleEdgeType: (type: string) => void;
  setDepthLimit: (depth: number | null) => void;
  setLayoutMode: (mode: 'force' | 'tree' | 'radial') => void;
}
```

### 10.2 View Store

```typescript
interface ViewStore {
  // Navigation
  activeView: 'explorer' | 'analysis' | 'cypher';
  setActiveView: (view: string) => void;

  // Panel state
  leftSidebarOpen: boolean;
  leftSidebarTab: 'files' | 'filters' | 'communities' | 'dead-code';
  rightPanelOpen: boolean;
  rightPanelTab: 'context' | 'impact' | 'code' | 'processes';

  // Command palette
  commandPaletteOpen: boolean;

  // Actions
  toggleLeftSidebar: () => void;
  toggleRightPanel: () => void;
  setLeftTab: (tab: string) => void;
  setRightTab: (tab: string) => void;
  toggleCommandPalette: () => void;
}
```

### 10.3 Data Store

```typescript
interface DataStore {
  // Node detail (loaded on select)
  nodeContext: NodeContext | null;   // callers, callees, typeRefs
  impactResult: ImpactResult | null;
  fileContent: FileContent | null;
  nodeProcesses: Process[] | null;

  // Analysis data (loaded on dashboard view)
  healthScore: HealthScore | null;
  deadCode: DeadCodeReport | null;
  couplingData: CouplingPair[] | null;
  allProcesses: Process[] | null;

  // Cypher
  cypherHistory: CypherEntry[];
  cypherResult: CypherResult | null;

  // Loading states
  loading: Record<string, boolean>;
}
```

---

## 11. API Endpoints

All routes served by the FastAPI backend at `localhost:8420`.

### 11.1 Graph Data

| Method | Path | Request | Response |
|--------|------|---------|----------|
| GET | `/api/graph` | — | `{ nodes: GraphNode[], edges: GraphEdge[] }` |
| GET | `/api/node/{node_id}` | — | `{ node, callers: [{node, confidence}], callees: [{node, confidence}], typeRefs: [node], processes: [name] }` |
| GET | `/api/overview` | — | `{ nodesByLabel: {Function: 234, ...}, edgesByType: {calls: 567, ...}, totals: {nodes, edges} }` |

### 11.2 Search

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/api/search` | `{ query: string, limit?: number }` | `{ results: [{ nodeId, score, name, filePath, label, snippet }] }` |

### 11.3 Analysis

| Method | Path | Request | Response |
|--------|------|---------|----------|
| GET | `/api/impact/{node_id}` | `?depth=3` | `{ target: node, affected: number, depths: { "1": [node], "2": [node], "3": [node] } }` |
| GET | `/api/dead-code` | — | `{ total: number, byFile: { "path": [{ name, type, line }] } }` |
| GET | `/api/coupling` | — | `{ pairs: [{ fileA, fileB, strength, coChanges }] }` |
| GET | `/api/communities` | — | `{ communities: [{ id, name, memberCount, cohesion, members: [nodeId] }] }` |
| GET | `/api/processes` | — | `{ processes: [{ name, kind, stepCount, steps: [{ nodeId, stepNumber }] }] }` |
| GET | `/api/health` | — | `{ score: number, breakdown: { deadCode: n, coupling: n, modularity: n, confidence: n, coverage: n } }` |

### 11.4 Files

| Method | Path | Request | Response |
|--------|------|---------|----------|
| GET | `/api/tree` | — | `{ tree: FolderNode[] }` (nested structure) |
| GET | `/api/file` | `?path=src/foo.py` | `{ path, content, language }` |

### 11.5 Query

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/api/cypher` | `{ query: string }` | `{ columns: string[], rows: any[][], rowCount: number, durationMs: number }` |

### 11.6 Diff

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/api/diff` | `{ base: string, compare: string }` | `{ added: node[], removed: node[], modified: node[], addedEdges: edge[], removedEdges: edge[] }` |

### 11.7 Live Events

| Method | Path | Response |
|--------|------|----------|
| SSE | `/api/events` | Stream of `{ type: "reindex_start" | "reindex_complete" | "file_changed", data: {...} }` |

### 11.8 Actions

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/api/reindex` | — | `{ status: "started" }` |

### 11.9 Implementation Notes

- All routes delegate to existing `StorageBackend` protocol methods — no new Cypher queries where an existing method suffices
- `/api/graph` → `storage.load_graph()` + serialize
- `/api/impact/{id}` → `storage.traverse_with_depth()`
- `/api/search` → `hybrid_search()` from `axon.core.search.hybrid`
- `/api/dead-code` → query `WHERE n.is_dead = true`
- `/api/coupling` → query `WHERE r.rel_type = 'coupled_with'`
- `/api/health` → computed on-the-fly from dead count, coupling stats, modularity, confidence avg
- CORS: restricted to `localhost` origins only
- Read-only enforcement: Cypher endpoint rejects write operations (same blocklist as CLI)

### 11.10 Build & Bundling

- Frontend built with `vite build` → output to `src/axon/web/frontend/dist/`
- `dist/` included in Python package via `pyproject.toml` package-data
- `axon ui` mounts `dist/` as FastAPI static files
- **Dev mode**: `axon ui --dev` proxies to Vite dev server (port 5173) for HMR

---

## 12. Live Reload

When `axon ui --watch` is used, file changes trigger automatic graph updates.

### 12.1 Server Side

- File watcher (existing `watchfiles`-based `watch_repo()`) detects changes
- On change: runs incremental reindex via `reindex_files()`
- Pushes SSE event to `/api/events`:
  ```json
  {
    "type": "reindex_complete",
    "data": {
      "added": ["function:src/new.py:new_func"],
      "removed": ["function:src/old.py:old_func"],
      "modified": ["function:src/changed.py:updated_func"]
    }
  }
  ```

### 12.2 Frontend Side

- `EventSource` connection to `/api/events`
- On `reindex_complete`:
  1. Fetch updated graph data (`GET /api/graph`)
  2. Diff against current Graphology instance
  3. Apply change animations (section 5.3.10)
  4. Update Graphology graph
  5. Run short ForceAtlas2 settling pass (~5s)
  6. Flash status bar indicator: "Updated — 3 changes"

---

## 13. Implementation Phases

Suggested build order, from foundation to polish.

### Phase 1 — API Server Foundation
- FastAPI app factory (`web/app.py`)
- Core routes: `/api/graph`, `/api/node/:id`, `/api/search`, `/api/overview`
- `axon ui` CLI command (new subcommand in `cli/main.py`)
- Static file serving for the frontend bundle
- **Milestone**: `axon ui` starts server, `/api/graph` returns real data

### Phase 2 — Frontend Shell + Graph Canvas
- Vite + React + TypeScript + Tailwind + shadcn/ui scaffold
- Header bar, status bar, three-panel layout with `Resizable`
- Sigma.js + Graphology initialization from `/api/graph`
- ForceAtlas2 layout with progress indicator
- Basic node rendering (color by type, size by degree)
- Zoom/pan, fit-to-screen button
- **Milestone**: Graph renders and is navigable

### Phase 3 — Explorer Interactions
- Left sidebar: File Explorer tab (tree from `/api/tree`)
- Left sidebar: Filters tab (node/edge type toggles, depth control)
- Node click → select, highlight neighbors, dim others
- Right panel: Context tab (callers, callees, type refs from `/api/node/:id`)
- Right panel: Code tab (file content from `/api/file` with Shiki)
- Command palette (shadcn `Command`, search via `/api/search`)
- **Milestone**: Full explore → select → inspect workflow works

### Phase 4 — Impact & Flow Visualization
- API route: `/api/impact/:id`
- Right panel: Impact tab with depth-grouped list
- Animated blast radius ripple on graph
- API route: `/api/processes`
- Left sidebar: Communities tab
- Right panel: Processes tab with flow list
- Animated flow trace (particle along edges)
- Community convex hulls on graph
- **Milestone**: Impact analysis and flow tracing work end-to-end

### Phase 5 — Analysis Dashboard
- API routes: `/api/health`, `/api/dead-code`, `/api/coupling`, `/api/communities`
- Analysis view layout with dashboard cards
- Code Health Score (composite + breakdown)
- Dead Code Report table
- Coupling Heatmap (canvas-based matrix)
- Inheritance tree view
- Dead Code sidebar tab
- **Milestone**: Full analysis dashboard functional

### Phase 6 — Cypher Console
- API route: `/api/cypher`
- Cypher view layout (editor + results + graph preview)
- Multi-line editor with basic syntax highlighting
- Preset queries dropdown
- Results table (sortable, paginated)
- Query history (localStorage)
- Graph preview highlighting matching nodes
- **Milestone**: Cypher queries execute and visualize

### Phase 7 — Branch Diff
- API route: `/api/diff`
- Branch diff input in Analysis dashboard
- Mini Sigma.js instance with color-coded merged graph
- Show all / changes only toggle
- "Open in Explorer" with diff overlay
- **Milestone**: Branch comparison shows structural changes visually

### Phase 8 — Live Reload
- SSE endpoint: `/api/events`
- `--watch` flag on `axon ui`
- EventSource connection in frontend
- Change detection + diff animations (green/red/amber pulses)
- ForceAtlas2 settling pass after changes
- Status bar update indicator
- **Milestone**: File edits in IDE update graph in real-time

### Phase 9 — Polish & Keyboard
- Full keyboard shortcut system
- Minimap implementation
- Layout mode switching (Force/Tree/Radial)
- Command mode (`>` prefix in palette)
- Draggable panel resizing
- Error states and loading skeletons
- Empty states for all panels
- Performance optimization (large graph handling)
- **Milestone**: Production-grade UX, keyboard-navigable

### Phase 10 — Packaging & Distribution
- Build pipeline: `vite build` → `dist/` → included in Python wheel
- Dev mode proxy (`axon ui --dev`)
- pyproject.toml updates for package-data
- Integration tests (API + frontend E2E)
- Documentation for `axon ui` command
- **Milestone**: `pip install axoniq` includes working web UI

---

## Appendix A: Key Differentiators vs GitNexus

| Feature | GitNexus | Axon Web UI |
|---------|----------|-------------|
| Aesthetic | Sleek void/cyan | Terminal green, data-dense, monospace |
| Analysis dashboard | None | Health score, coupling heatmap, inheritance trees |
| Coupling visualization | None | Interactive heatmap matrix |
| Branch diff | None | Color-coded merged graph |
| Impact visualization | Simple list | Animated depth-colored ripple |
| Flow visualization | Static Mermaid diagrams | Animated particle trace on graph |
| Search | Basic search bar | Command palette with commands |
| Community display | Node coloring only | Convex hull regions with labels |
| AI chat | Built-in (6 LLM providers) | None (deferred to MCP) |
| Runtime | All-browser WASM | Local Python server + static SPA |
| Component library | Custom | shadcn/ui (composable primitives) |
| Dead code | None | Sidebar tab + dashboard report |
| Graph minimap | None | Corner minimap with viewport |

## Appendix B: Node Color Reference

| Node Type | Color Token | Hex | Usage |
|-----------|-------------|-----|-------|
| Function | `--node-function` | `#39d353` | Graph nodes, badges, type filters |
| Class | `--node-class` | `#58a6ff` | Graph nodes, badges, type filters |
| Method | `--node-method` | `#a371f7` | Graph nodes, badges, type filters |
| Interface | `--node-interface` | `#3fb8af` | Graph nodes, badges, type filters |
| TypeAlias | `--node-typealias` | `#56d4dd` | Graph nodes, badges, type filters |
| Enum | `--node-enum` | `#f0883e` | Graph nodes, badges, type filters |
| File | `--node-file` | `#6b7d8e` | Graph nodes (when visible) |
| Folder | `--node-folder` | `#4d5969` | Graph nodes (when visible) |

## Appendix C: Edge Style Reference

| Edge Type | Line Style | Color | Default Opacity |
|-----------|-----------|-------|-----------------|
| CALLS | Solid | `--text-dimmed` | `confidence * 0.6` |
| IMPORTS | Dashed | `--text-dimmed` | 0.3 |
| EXTENDS | Solid + arrow | `--purple` | 0.5 |
| IMPLEMENTS | Dashed + arrow | `--purple` | 0.4 |
| USES_TYPE | Dotted | `--cyan` | 0.3 |
| COUPLED_WITH | Thick solid | `--warning` | `strength * 0.8` |
| MEMBER_OF | Hidden by default | `--purple` | 0.2 (when visible) |
| STEP_IN_PROCESS | Hidden by default | `--cyan` | 0.2 (when visible) |
