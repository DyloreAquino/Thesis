# Thesis Layout Guide

This document is the concrete reference for editing the station layouts in
`godot/thesis-godot`. It explains how entries, exits, obstacles, queues, and
switches are structured and wired, and gives repeatable recipes for creating or
modifying layouts.

The generated topology snapshot at the end is derived from the current
`.tscn` files. Treat it as a snapshot, not as a live source of truth. If you
change a layout, re-verify the affected section before editing further.

Snapshot date: 2026-11-24.

---

## 1. Canonical layouts

| Layout | File | Meaning | Canonical use |
|---|---|---|---|
| O1T1E1 | `res://Tests/O1T1E1.tscn` | Base station layout, all entries/exits | Best default base for a new layout |
| O1T1E2 | `res://Tests/O1T1E2.tscn` | Base layout with E2 entry/exit removal | Entry-removal variant |
| O1T1E3 | `res://Tests/O1T1E3.tscn` | Base layout with E3 entry/exit removal | Exit-removal variant |
| O1T2E1 | `res://Tests/O1T2E1.tscn` | Alternating gates and stricter routing separation | Turnstile-orientation / routing variant |
| O1T2E2 | `res://Tests/O1T2E2.tscn` | Alternating gates with E2 entry/exit removal | Combined turnstile / entry-removal variant |
| O1T2E3 | `res://Tests/O1T2E3.tscn` | Alternating gates with E3 entry/exit removal | Combined turnstile / exit-removal variant |
| O1T3E1 | `res://Tests/O1T3E1.tscn` | Grouped entry/exit gates on left and right sides | Grouped-turnstile variant |
| O1T3E2 | `res://Tests/O1T3E2.tscn` | Grouped gates with E2 entry/exit removal | Combined grouped-turnstile / entry-removal variant |
| O1T3E3 | `res://Tests/O1T3E3.tscn` | Grouped gates with E3 entry/exit removal | Combined grouped-turnstile / exit-removal variant |
| O2T1E1 | `res://Tests/O2T1E1.tscn` | Repositioned food stands | Obstacle-position variant |
| O2T1E2 | `res://Tests/O2T1E2.tscn` | Repositioned food stands with E2 entry/exit removal | Combined obstacle / entry-removal variant |
| O2T1E3 | `res://Tests/O2T1E3.tscn` | Repositioned food stands with E3 entry/exit removal | Combined obstacle / exit-removal variant |
| O2T2E1 | `res://Tests/O2T2E1.tscn` | Repositioned food stands + alternating gates | Combined obstacle / turnstile variant |
| O2T2E2 | `res://Tests/O2T2E2.tscn` | Repositioned food stands + alternating gates with E2 entry/exit removal | Combined obstacle / turnstile / entry-removal variant |
| O2T2E3 | `res://Tests/O2T2E3.tscn` | Repositioned food stands + alternating gates with E3 entry/exit removal | Combined obstacle / turnstile / exit-removal variant |
| O2T3E1 | `res://Tests/O2T3E1.tscn` | Repositioned food stands + grouped gates | Combined obstacle / turnstile variant |
| O2T3E2 | `res://Tests/O2T3E2.tscn` | Repositioned food stands + grouped gates with E2 entry/exit removal | Combined obstacle / grouped-turnstile / entry-removal variant |
| O2T3E3 | `res://Tests/O2T3E3.tscn` | Repositioned food stands + grouped gates with E3 entry/exit removal | Combined obstacle / grouped-turnstile / exit-removal variant |

Legacy or experimental scenes such as `main_layout_new.tscn`, `test_main.tscn`,
`test_two.tscn`, and `test_layout_1.tscn` are **not** canonical layout bases.
Do not copy from them unless intentionally reviving an old experiment.

The startup scene is `res://layout_selector.tscn`. It presents buttons for the
eighteen canonical layouts and uses `layout_selector.gd` to switch scenes.

---

## 2. Runtime flow

1. The layout selector loads one of the canonical layouts.
2. Each layout contains a `SimClient`, `GeometryExporter`, `AgentManager`,
   `ParametersManager`, and `StatisticsManager`.
3. `SimClient` connects to the Python simulation server at
   `ws://127.0.0.1:8765`.
4. The Python server must be running from `sim_server` before simulation.
5. The user presses **Fix Geometry** to send the current scene geometry to the
   server.
6. The server validates the geometry and routing graph.
7. The user presses **Start Simulation**.
8. Agents are simulated by JuPedSim and rendered in Godot.
9. The **Back to Layout Selector** button stops the simulation and returns to
   the selector.

Important scripts:

| Script | Role |
|---|---|
| `geometry_exporter.gd` | Collects scene geometry and sends it to the server |
| `sim_client.gd` | WebSocket client and simulation state machine |
| `agent_manager.gd` | Spawns, updates, and despawns rendered agents |
| `parameters_manager.gd` | Sends agent count and entry-rate changes |
| `statistics_manager.gd` | Receives statistics for the density chart |
| `journey_entry.gd` | Marks an entry polygon and its starting switch |
| `journey_queue.gd` | Marks a queue path and its downstream targets |
| `journey_switch.gd` | Marks a waypoint and its outgoing targets |
| `layout_selector.gd` | Startup layout chooser |
| `Tests/camera_2d.gd` | Pan/zoom camera |
| `Tests/canvas_layer.gd` | Shows the UI layer |

---

## 3. Scene anatomy

Every canonical layout uses the same top-level node structure:

```text
<LayoutRoot> (Node2D)
├── Camera2D
├── SimClient
├── GeometryExporter
├── AgentManager
├── ParametersManager
├── StatisticsManager
├── WalkableArea (Polygon2D)
├── EntryPoints (Node2D)
│   ├── EntryPoint (Polygon2D + journey_entry.gd)
│   ├── EntryPoint2
│   └── ...
├── ExitPoints (Node2D)
│   ├── ExitPoint (Polygon2D)
│   └── ...
├── Obstacles (Node2D)
│   ├── Obstacle (Polygon2D)
│   └── ...
├── QueueLines (Node2D)
│   ├── QueueLine (Line2D + journey_queue.gd)
│   └── ...
├── JourneySwitches (Node2D)
│   ├── JourneySwitch1 (Marker2D + journey_switch.gd)
│   └── ...
└── CanvasLayer
    └── UI
        ├── DensityChart
        ├── TopRight
        └── BottomRight
```

### Required parent names

`GeometryExporter` looks up these exact child groups:

```gdscript
$"../WalkableArea"
$"../EntryPoints"
$"../ExitPoints"
$"../Obstacles"
$"../QueueLines"
$"../JourneySwitches"
```

Do not rename these groups unless you also update `geometry_exporter.gd`.

### Node roles

| Node | Script | Meaning |
|---|---|---|
| `WalkableArea` | none | Base walkable polygon |
| `EntryPoints/*` | `journey_entry.gd` | Agent spawn polygon |
| `ExitPoints/*` | none | Exit polygon |
| `Obstacles/*` | none | Obstacle polygon subtracted from walkable space |
| `QueueLines/*` | `journey_queue.gd` | Queue waiting path |
| `JourneySwitches/*` | `journey_switch.gd` | Waypoint/routing node |

### Naming conventions

Current maximum names:

| Type | Current naming | Current max |
|---|---|---|
| Entry | `EntryPoint`, `EntryPoint2..7` | `EntryPoint7` |
| Exit | `ExitPoint`, `ExitPoint2..8` | `ExitPoint8` |
| Obstacle | `Obstacle`, `Obstacle2..75` | `Obstacle75` |
| Queue | `QueueLine`, `QueueLine2..35` | `QueueLine35` |
| Switch | `JourneySwitch1..64`; `30..64` are queue approach switches | `JourneySwitch64` |

Notes:

- `QueueLine` is treated as the first queue, `QueueLine2` as the second, etc.
- `JourneySwitch30..64` correspond one-to-one with `QueueLine`..`QueueLine35`.
- Queue approach switches all use `radius_m = 1.0`.
- Switch numbering has gaps below `30` because old experimental switches were removed.
- When adding a new node, use the next free number to avoid confusing future
  agents.
- Do not reuse a removed node number unless you are intentionally replacing
  that node.
- If you remove a node, remove every `NodePath` that referenced it.
- If you add a node with a number higher than the current maximum, update this
  table.
- `unique_id` values must remain unique within a scene.
- When duplicating a node inside the same scene, give the copy a new
  `unique_id`.

---

## 4. Geometry conventions

### Coordinate conversion

`GeometryExporter.world_scale` is:

```gdscript
0.031
```

So:

```text
1 metre is about 32.3 Godot pixels
```

World geometry is calculated as:

```text
world_point = node.to_global(local_point)
meters      = world_point * 0.031
```

### Obstacles

Obstacles are `Polygon2D` nodes under `Obstacles`. The server subtracts every
obstacle from `WalkableArea`:

```python
walkable_area = walkable_area.difference(obstacle)
```

This means obstacles can carve corridors, walls, and turnstile gaps.

Important obstacle patterns:

| Obstacle(s) | Role |
|---|---|
| `Obstacle` | Large station block |
| `Obstacle14`, `Obstacle25`, `Obstacle30`, `Obstacle45`, `Obstacle61` | Large walls/blocks |
| `Obstacle40` | Central rectangular island |
| Most remaining numbered obstacles | Smaller walls, partitions, and platform furniture |
| `Obstacle64..69`, `Obstacle62..63` | Outer wall segments |
| `Obstacle70..74` | Top-left turnstile barriers |
| `Obstacle75` | Left-side station block added in the current base layout |

### Central food-stand block

`Obstacle40` is the central food-stand block.

- `O1` uses the normal placement.
- `O2` uses the repositioned placement implemented in `O2T1E1`.

When copying a layout, preserve this difference intentionally.

### Turnstile barriers

The top-left exit bank uses five obstacle pieces:

```text
Obstacle70, Obstacle71, Obstacle72, Obstacle73, Obstacle74
```

These form turnstile-like barriers with gaps. `QueueLine32..35` pass through
those gaps toward `ExitPoint8`.

Queue lines should not intersect obstacles. If they do, agents may route badly
or get stuck visually.

---

## 5. Queue conventions

### Queue geometry

A `JourneyQueue` is a `Line2D`.

```text
points[0]  = queue head / release side / destination side
points[-1] = queue tail / waiting side
```

So a horizontal queue like this:

```gdscript
points = PackedVector2Array(0, 0, 176, 0)
```

has its head at the node position and its tail extending to the right.

Every queue also has exactly one queue approach switch under `JourneySwitches`.
That switch sits just past `points[-1]` on the entry side, targets only that
queue, and uses `radius_m = 1.0`. Feeder switches target approach switches,
never queues directly.

When reversing a queue direction, reverse the point order. Do not change only
the node position.

### Elongation

To elongate a queue:

1. Keep the head point unchanged.
2. Extend the tail point along the existing tail direction.
3. Keep the queue inside walkable geometry and clear of obstacles.

All queues are capped at **160 px** (~5 m) so agents do not walk backward along
long queues before reaching a turnstile. T3 keeps one length per gate group,
limited either by that cap or by obstacle clearance: right exit `160 px`, right
entry `112 px`, left exit `160 px`, left entry `160 px`.

### Release intervals

Current rule:

| Queue | Release interval |
|---|---|
| `QueueLine9` | `1.1` seconds |
| `QueueLine10` | `1.1` seconds |
| Every other queue | `3.8` seconds |

`release_interval_seconds` is exported by `journey_queue.gd`.

### Transition types

Queues and switches support the same transition types:

```gdscript
"fixed"
"least_targeted"
"round_robin"
```

Rules:

| Transition | Meaning | Constraint |
|---|---|---|
| `fixed` | Always goes to the single target | Must have exactly one target |
| `least_targeted` | Chooses the least-used target | Works with one or more targets |
| `round_robin` | Cycles through targets in order | Works with one or more targets |

Most queues use `least_targeted`. The bottom vertical pair uses `round_robin`.

### Queue banks

The station is organized into queue banks.

#### Right-upper bank

- `QueueLine..QueueLine8`
- Feeder switches: `S2`; in `T3`, `S17` routes onward to `S18` instead of this
  bank.
- Downstream destinations:
  - `S20` → station exits 6/7
  - `S25` → right-side platform exits
- `O1T2E1` alternates head directions within the bank.

#### Right-lower bank

- `QueueLine11..QueueLine17`
- Feeder switches: `S9`, `S18`, depending on layout; in `T3`, `S17` also reaches
  this bank through `S18`.
- Downstream destinations:
  - `S19` → `ExitPoint2`
  - `S20` → station exits 6/7
  - `S26` → station exits 6/7, only in `O1T2E1`
- `O1T2E1` alternates head directions within the bank.

#### Left bank

- `QueueLine18..QueueLine31`
- Feeder switches: `S5`, `S22`, `S6`, `S13`, depending on layout; `S12` is
  used only in `T1`, `T3`, and `O1T1E1`. In `T3`, `S13` is inert and `S12`
  feeds the `S49`/`S51..S60` approach switches directly.
- Downstream destinations:
  - `S14`, `S16` → left-side platform exits
  - `S7`, `S10` → station exits 6/7
- `O1T2E1` alternates head directions by spatial position, not simply by numeric
  order.

#### Bottom vertical pair

- `QueueLine9`, `QueueLine10`
- Both heads face into the station.
- Feeder: `S1`.
- Destination: `S2`.
- Special release interval: `1.1`.

#### Top-left turnstile bank

- `QueueLine32..QueueLine35`
- Vertical queues with heads pointing up toward `ExitPoint8`.
- Feeder: `JourneySwitch28`.
- Exit-side waypoint: `JourneySwitch29`.
- Release interval: `3.8`.
- Present identically in all current layouts.

---

## 6. Switch conventions

A `JourneySwitch` is a `Marker2D` with:

```gdscript
radius_m
target_switches
target_queues
target_exits
transition_type
```

`radius_m` is how close an agent must get for JuPedSim to consider the waypoint
reached.

### Graph rules

1. Every switch must target at least one switch, queue, or exit.
2. Every queue must target at least one switch or exit.
3. Every queue has exactly one queue approach switch.
4. Only queue approach switches target queues; feeders target approach switches.
5. A `fixed` transition must have exactly one target.
6. The routing graph must be acyclic.
7. Every routing path must eventually reach an exit.
8. Switch positions must remain inside the walkable area.
9. Queue points should remain inside the walkable area.
10. Rewired switches must not be left orphaned; remove them or give them a
   deliberate inbound edge.

The Python server performs these checks when geometry is sent. If validation
fails, Godot receives a simulation error state.

### Feeder/destination pattern

Most queue banks use a flanking pattern:

```text
entry-side switch
    
feeder switch
    
queue approach switches
    
queues
    
destination switch
    
exit
```

Example:

```text
S24  S28  S61/S62/S63/S64  Q32/Q33/Q34/Q35  S29  ExitPoint8
```

`S28` is the feeder. `S61`..`S64` are the one-per-queue approach switches.
Each approach switch has a `fixed` transition into exactly one queue.
`S29` is the destination-side waypoint. It sends released agents to the exit.

An entry-side switch may target approach switches directly when an extra feeder
would make agents detour backward. In T2, `S23` feeds `S49/S51/S53/S55/S57/S58/S60`
directly; do not reintroduce `S12` as an intermediate hop.

When adding a bank, use this pattern unless there is a deliberate reason not to.

---

## 7. Entry and exit classification

### Entries

| Entry | Starting switch | Classification |
|---|---|---|
| `EntryPoint` | `JourneySwitch1` | Station-side |
| `EntryPoint2` | `JourneySwitch17` | Train-side |
| `EntryPoint3` | `JourneySwitch18` | Train-side |
| `EntryPoint4` | `JourneySwitch23` | Train-side |
| `EntryPoint5` | `JourneySwitch23` | Train-side |
| `EntryPoint6` | `JourneySwitch24` | Train-side |
| `EntryPoint7` | `JourneySwitch8` | Station-side |

### Exits

| Exit | Classification |
|---|---|
| `ExitPoint` | Platform |
| `ExitPoint2` | Platform |
| `ExitPoint3` | Platform |
| `ExitPoint4` | Platform |
| `ExitPoint5` | Platform |
| `ExitPoint6` | Station exit |
| `ExitPoint7` | Station exit |
| `ExitPoint8` | Station exit |

### Routing separation

`O1T2E1` is intentionally stricter:

- Train-side entries should reach only station exits.
- Station-side entries should reach only platform exits.

`O1T1E1` and `O2T1E1` are currently more permissive, but future edits should
avoid accidentally mixing flows unless that is the intended variant.

---

## 8. Layout-specific differences

### Obstacle variants

| Feature | `O1` | `O2` |
|---|---|---|
| Food-stand block | Normal placement | Repositioned |

The old `O3` and `O4` obstacle codes are retired. Their blocked entry/exit role
is now handled by the `E` dimension.

### Entry/exit variants

| Feature | `E1` | `E2` | `E3` |
|---|---|---|---|
| `EntryPoint` | Present | Removed | Present |
| `EntryPoint2`..`EntryPoint6` | Present | Present | Removed |
| `EntryPoint7` | Present | Removed | Present |
| `ExitPoint`, `ExitPoint2`..`ExitPoint5` | Present | Removed | Present |
| `ExitPoint6`..`ExitPoint8` | Present | Present | Removed |

`E2` keeps the platform-to-station exit side while removing the north/south
entry side. `E3` does the opposite: it keeps the station-to-platform entry side
and removes exits `6`, `7`, and `8`.

Both `E2` and `E3` also omit queue lines and journey switches that no longer
have any path to a remaining exit. Surviving routes are otherwise unchanged.

### Default entry rate

The scene default for `EntryRateInput` is `1.5 × N`, where `N` is the number of
retained entry points:

| E variant | Entry points | Default entry rate |
|---|---:|---:|
| `E1` | 7 | 10.5 agents/s |
| `E2` | 5 | 7.5 agents/s |
| `E3` | 2 | 3.0 agents/s |

The UI can still override this value before starting a simulation.

### Default agent count

The scene default for `AgentCountInput` is `20 × N`, where `N` is the number of
retained entry points:

| E variant | Entry points | Default agent count |
|---|---:|---:|
| `E1` | 7 | 140 agents |
| `E2` | 5 | 100 agents |
| `E3` | 2 | 40 agents |

The UI can still override this value before starting a simulation.

### Turnstile variants

| Feature | `T1` | `T2` | `T3` |
|---|---|---|---|
| Gate pattern | Normal | Alternating entry/exit | Grouped half entry / half exit |
| Queue direction | Mixed | Alternating | Upper half in, lower half out per side section |
| Routing strictness | Permissive | Train/station separation | Preserves valid routing without alternating order |
| Extra routing switches | None | `S25`, `S26` | Reuses `T2` destination switches |
| Top-left bank | Present | Present | Present |
| Bottom pair | Present | Present | Present |

In T3, upper/lower is evaluated **within each side section**, not across the
whole map:

- Right section: `Q11..Q17` are entry queues; `Q`..`Q8` are exit queues.
- Left section: `Q22..Q28` are entry queues; `Q18..Q21` and `Q29..Q31` are exit
  queues.
- `Q5..Q8` and `Q11..Q14` are reversed from the T2 alternating pattern to match
  this grouped flow.
- `S17` targets `S18`; `S18` targets `S40..S46`, which feed `Q11..Q17`.
- `S23` targets `S12`; `S12` targets `S49`, `S51..S60`; `S24` targets `S12` and
  `S28`. `S13` is inert in `T3`.
- `S22` targets `S50`, `S49`, `S48`, `S58`, `S59`, `S60`, `S47`, in that order.
- `Q22..Q28` target `S10`; `Q18..Q21` and `Q29..Q31` target `S16`.
- `Q9/Q10` and `Q32..Q35` keep their existing direction.
- Queue heads must line up with the turnstile obstacle end: right exit heads at
  `x=640`, right entry heads at `x=576`, left entry heads at `x=-640`, left exit
  heads at `x=-704`. Move only `points[0]`; translating the whole queue can push
  the tail into an obstacle.
- Queues in the same gate group share one length: right exit `160 px`, right
  entry `112 px`, left exit `160 px`, left entry `160 px`. Do not keep the old
  alternating tail positions.

---

## 9. Editing recipes

### 9.1 Create a new layout

1. Copy the closest canonical `E1` scene:
   - Use `O1T1E1.tscn` for a general layout.
   - Use `O2T1E1.tscn` for repositioned food stands.
   - Use `O1T2E1.tscn` for alternating entry/exit gates.
   - Use `O1T3E1.tscn` for grouped entry/exit gates.
2. Save as `res://Tests/O<obstacle>T<turnstile>E<entry-exit>.tscn`.
3. Change the scene header UID so it does not collide with the source scene:

```text
[gd_scene format=3 uid="uid://<unique-id>"]
```

4. Optionally rename the root node, but keep the required runtime child node
   names intact.
5. For `E2` and `E3`, remove only the entry/exit nodes listed in the
   entry/exit variant table. Keep all other queue lines and switches unchanged
   at this step.
6. Remove `NodePath` entries pointing to deleted exit nodes from `target_exits`.
   If a node has no remaining exits, remove the `target_exits` property and
   remove `"target_exits"` from its `node_paths` list. Never leave `[null]`.
7. Delete any `JourneySwitch` or `QueueLine` that has no path to a remaining
   exit, then remove incoming `NodePath` references to those deleted nodes.
   The server rejects inert routes as cycles or dead ends.
8. Add the new scene to `layout_selector.gd`.
9. Add a matching button to `layout_selector.tscn`.
10. Add the new layout to the canonical layout table and generated appendices.
11. Preserve the `BackToLayoutSelectorButton` and its `SimClient` connection.
12. Run the layout in Godot and press **Fix Geometry** before simulating.

### 9.2 Add a queue

1. Choose the next free queue name, currently `QueueLine36`.
2. Add a `Line2D` under `QueueLines`.
3. Attach `journey_queue.gd`.
4. Set `points` so `points[0]` is the head/destination side.
5. Extend the tail away from the destination.
6. Set `target_switches` or `target_exits`.
7. Set `transition_type`.
8. Set `release_interval_seconds`:
   - `3.8` normally,
   - `1.1` only for the bottom pair.
9. If using `target_switches`, make sure the switch exists and can reach an exit.
10. If adding `node_paths`, include only the properties actually used.
11. Make sure the new queue does not intersect existing queues or obstacles.
12. Add its queue approach switch and rewire every incoming feeder to that
    switch instead of the queue.

Example skeleton:

```text
[node name="QueueLine36" type="Line2D" parent="QueueLines" unique_id=<unique> node_paths=PackedStringArray("target_switches")]
position = Vector2(x, y)
points = PackedVector2Array(0, 0, dx, dy)
width = 4.0
default_color = Color(1, 1, 0.36078432, 1)
script = ExtResource("8_gnm01")
target_switches = [NodePath("../../JourneySwitches/JourneySwitch<id>")]
transition_type = "least_targeted"
release_interval_seconds = 3.8
```

### 9.3 Add a switch

1. Choose the next free switch name, currently `JourneySwitch65`.
2. Add a `Marker2D` under `JourneySwitches`.
3. Attach `journey_switch.gd`.
4. Place it inside walkable geometry.
5. Set `radius_m`.
6. Set one or more of:
   - `target_switches`
   - `target_queues`
   - `target_exits`
7. Set `transition_type`.
8. Update `node_paths` to include every exported target array actually used.
9. Make sure the switch does not overlap an obstacle or existing waypoint.

Example skeleton:

```text
[node name="JourneySwitch65" type="Marker2D" parent="JourneySwitches" unique_id=<unique> node_paths=PackedStringArray("target_queues")]
position = Vector2(x, y)
script = ExtResource("9_on656")
radius_m = 1.0
target_queues = [NodePath("../../QueueLines/QueueLine<id>")]
transition_type = "fixed"
```

For a queue approach switch, use `radius_m = 1.0`, `transition_type = "fixed"`,
one `target_queues` entry, and place it just past the queue tail:

```text
[node name="JourneySwitch<id>" type="Marker2D" parent="JourneySwitches" unique_id=<unique> node_paths=PackedStringArray("target_queues")]
position = Vector2(x, y)
script = ExtResource("9_on656")
radius_m = 1.0
target_queues = [NodePath("../../QueueLines/QueueLine<id>")]
transition_type = "fixed"
```

### 9.4 Add an exit

1. Add a `Polygon2D` under `ExitPoints`.
2. Name it `ExitPoint9` or the next free exit name.
3. Draw the polygon in world-local coordinates.
4. Wire a switch or queue to it.

No script is needed on an exit polygon.

### 9.5 Add an obstacle

1. Add a `Polygon2D` under `Obstacles`.
2. Name it `Obstacle76` or the next free obstacle name.
3. Draw the polygon.
4. Make sure it does not overlap a queue line or switch waypoint.
5. Remember that the server subtracts it from the walkable area.
6. Verify that the walkable area still connects the regions that need to route
   to each other.

### 9.6 Elongate a queue

For a two-point queue:

1. Keep `points[0]` unchanged.
2. Move `points[-1]` farther along the current tail direction.
3. Do not cross walls or other queue lines.

For a multi-point queue, extend the final segment only.

### 9.7 Wire a new bank

Use the flanking pattern:

```text
upstream switch
    
feeder switch
    
queue approach switches
    
queues
    
destination switch
    
exit
```

Checklist:

- The feeder switch targets one approach switch per queue.
- Each approach switch targets exactly one queue.
- Each queue targets the destination switch or an exit.
- The destination switch targets the exit or another legal downstream node.
- The upstream switch is reachable from an entry.
- No path returns to an earlier switch.
- All switch and queue positions are inside walkable geometry.

### 9.8 Preserve `O1T2E1` routing separation

When editing `O1T2E1`, keep the flow classes separated:

```text
train-side entries → station exits
station-side entries → platform exits
```

Do not let a train-side switch target a platform-bound queue unless the change
is intentional.

### 9.9 Add a layout to the selector

In `layout_selector.gd`, append:

```gdscript
{
    "button_path": "ScrollContainer/GridContainer/<ButtonName>",
    "scene_path": "res://Tests/<NewLayout>.tscn",
},
```

Then add the matching `Button` node in `layout_selector.tscn`.

Current selector entries:

| Button | Scene |
|---|---|
| `O1T1E1Button` | `res://Tests/O1T1E1.tscn` |
| `O1T1E2Button` | `res://Tests/O1T1E2.tscn` |
| `O1T1E3Button` | `res://Tests/O1T1E3.tscn` |
| `O1T2E1Button` | `res://Tests/O1T2E1.tscn` |
| `O1T2E2Button` | `res://Tests/O1T2E2.tscn` |
| `O1T2E3Button` | `res://Tests/O1T2E3.tscn` |
| `O1T3E1Button` | `res://Tests/O1T3E1.tscn` |
| `O1T3E2Button` | `res://Tests/O1T3E2.tscn` |
| `O1T3E3Button` | `res://Tests/O1T3E3.tscn` |
| `O2T1E1Button` | `res://Tests/O2T1E1.tscn` |
| `O2T1E2Button` | `res://Tests/O2T1E2.tscn` |
| `O2T1E3Button` | `res://Tests/O2T1E3.tscn` |
| `O2T2E1Button` | `res://Tests/O2T2E1.tscn` |
| `O2T2E2Button` | `res://Tests/O2T2E2.tscn` |
| `O2T2E3Button` | `res://Tests/O2T2E3.tscn` |
| `O2T3E1Button` | `res://Tests/O2T3E1.tscn` |
| `O2T3E2Button` | `res://Tests/O2T3E2.tscn` |
| `O2T3E3Button` | `res://Tests/O2T3E3.tscn` |

### 9.10 Add an entry

1. Add a `Polygon2D` under `EntryPoints`.
2. Name it `EntryPoint8` or the next free entry name.
3. Attach `journey_entry.gd`.
4. Set `starting_switch` to an existing switch.
5. Update `node_paths` to include `starting_switch`.
6. Make sure the starting switch can reach an exit.
7. Keep the spawn polygon inside walkable geometry and clear of obstacles.

---

## 10. Manual validation checklist

Before considering a layout finished:

1. **Parent groups exist**
   - `WalkableArea`
   - `EntryPoints`
   - `ExitPoints`
   - `Obstacles`
   - `QueueLines`
   - `JourneySwitches`

2. **Every entry has a valid starting switch**

3. **Every queue has a destination**
   - switch or exit
   - no empty target

4. **Every switch has a destination**
   - switch, queue, or exit
   - no empty target

5. **No `NodePath("")`**
   - This usually means a removed target is still referenced.

6. **No duplicate switch IDs**
   - `JourneySwitch._enter_tree()` uses the node name as `switch_id`.

7. **No duplicate sibling node names**
   - Especially within `QueueLines`, `JourneySwitches`, and `Obstacles`.

8. **No routing cycles**
   - The server rejects them.

9. **All paths reach exits**
   - The server rejects dead ends.

10. **Fixed transitions have exactly one target**

11. **Release intervals are correct**
    - `3.8` everywhere,
    - `1.1` only on `Q9/Q10`.

12. **Queue heads face their destinations**
    - In T3, heads align with the turnstile obstacle end for their section half.

13. **Queue tails stay inside walkable geometry**

14. **Queue lines do not intersect obstacles**

15. **Switches stay inside walkable geometry**

16. **Exactly one approach switch exists per queue**
    - Each approach switch uses `radius_m = 1.0`.

17. **Feeders target approach switches, not queues**

18. **`O1T2E1` flow classes remain separated**

19. **Back button still works**

20. **Fix Geometry still sends the layout**

21. **Default entry rate matches the `E` variant**
    - `E1` = `10.5`, `E2` = `7.5`, `E3` = `3.0`.

22. **Default agent count matches the `E` variant**
    - `E1` = `140`, `E2` = `100`, `E3` = `40`.

---

## 11. Gotchas

### Do not copy from `main_layout_new.tscn`

It is legacy/experimental. Use one of the canonical layouts.

### Do not mutate canonical layouts for throwaway experiments

Duplicate the scene first, change its UID, and edit the copy. This keeps the
canonical layouts stable for future comparison.

### `CanvasLayer.visible = false` is intentional

The `CanvasLayer` script calls `show()` in `_ready()`, so the UI still appears.

### `node_paths` must match real properties

In `.tscn` files, this metadata tells Godot which exported `NodePath` arrays to
resolve:

```text
node_paths=PackedStringArray("target_switches")
```

If you add `target_queues` but do not add it to `node_paths`, Godot may not
resolve it correctly. Conversely, do not leave `node_paths` entries for
properties that no longer exist.

### Scene UIDs must be unique

When duplicating a scene, change the scene UID. Otherwise Godot may resolve the
wrong scene.

Node `unique_id`s may repeat across different scenes, but they must remain
unique within one scene.

### Switch IDs come from node names

`JourneySwitch._enter_tree()` assigns:

```gdscript
switch_id = self.name
```

Renaming a switch changes its routing ID. Also remember that switch numbering is
not identical across layouts; verify that a switch exists in the layout you are
editing before wiring to it.

### Entry fallback uses the first switch

If an entry polygon has no `starting_switch`, `GeometryExporter` falls back to
the first `JourneySwitch` under `JourneySwitches`. Always set an explicit
starting switch for new entries.

### Obstacles are subtractive

An obstacle does not need to be a visual wall only; it also removes walkable
area. A large obstacle can make a switch or queue invalid if it overlaps them.

### Queue direction is easy to invert accidentally

Remember that the first point is the head. Reversing a queue changes where
agents are released, not just how the line looks.

### The Python server must be running

If the server is not running, geometry cannot be sent and simulation cannot
start.

### `Fix Geometry` must be pressed after layout changes

The Godot scene does not continuously export geometry. Press **Fix Geometry**
after edits or after entering a new layout.

If the server reports a geometry or routing error, fix the scene and press
**Fix Geometry** again.

### Do not remove required runtime nodes

`SimClient`, `GeometryExporter`, `AgentManager`, `ParametersManager`, and
`StatisticsManager` are required for the layout to simulate correctly.

---

## Appendix A. Generated topology snapshot

The following snapshot was generated from the current canonical `E1` `.tscn`
files. It is intended for quick reference when editing routing. `E2` and `E3`
share these routes except for the entry/exit nodes and exit `NodePath`s removed
by their variant rules. Do not hand-edit these tables unless you also re-verify
the live scenes. Queue approach switches `JourneySwitch30..64` are not expanded
here; each targets exactly one queue.

### A.1 O1T1E1.tscn

#### Entry reachability

```text
EntryPoint   -> ExitPoint, ExitPoint2, ExitPoint3, ExitPoint4, ExitPoint5, ExitPoint6
EntryPoint2  -> ExitPoint6, ExitPoint7
EntryPoint3  -> ExitPoint6, ExitPoint7
EntryPoint4  -> ExitPoint3, ExitPoint4, ExitPoint5, ExitPoint6, ExitPoint7
EntryPoint5  -> ExitPoint3, ExitPoint4, ExitPoint5, ExitPoint6, ExitPoint7
EntryPoint6  -> ExitPoint3, ExitPoint4, ExitPoint5, ExitPoint6, ExitPoint7, ExitPoint8
EntryPoint7  -> ExitPoint, ExitPoint2, ExitPoint3, ExitPoint4, ExitPoint5
```

#### Switch targets

```text
JourneySwitch1  -> Q9, Q10
JourneySwitch2  -> Q1, Q2, Q3, Q4
JourneySwitch5  -> S22, Q18
JourneySwitch6  -> S22, Q22, Q23
JourneySwitch7  -> ExitPoint6, ExitPoint7
JourneySwitch8  -> S2, S9, S5, S22, S6
JourneySwitch9  -> Q17
JourneySwitch10 -> Q22, Q23, ExitPoint6, ExitPoint7
JourneySwitch12 -> S13, Q27, Q28, Q29, Q30, Q31
JourneySwitch13 -> Q24, Q25, Q26, Q27, Q28
JourneySwitch14 -> ExitPoint3, ExitPoint4
JourneySwitch15 -> ExitPoint5
JourneySwitch16 -> S14, S15
JourneySwitch17 -> Q5, Q6, Q7, Q8
JourneySwitch18 -> Q11, Q12, Q13, Q14, Q15, Q16
JourneySwitch19 -> ExitPoint2
JourneySwitch20 -> ExitPoint6, ExitPoint7
JourneySwitch22 -> Q19, Q20, Q21
JourneySwitch23 -> S12
JourneySwitch24 -> S13, S28
JourneySwitch28 -> Q32, Q33, Q34, Q35
JourneySwitch29 -> ExitPoint8
```

#### Queue targets

```text
Q1          -> ExitPoint
Q2          -> ExitPoint
Q3          -> ExitPoint
Q4          -> ExitPoint
Q5          -> S20
Q6          -> S25
Q7          -> S20
Q8          -> S25
Q9          -> S2, S5, S6, S9, S22, ExitPoint6
Q10         -> S2, S5, S6, S9, S22, ExitPoint6
Q11         -> ExitPoint6, ExitPoint7
Q12         -> ExitPoint6, ExitPoint7
Q13         -> ExitPoint6, ExitPoint7
Q14         -> ExitPoint6, ExitPoint7
Q15         -> ExitPoint6, ExitPoint7
Q16         -> ExitPoint6, ExitPoint7
Q17         -> S19
Q18         -> S16
Q19         -> S16
Q20         -> S16
Q21         -> S16
Q22         -> S16
Q23         -> S16
Q24         -> S10
Q25         -> S10
Q26         -> S10
Q27         -> S10
Q28         -> S10
Q29         -> S7
Q30         -> S7
Q31         -> S7
Q32         -> S29
Q33         -> S29
Q34         -> S29
Q35         -> S29
```

### A.2 O2T1E1.tscn

`O2T1E1` currently has the same routing topology as `O1T1E1`. The intended
layout difference is the repositioned food-stand block represented by
`Obstacle40`.

Refer to the `O1T1E1.tscn` tables above for its current topology.

### A.3 O1T2E1.tscn

#### Entry reachability

```text
EntryPoint   -> ExitPoint, ExitPoint2
EntryPoint2  -> ExitPoint6, ExitPoint7
EntryPoint3  -> ExitPoint6, ExitPoint7
EntryPoint4  -> ExitPoint6, ExitPoint7
EntryPoint5  -> ExitPoint6, ExitPoint7
EntryPoint6  -> ExitPoint6, ExitPoint7, ExitPoint8
EntryPoint7  -> ExitPoint, ExitPoint2, ExitPoint3, ExitPoint4, ExitPoint5
```

#### Switch targets

```text
JourneySwitch1   -> Q9, Q10
JourneySwitch2   -> Q2, Q4, Q6, Q8
JourneySwitch5   -> Q18, Q30
JourneySwitch6   -> Q23, Q25
JourneySwitch7   -> ExitPoint6, ExitPoint7
JourneySwitch8   -> S2, S9, S5, S22, S6
JourneySwitch9   -> Q11, Q13, Q15, Q17
JourneySwitch10  -> ExitPoint6, ExitPoint7
JourneySwitch13  -> Q22, Q24, Q26, Q28
JourneySwitch14  -> ExitPoint3, ExitPoint4
JourneySwitch15  -> ExitPoint5
JourneySwitch16  -> S15, S14
JourneySwitch17  -> Q, Q3, Q5, Q7
JourneySwitch18  -> Q12, Q14, Q16
JourneySwitch19  -> ExitPoint2
JourneySwitch20  -> ExitPoint6, ExitPoint7
JourneySwitch22  -> Q19, Q21, Q27
JourneySwitch23  -> Q20, Q22, Q24, Q26, Q28, Q29, Q31
JourneySwitch24  -> S13, S28
JourneySwitch25  -> ExitPoint, ExitPoint2
JourneySwitch26  -> ExitPoint6, ExitPoint7
JourneySwitch28  -> Q32, Q33, Q34, Q35
JourneySwitch29  -> ExitPoint8
```

#### Queue targets

```text
Q1          -> S20
Q2          -> S25
Q3          -> S20
Q4          -> S25
Q5          -> S20
Q6          -> S25
Q7          -> S20
Q8          -> S25
Q9          -> S2
Q10         -> S2
Q11         -> S19
Q12         -> S26
Q13         -> S19
Q14         -> S26
Q15         -> S19
Q16         -> S26
Q17         -> S19
Q18         -> S14
Q19         -> S16
Q20         -> S7
Q21         -> S16
Q22         -> S10
Q23         -> S16
Q24         -> S10
Q25         -> S16
Q26         -> S10
Q27         -> S16
Q28         -> S10
Q29         -> S7
Q30         -> S14
Q31         -> S7
Q32         -> S29
Q33         -> S29
Q34         -> S29
Q35         -> S29
```

## Appendix B. Generated queue orientation snapshot

The following tables show the current queue geometry in each canonical layout.
`Head` is `points[0]`; `Tail` is the final point. Orientation describes the
direction from head to tail.

These tables are ordered by queue number, not necessarily by spatial bank
position. In `O1T2E1`, the alternating pattern follows spatial bank order.

### B.1 O1T1E1.tscn

| Queue | Head | Tail | Head to Tail | Length (px) | Interval | Transition |
|---|---:|---:|---|---:|---:|---|
| Q | (640, 512) | (480, 512) | left | 160 | 3.8 | least_targeted |
| Q2 | (640, 464) | (480, 464) | left | 160 | 3.8 | least_targeted |
| Q3 | (640, 416) | (480, 416) | left | 160 | 3.8 | least_targeted |
| Q4 | (640, 368) | (480, 368) | left | 160 | 3.8 | least_targeted |
| Q5 | (576, 320) | (736, 320) | right | 160 | 3.8 | least_targeted |
| Q6 | (576, 272) | (736, 272) | right | 160 | 3.8 | least_targeted |
| Q7 | (576, 224) | (736, 224) | right | 160 | 3.8 | least_targeted |
| Q8 | (576, 176) | (736, 176) | right | 160 | 3.8 | least_targeted |
| Q9 | (352, 660) | (352, 820) | down | 160 | 1.1 | round_robin |
| Q10 | (228, 659) | (228, 819) | down | 160 | 1.1 | round_robin |
| Q11 | (576, -160) | (736, -160) | right | 160 | 3.8 | least_targeted |
| Q12 | (576, -208) | (732, -208) | right | 156 | 3.8 | least_targeted |
| Q13 | (576, -256) | (736, -256) | right | 160 | 3.8 | least_targeted |
| Q14 | (576, -304) | (736, -304) | right | 160 | 3.8 | least_targeted |
| Q15 | (576, -352) | (736, -352) | right | 160 | 3.8 | least_targeted |
| Q16 | (576, -400) | (736, -400) | right | 160 | 3.8 | least_targeted |
| Q17 | (640, -448) | (480, -448) | left | 160 | 3.8 | least_targeted |
| Q18 | (-704, 448) | (-544, 448) | right | 160 | 3.8 | least_targeted |
| Q19 | (-704, 256) | (-544, 256) | right | 160 | 3.8 | least_targeted |
| Q20 | (-704, 208) | (-544, 208) | right | 160 | 3.8 | least_targeted |
| Q21 | (-704, 160) | (-544, 160) | right | 160 | 3.8 | least_targeted |
| Q22 | (-704, -176) | (-544, -176) | right | 160 | 3.8 | least_targeted |
| Q23 | (-704, -128) | (-544, -128) | right | 160 | 3.8 | least_targeted |
| Q24 | (-640, -80) | (-800, -80) | left | 160 | 3.8 | least_targeted |
| Q25 | (-640, -32) | (-800, -32) | left | 160 | 3.8 | least_targeted |
| Q26 | (-640, 16) | (-800, 16) | left | 160 | 3.8 | least_targeted |
| Q27 | (-640, 64) | (-800, 64) | left | 160 | 3.8 | least_targeted |
| Q28 | (-640, 112) | (-800, 112) | left | 160 | 3.8 | least_targeted |
| Q29 | (-640, 304) | (-800, 304) | left | 160 | 3.8 | least_targeted |
| Q30 | (-640, 352) | (-800, 352) | left | 160 | 3.8 | least_targeted |
| Q31 | (-640, 400) | (-800, 400) | left | 160 | 3.8 | least_targeted |
| Q32 | (-784, -784) | (-784, -624) | down | 160 | 3.8 | least_targeted |
| Q33 | (-928, -784) | (-928, -624) | down | 160 | 3.8 | least_targeted |
| Q34 | (-880, -784) | (-880, -624) | down | 160 | 3.8 | least_targeted |
| Q35 | (-832, -784) | (-832, -624) | down | 160 | 3.8 | least_targeted |

### B.2 O2T1E1.tscn

| Queue | Head | Tail | Head to Tail | Length (px) | Interval | Transition |
|---|---:|---:|---|---:|---:|---|
| Q | (640, 512) | (480, 512) | left | 160 | 3.8 | least_targeted |
| Q2 | (640, 464) | (480, 464) | left | 160 | 3.8 | least_targeted |
| Q3 | (640, 416) | (480, 416) | left | 160 | 3.8 | least_targeted |
| Q4 | (640, 368) | (480, 368) | left | 160 | 3.8 | least_targeted |
| Q5 | (576, 320) | (736, 320) | right | 160 | 3.8 | least_targeted |
| Q6 | (576, 272) | (736, 272) | right | 160 | 3.8 | least_targeted |
| Q7 | (576, 224) | (736, 224) | right | 160 | 3.8 | least_targeted |
| Q8 | (576, 176) | (736, 176) | right | 160 | 3.8 | least_targeted |
| Q9 | (352, 660) | (352, 820) | down | 160 | 1.1 | round_robin |
| Q10 | (228, 659) | (228, 819) | down | 160 | 1.1 | round_robin |
| Q11 | (576, -160) | (736, -160) | right | 160 | 3.8 | least_targeted |
| Q12 | (576, -208) | (732, -208) | right | 156 | 3.8 | least_targeted |
| Q13 | (576, -256) | (736, -256) | right | 160 | 3.8 | least_targeted |
| Q14 | (576, -304) | (736, -304) | right | 160 | 3.8 | least_targeted |
| Q15 | (576, -352) | (736, -352) | right | 160 | 3.8 | least_targeted |
| Q16 | (576, -400) | (736, -400) | right | 160 | 3.8 | least_targeted |
| Q17 | (640, -448) | (480, -448) | left | 160 | 3.8 | least_targeted |
| Q18 | (-704, 448) | (-544, 448) | right | 160 | 3.8 | least_targeted |
| Q19 | (-704, 256) | (-544, 256) | right | 160 | 3.8 | least_targeted |
| Q20 | (-704, 208) | (-544, 208) | right | 160 | 3.8 | least_targeted |
| Q21 | (-704, 160) | (-544, 160) | right | 160 | 3.8 | least_targeted |
| Q22 | (-704, -176) | (-544, -176) | right | 160 | 3.8 | least_targeted |
| Q23 | (-704, -128) | (-544, -128) | right | 160 | 3.8 | least_targeted |
| Q24 | (-640, -80) | (-800, -80) | left | 160 | 3.8 | least_targeted |
| Q25 | (-640, -32) | (-800, -32) | left | 160 | 3.8 | least_targeted |
| Q26 | (-640, 16) | (-800, 16) | left | 160 | 3.8 | least_targeted |
| Q27 | (-640, 64) | (-800, 64) | left | 160 | 3.8 | least_targeted |
| Q28 | (-640, 112) | (-800, 112) | left | 160 | 3.8 | least_targeted |
| Q29 | (-640, 304) | (-800, 304) | left | 160 | 3.8 | least_targeted |
| Q30 | (-640, 352) | (-800, 352) | left | 160 | 3.8 | least_targeted |
| Q31 | (-640, 400) | (-800, 400) | left | 160 | 3.8 | least_targeted |
| Q32 | (-784, -784) | (-784, -624) | down | 160 | 3.8 | least_targeted |
| Q33 | (-928, -784) | (-928, -624) | down | 160 | 3.8 | least_targeted |
| Q34 | (-880, -784) | (-880, -624) | down | 160 | 3.8 | least_targeted |
| Q35 | (-832, -784) | (-832, -624) | down | 160 | 3.8 | least_targeted |

### B.3 O1T2E1.tscn

| Queue | Head | Tail | Head to Tail | Length (px) | Interval | Transition |
|---|---:|---:|---|---:|---:|---|
| Q | (576, 512) | (736, 512) | right | 160 | 3.8 | least_targeted |
| Q2 | (640, 464) | (480, 464) | left | 160 | 3.8 | least_targeted |
| Q3 | (576, 416) | (736, 416) | right | 160 | 3.8 | least_targeted |
| Q4 | (640, 368) | (480, 368) | left | 160 | 3.8 | least_targeted |
| Q5 | (576, 320) | (736, 320) | right | 160 | 3.8 | least_targeted |
| Q6 | (640, 272) | (480, 272) | left | 160 | 3.8 | least_targeted |
| Q7 | (576, 224) | (736, 224) | right | 160 | 3.8 | least_targeted |
| Q8 | (640, 176) | (480, 176) | left | 160 | 3.8 | least_targeted |
| Q9 | (352, 660) | (352, 820) | down | 160 | 1.1 | round_robin |
| Q10 | (224, 656) | (224, 816) | down | 160 | 1.1 | round_robin |
| Q11 | (640, -160) | (480, -160) | left | 160 | 3.8 | least_targeted |
| Q12 | (576, -208) | (668, -208) | right | 92 | 3.8 | least_targeted |
| Q13 | (640, -256) | (480, -256) | left | 160 | 3.8 | least_targeted |
| Q14 | (576, -304) | (736, -304) | right | 160 | 3.8 | least_targeted |
| Q15 | (640, -352) | (480, -352) | left | 160 | 3.8 | least_targeted |
| Q16 | (576, -400) | (736, -400) | right | 160 | 3.8 | least_targeted |
| Q17 | (640, -448) | (480, -448) | left | 160 | 3.8 | least_targeted |
| Q18 | (-704, 448) | (-544, 448) | right | 160 | 3.8 | least_targeted |
| Q19 | (-704, 256) | (-544, 256) | right | 160 | 3.8 | least_targeted |
| Q20 | (-640, 208) | (-800, 208) | left | 160 | 3.8 | least_targeted |
| Q21 | (-704, 160) | (-544, 160) | right | 160 | 3.8 | least_targeted |
| Q22 | (-640, -176) | (-800, -176) | left | 160 | 3.8 | least_targeted |
| Q23 | (-704, -128) | (-544, -128) | right | 160 | 3.8 | least_targeted |
| Q24 | (-640, -80) | (-800, -80) | left | 160 | 3.8 | least_targeted |
| Q25 | (-704, -32) | (-544, -32) | right | 160 | 3.8 | least_targeted |
| Q26 | (-640, 16) | (-800, 16) | left | 160 | 3.8 | least_targeted |
| Q27 | (-704, 64) | (-544, 64) | right | 160 | 3.8 | least_targeted |
| Q28 | (-640, 112) | (-800, 112) | left | 160 | 3.8 | least_targeted |
| Q29 | (-640, 304) | (-800, 304) | left | 160 | 3.8 | least_targeted |
| Q30 | (-704, 352) | (-544, 352) | right | 160 | 3.8 | least_targeted |
| Q31 | (-640, 400) | (-800, 400) | left | 160 | 3.8 | least_targeted |
| Q32 | (-784, -784) | (-784, -624) | down | 160 | 3.8 | least_targeted |
| Q33 | (-928, -784) | (-928, -624) | down | 160 | 3.8 | least_targeted |
| Q34 | (-880, -784) | (-880, -624) | down | 160 | 3.8 | least_targeted |
| Q35 | (-832, -784) | (-832, -624) | down | 160 | 3.8 | least_targeted |
