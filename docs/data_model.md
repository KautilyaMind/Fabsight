# FabSight v0.1 data model

FabSight v0.1 contains **synthetic educational simulation data**. It is a small,
simplified model for learning data engineering concepts around semiconductor
manufacturing. It does not reproduce data, recipes, tools, sensor definitions,
alarms, or standard operating procedures from a real manufacturer.

```text
LOT
 │
 ├── WAFER
 │     │
 │     └── PROCESS_EVENT
 │              │
 │              ├── PROCESS_STEP
 │              └── TOOL
 │
TOOL
 ├── MAINTENANCE
 └── ALARM
```

## Tables

### `lots.csv`

A lot is a group of wafers that enters the simulated fab together. Each lot has a
fictional product family, priority, status, start time, and wafer count.

### `wafers.csv`

A wafer is one simulated circular substrate in a lot. `lot_id` links every wafer to
exactly one lot. The wafer count is intentionally simplified to 10–25 per lot.

### `process_steps.csv`

This table defines the seven-stage educational route. Clean, deposition,
lithography, etch, implant, CMP (planarization), and inspection are broad concepts;
the table contains no detailed production recipes.

### `tools.csv`

A tool is a fictional piece of equipment capable of one category of work. Names and
IDs were invented for this project and do not identify real factory equipment.

### `process_events.csv`

Each event records one wafer visiting one tool for one process step. It connects a
wafer and its lot to the route and tool. Start and end times follow route order.
Statuses are independent random workflow outcomes, not effects of alarms,
maintenance, or hidden simulated conditions.

### `maintenance.csv`

These rows record generic, fictional maintenance windows for tools. Descriptions are
deliberately high-level and are not engineering procedures.

### `alarms.csv`

These rows record generic fictional software notifications associated with tools.
They are independent of process results and do not correspond to real alarm codes.

## Keys and relationships

| Child column | Parent column | Meaning |
|---|---|---|
| `wafers.lot_id` | `lots.lot_id` | The lot that owns the wafer |
| `process_events.wafer_id` | `wafers.wafer_id` | The wafer being processed |
| `process_events.lot_id` | `lots.lot_id` | Convenient lot reference for the event |
| `process_events.step_id` | `process_steps.step_id` | The educational route stage |
| `process_events.tool_id` | `tools.tool_id` | The fictional tool used |
| `maintenance.tool_id` | `tools.tool_id` | The maintained tool |
| `alarms.tool_id` | `tools.tool_id` | The tool reporting the fictional alarm |
