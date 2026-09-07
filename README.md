<img width="1267" height="952" alt="Screenshot from 2026-09-07 09-19-58" src="https://github.com/user-attachments/assets/ea535dc1-9116-43ee-a277-be3a8c357698" />
# Battery Manager for Home Assistant

A custom Home Assistant integration that automatically detects every battery-powered device in your instance and tracks the exact battery *type* it takes (AA, CR2032, CR123A, etc.) — without creating a single new entity, and without you ever having to type it in by hand.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=lyntoo&repository=battery-manager-ha&category=integration)

---

## Why

Home Assistant already tells you a battery is at 12%. It has no idea what to actually buy to fix that. Existing solutions to track battery *type* per device add a second, parallel entity per device — and that new entity sometimes gets picked as the "primary" one on a device card, burying the real battery-level sensor. Battery Manager tracks type as pure metadata, never as a competing entity.

---

## Features

- **Zero manual entry, most of the time** — ships with a built-in lookup table (140+ entries) covering common Zigbee/Z-Wave/Bluetooth/WiFi device families (Aqara, Sonoff, IKEA, Philips Hue, SwitchBot, Zooz, Aeotec, Fibaro, Ring, YoLink, Eve, and more). Matching devices get their battery type filled in automatically the first time they're seen.
- **No new entities, ever** — the type is stored via Home Assistant's own internal `Store` helper (the same mechanism core uses for its own config), never as a `sensor`/`input_*` that could shadow the real battery entity.
- **Fully dynamic detection** — queries the entity/device registries live on every load for anything with a `battery` or `battery_charging` device class. New devices show up with no configuration.
- **Selector per device** — every device gets a dropdown of common battery types, always editable, with an "Unknown" default and the ability to add/remove your own custom types.
- **Self-teaching database** — click 🎓 on any device to remember its battery type for every current *and future* device sharing the same manufacturer/model — no code changes needed.
- **Smart exclusion for non-replaceable batteries** — phones (via the mobile app integration), vacuums, lawn mowers, and any device whose assigned type is a soldered/rechargeable pack are hidden automatically, with a one-click way to review or un-hide them.
- **Sortable table** — click any column header (Name, Level, Type) to sort; a one-click toggle returns to the default area-grouped view.

---

## Requirements

- Home Assistant Core with `panel_custom`, `http`, and `websocket_api` (all stable core components)
- No extra Python dependencies (uses only Home Assistant's own stdlib APIs)

---

## Installation

### Via HACS (custom repository)

1. Click the badge above, or go to **HACS → Integrations → ⋮ → Custom repositories**
2. Add `https://github.com/lyntoo/battery-manager-ha` as an **Integration**
3. Search for **Battery Manager** and install
4. Restart Home Assistant

### Manual

1. Copy the `custom_components/battery_manager` folder into your HA `config/custom_components/` directory
2. Restart Home Assistant

---

## Setup

No accounts, no credentials, no configuration form.

1. Go to **Settings → Devices & services → Add Integration**
2. Search for **Battery Manager** and confirm

A **Batteries** panel appears in the sidebar immediately. Only a single instance can be created.

---

## Uninstalling

**Settings → Devices & services → Battery Manager → ⋮ → Delete**, then remove the `custom_components/battery_manager` folder (or remove it via HACS). All stored battery types live in `.storage/battery_manager.battery_types` and are removed with the integration — nothing is left behind in your entity or device registry, since none were ever created.

---

## How it works

- **Storage:** Home Assistant's own `Store` helper — versioned, async, `.storage/battery_manager.battery_types` — never an entity.
- **Detection:** live queries against the entity/device registries for `device_class: battery` (sensor) and `battery` / `battery_charging` (binary_sensor), grouped by device.
- **Lookup:** a built-in seed table (manufacturer/model substring match) plus a separately-stored "learned" table that grows every time you confirm a type via the panel — the seed file itself is never modified at runtime.
- **Frontend:** a single self-contained vanilla JS file (no build step, no external dependency), registered as a `panel_custom` sidebar panel.

---

## Disclaimer

This project is not affiliated with or endorsed by Home Assistant / Nabu Casa, nor by any device manufacturer mentioned in its built-in lookup table. Battery type suggestions are provided as a starting point — always double-check before buying replacements for a device not explicitly confirmed on its own packaging or manual.
