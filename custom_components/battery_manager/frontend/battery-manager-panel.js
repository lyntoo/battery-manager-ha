class BatteryManagerPanel extends HTMLElement {
  constructor() {
    super();
    this._hass = null;
    this._data = null;
    this._rendered = false;
    this._sortColumn = null; // null = groupe par zone (defaut)
    this._sortDirection = 1;
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first) {
      this._load();
    }
  }

  get hass() {
    return this._hass;
  }

  async _load() {
    this._data = await this._hass.connection.sendMessagePromise({
      type: "battery_manager/list",
    });
    this._render();
  }

  async _setType(key, batteryType) {
    await this._hass.connection.sendMessagePromise({
      type: "battery_manager/set_type",
      key,
      battery_type: batteryType,
    });
    const row = this._data.devices.find((d) => d.key === key);
    if (row) row.battery_type = batteryType;
    this._render();
  }

  async _addCustomType(name) {
    name = name.trim();
    if (!name) return;
    await this._hass.connection.sendMessagePromise({
      type: "battery_manager/add_custom_type",
      name,
    });
    await this._load();
  }

  async _learnDevice(key) {
    const row = this._data.devices.find((d) => d.key === key);
    if (!row) return;
    await this._hass.connection.sendMessagePromise({
      type: "battery_manager/learn_device",
      manufacturer: row.manufacturer || null,
      model: row.model || null,
      battery_type: row.battery_type,
    });
    await this._load();
  }

  async _hideDevice(key) {
    await this._hass.connection.sendMessagePromise({
      type: "battery_manager/hide_device",
      key,
    });
    await this._load();
  }

  async _unhideDevice(key) {
    await this._hass.connection.sendMessagePromise({
      type: "battery_manager/unhide_device",
      key,
    });
    await this._load();
  }

  async _deleteCustomType(name) {
    await this._hass.connection.sendMessagePromise({
      type: "battery_manager/delete_custom_type",
      name,
    });
    await this._load();
  }

  _batteryColor(level, low) {
    if (low === true) return "var(--error-color, #db4437)";
    if (level === null || level === undefined) return "var(--disabled-text-color, #888)";
    if (level <= 20) return "var(--error-color, #db4437)";
    if (level <= 40) return "var(--warning-color, #ff9800)";
    return "var(--success-color, #43a047)";
  }

  _setSort(column) {
    if (column === "area") {
      this._sortColumn = null;
    } else if (this._sortColumn === column) {
      this._sortDirection *= -1;
    } else {
      this._sortColumn = column;
      this._sortDirection = 1;
    }
    this._render();
  }

  _sortArrow(column) {
    if (this._sortColumn !== column) return "";
    return this._sortDirection === 1 ? " ▲" : " ▼";
  }

  _sortDevices(devices) {
    const col = this._sortColumn;
    const dir = this._sortDirection;
    const sorted = [...devices];
    sorted.sort((a, b) => {
      let cmp = 0;
      if (col === "name") {
        cmp = (a.name || "").localeCompare(b.name || "");
      } else if (col === "type") {
        cmp = (a.battery_type || "").localeCompare(b.battery_type || "");
      } else if (col === "level") {
        const av = a.battery_level === null || a.battery_level === undefined ? -1 : a.battery_level;
        const bv = b.battery_level === null || b.battery_level === undefined ? -1 : b.battery_level;
        cmp = av - bv;
      }
      return cmp * dir;
    });
    return sorted;
  }

  _groupByArea(devices) {
    const groups = new Map();
    for (const d of devices) {
      const area = d.area || "Sans zone";
      if (!groups.has(area)) groups.set(area, []);
      groups.get(area).push(d);
    }
    return groups;
  }

  _render() {
    if (!this._data) return;

    const { devices, hidden_devices, default_types, custom_types, unknown_type } = this._data;
    const allTypes = [unknown_type, ...default_types, ...custom_types];
    const flatSort = this._sortColumn !== null;

    const optionsHtml = (selected) =>
      allTypes
        .map(
          (t) =>
            `<option value="${this._esc(t)}" ${t === selected ? "selected" : ""}>${this._esc(t)}</option>`
        )
        .join("");

    const rowHtml = (d) => `
      <tr data-key="${this._esc(d.key)}">
        <td class="name">
          <div class="device-name">${this._esc(d.name)}</div>
          ${
            flatSort || d.manufacturer || d.model
              ? `<div class="device-sub">${this._esc(
                  [flatSort ? d.area || "Sans zone" : null, d.manufacturer, d.model]
                    .filter(Boolean)
                    .join(" · ")
                )}</div>`
              : ""
          }
        </td>
        <td class="level">
          <span class="dot" style="background:${this._batteryColor(d.battery_level, d.battery_low)}"></span>
          ${d.battery_level !== null && d.battery_level !== undefined ? Math.round(d.battery_level) + "%" : d.battery_low === true ? "Basse" : "—"}
        </td>
        <td class="type">
          <select class="type-select">${optionsHtml(d.battery_type)}</select>
          ${d.auto_filled ? '<span class="db-badge" title="Suggere par la base de donnees — modifiable">🗄️</span>' : ""}
        </td>
        <td class="actions">
          ${d.manufacturer || d.model ? `<button class="learn-btn" title="Retenir ce type pour tous les appareils ${this._esc([d.manufacturer, d.model].filter(Boolean).join(" "))}">🎓</button>` : ""}
          <button class="reset-btn" title="Reinitialiser a Unknown">↺</button>
          <button class="hide-btn" title="Masquer cet appareil (pile non remplacable, etc.)">🗑️</button>
        </td>
      </tr>
    `;

    const headHtml = `
      <thead><tr>
        <th class="sortable" data-sort="name">Nom${this._sortArrow("name")}</th>
        <th class="sortable" data-sort="level">Niveau${this._sortArrow("level")}</th>
        <th class="sortable" data-sort="type">Type${this._sortArrow("type")}</th>
        <th></th>
      </tr></thead>
    `;

    const groupsHtml = flatSort
      ? this._sortDevices(devices).map(rowHtml).join("")
      : [...this._groupByArea(devices).entries()]
          .sort(([a], [b]) => a.localeCompare(b))
          .map(
            ([area, rows]) => `
              <tr class="area-header"><td colspan="4">${this._esc(area)}</td></tr>
              ${rows.map(rowHtml).join("")}
            `
          )
          .join("");

    const customTypesHtml = custom_types
      .map(
        (t) => `
          <span class="custom-type-chip">
            ${this._esc(t)}
            <button class="del-custom" data-name="${this._esc(t)}" title="Supprimer ce type">×</button>
          </span>
        `
      )
      .join("");

    this.innerHTML = `
      <style>
        :host { display: block; }
        .bm-wrap {
          padding: 16px;
          max-width: 1000px;
          margin: 0 auto;
          font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif);
          color: var(--primary-text-color);
        }
        h1 { font-size: 24px; font-weight: 400; margin: 8px 0 16px; }
        .title-row { display: flex; align-items: center; justify-content: space-between; }
        .group-reset-btn {
          background: none; border: 1px solid var(--divider-color, #444); border-radius: 6px;
          color: var(--primary-text-color); cursor: pointer; padding: 6px 12px; font-size: 12px;
          margin-bottom: 8px;
        }
        .group-reset-btn:hover { border-color: var(--primary-color, #03a9f4); }
        thead th {
          text-align: left; padding: 8px 12px; font-size: 12px; font-weight: 600;
          text-transform: uppercase; letter-spacing: 0.04em; color: var(--secondary-text-color);
          border-bottom: 1px solid var(--divider-color, #333);
          background: var(--secondary-background-color, #2a2a2a);
        }
        thead th.sortable { cursor: pointer; user-select: none; }
        thead th.sortable:hover { color: var(--primary-text-color); }
        .bm-card {
          background: var(--card-background-color, #1c1c1c);
          border-radius: var(--ha-card-border-radius, 12px);
          box-shadow: var(--ha-card-box-shadow, none);
          border: 1px solid var(--divider-color, #333);
          overflow: hidden;
          margin-bottom: 24px;
        }
        table { width: 100%; border-collapse: collapse; }
        td { padding: 8px 12px; border-bottom: 1px solid var(--divider-color, #333); vertical-align: middle; }
        tr.area-header td {
          background: var(--secondary-background-color, #2a2a2a);
          font-weight: 600;
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 0.04em;
          color: var(--secondary-text-color);
          padding: 6px 12px;
        }
        .device-name { font-size: 14px; }
        .device-sub { font-size: 12px; color: var(--secondary-text-color); }
        .dot {
          display: inline-block; width: 10px; height: 10px; border-radius: 50%;
          margin-right: 6px; vertical-align: middle;
        }
        .level { white-space: nowrap; font-size: 13px; }
        select.type-select {
          background: var(--card-background-color, #1c1c1c);
          color: var(--primary-text-color);
          border: 1px solid var(--divider-color, #444);
          border-radius: 6px;
          padding: 4px 8px;
          font-size: 13px;
          max-width: 220px;
        }
        .reset-btn, .learn-btn {
          background: none; border: none; cursor: pointer;
          color: var(--secondary-text-color); font-size: 16px;
          padding: 4px 8px;
        }
        .reset-btn:hover, .learn-btn:hover { color: var(--primary-text-color); }
        .actions { text-align: right; white-space: nowrap; }
        .db-badge { margin-left: 6px; font-size: 13px; cursor: help; }
        .manage-section h2 { font-size: 16px; font-weight: 500; margin: 0 0 8px; }
        .manage-card {
          background: var(--card-background-color, #1c1c1c);
          border-radius: var(--ha-card-border-radius, 12px);
          border: 1px solid var(--divider-color, #333);
          padding: 16px;
        }
        .custom-types-list { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
        .custom-type-chip {
          background: var(--secondary-background-color, #2a2a2a);
          border-radius: 16px;
          padding: 4px 6px 4px 12px;
          font-size: 13px;
          display: inline-flex; align-items: center; gap: 6px;
        }
        .del-custom {
          background: none; border: none; cursor: pointer;
          color: var(--secondary-text-color); font-size: 15px; line-height: 1;
          padding: 2px 6px;
        }
        .del-custom:hover { color: var(--error-color, #db4437); }
        .add-row { display: flex; gap: 8px; }
        .add-row input {
          flex: 1;
          background: var(--card-background-color, #1c1c1c);
          color: var(--primary-text-color);
          border: 1px solid var(--divider-color, #444);
          border-radius: 6px;
          padding: 6px 10px;
          font-size: 13px;
        }
        .add-row button {
          background: var(--primary-color, #03a9f4);
          color: white; border: none; border-radius: 6px;
          padding: 6px 16px; cursor: pointer; font-size: 13px;
        }
        .empty { padding: 24px; text-align: center; color: var(--secondary-text-color); }
        .hidden-section { margin-bottom: 24px; }
        .hidden-section summary {
          cursor: pointer; font-size: 13px; color: var(--secondary-text-color);
          padding: 4px 0;
        }
        .unhide-btn {
          background: none; border: 1px solid var(--divider-color, #444); border-radius: 6px;
          color: var(--primary-text-color); cursor: pointer; padding: 4px 12px; font-size: 12px;
        }
        .unhide-btn:hover { border-color: var(--primary-color, #03a9f4); }
      </style>
      <div class="bm-wrap">
        <div class="title-row">
          <h1>🔋 Batteries</h1>
          ${
            flatSort
              ? `<button class="group-reset-btn" data-sort="area">↺ Grouper par zone</button>`
              : ""
          }
        </div>
        <div class="bm-card">
          ${
            devices.length
              ? `<table>${headHtml}<tbody>${groupsHtml}</tbody></table>`
              : `<div class="empty">Aucun appareil a pile detecte pour l'instant.</div>`
          }
        </div>

        ${
          hidden_devices.length
            ? `
        <details class="hidden-section">
          <summary>Appareils masques (${hidden_devices.length})</summary>
          <div class="bm-card" style="margin-top:8px;">
            <table><tbody>
              ${hidden_devices
                .map(
                  (d) => `
                <tr data-key="${this._esc(d.key)}">
                  <td class="name">
                    <div class="device-name">${this._esc(d.name)}</div>
                    ${d.manufacturer || d.model ? `<div class="device-sub">${this._esc([d.manufacturer, d.model].filter(Boolean).join(" · "))}</div>` : ""}
                  </td>
                  <td style="font-size:12px;color:var(--secondary-text-color);">
                    ${d.manually_hidden ? "Masque manuellement" : "Masque auto (pile non remplacable)"}
                  </td>
                  <td class="actions"><button class="unhide-btn">Afficher</button></td>
                </tr>
              `
                )
                .join("")}
            </tbody></table>
          </div>
        </details>
        `
            : ""
        }

        <div class="manage-section">
          <h2>Types de piles personnalises</h2>
          <div class="manage-card">
            <div class="custom-types-list">
              ${custom_types.length ? customTypesHtml : '<span style="color:var(--secondary-text-color);font-size:13px;">Aucun type custom ajoute.</span>'}
            </div>
            <div class="add-row">
              <input type="text" id="new-type-input" placeholder="Ex: Pack 3.7V proprietaire XYZ" />
              <button id="add-type-btn">Ajouter</button>
            </div>
          </div>
        </div>
      </div>
    `;

    this.querySelectorAll("th.sortable, .group-reset-btn").forEach((el) => {
      el.addEventListener("click", (e) => {
        this._setSort(e.target.dataset.sort || e.currentTarget.dataset.sort);
      });
    });

    this.querySelectorAll(".type-select").forEach((sel) => {
      sel.addEventListener("change", (e) => {
        const key = e.target.closest("tr").dataset.key;
        this._setType(key, e.target.value);
      });
    });

    this.querySelectorAll(".reset-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const key = e.target.closest("tr").dataset.key;
        this._setType(key, unknown_type);
      });
    });

    this.querySelectorAll(".learn-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const key = e.target.closest("tr").dataset.key;
        this._learnDevice(key);
      });
    });

    this.querySelectorAll(".hide-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const key = e.target.closest("tr").dataset.key;
        this._hideDevice(key);
      });
    });

    this.querySelectorAll(".unhide-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const key = e.target.closest("tr").dataset.key;
        this._unhideDevice(key);
      });
    });

    this.querySelectorAll(".del-custom").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        this._deleteCustomType(e.target.dataset.name);
      });
    });

    const addBtn = this.querySelector("#add-type-btn");
    const addInput = this.querySelector("#new-type-input");
    addBtn.addEventListener("click", () => this._addCustomType(addInput.value));
    addInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") this._addCustomType(addInput.value);
    });
  }

  _esc(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
}

customElements.define("battery-manager-panel", BatteryManagerPanel);
