"""Constants for the Battery Manager integration."""

DOMAIN = "battery_manager"
URL_BASE = "/battery_manager_static"
PANEL_URL_PATH = "battery-manager"
PANEL_TITLE = "Batteries"
PANEL_ICON = "mdi:battery-unknown"

STORAGE_KEY = "battery_manager.battery_types"
STORAGE_VERSION = 1

# Types de piles/batteries IoT courants, propose par defaut dans le selecteur.
# Non supprimables (contrairement aux types custom ajoutes par l'utilisateur).
DEFAULT_BATTERY_TYPES = [
    "AA",
    "AAA",
    "AAAA",
    "C",
    "D",
    "9V",
    "CR2032",
    "CR2025",
    "CR2016",
    "CR1632",
    "CR1220",
    "CR2450",
    "CR2477",
    "CR123A",
    "CR2",
    "CR-P2",
    "ER14250",
    "18650",
    "21700",
    "14500",
    "26650",
    "LR44 / AG13",
    "LR41",
    "A23",
    "N (LR1)",
    "Pack Li-ion proprietaire",
    "Pack Li-Po proprietaire",
    "Pack NiMH proprietaire",
]

UNKNOWN_TYPE = "Unknown"

# Auto-exclusion : appareils dont la "pile" est en realite un pack rechargeable
# non remplacable par l'utilisateur (telephones, robots, tondeuses). Masques
# par defaut sans intervention — l'utilisateur peut toujours les reafficher.
AUTO_HIDE_CONFIG_DOMAINS = {"mobile_app"}
AUTO_HIDE_IF_HAS_ENTITY_DOMAIN = {"vacuum", "lawn_mower"}

# Regle generale, plus large que les deux heuristiques ci-dessus : n'importe
# quel appareil dont le type de pile *connu* (assigne, auto-rempli ou appris)
# est un pack rechargeable non remplacable est masque automatiquement, peu
# importe son integration/domaine d'origine (couvre les cas non capturables
# par domaine, ex: SwitchBot Curtain/BlindTilt, AWTRIX, etc.).
RECHARGEABLE_PACK_TYPES = {
    "Pack Li-ion proprietaire",
    "Pack Li-Po proprietaire",
    "Pack NiMH proprietaire",
}
