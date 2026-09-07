"""Seed database: manufacturer/model -> type de pile connu.

Base de depart couvrant des familles d'appareils IoT courantes (Zigbee,
Z-Wave, Bluetooth, WiFi). Volontairement non-exhaustive — impossible de
couvrir toute la panoplie existante. Complementee au fil du temps par la
base "apprise" (learned_devices) stockee separement, qui grandit chaque
fois qu'un type est confirme via le panneau (par l'utilisateur ou par
recherche), sans jamais toucher a ce fichier.

Format : (manufacturer_substring, model_substring, battery_type).
Comparaison insensible a la casse, par sous-chaine (les integrations HA
rapportent manufacturer/model de facon inconsistante d'un appareil a
l'autre — ex: "Aqara" vs "LUMI", "SNZB-02" vs "SNZB-02P").
Le premier match (manufacturer ET model tous deux trouves dans la chaine
de l'appareil) l'emporte.
"""

from __future__ import annotations

# (manufacturer contient, model contient, type de pile)
KNOWN_DEVICE_BATTERY_TYPES: list[tuple[str, str, str]] = [
    # --- Aqara / Xiaomi (Zigbee) ---
    # ATTENTION ORDRE : les variantes P1/T1 (sous-chaines plus specifiques)
    # doivent toujours precede la sous-chaine generique du meme appareil —
    # sinon le match generique gagne en premier et retourne le mauvais
    # format de pile (ex: P1 Door/Window = CR123A 1400mAh, vs CR1632 sur le
    # modele standard MCCGQ11LM — corrige suite a un vrai cas trouve
    # 2026-09-07, meme piege deja evite pour motion sensor p1 ci-dessous).
    ("aqara", "door and window sensor p1", "CR123A"),
    ("aqara", "door and window", "CR1632"),
    ("aqara", "motion sensor p1", "CR2450"),
    ("aqara", "motion sensor", "CR2450"),
    ("aqara", "temperature", "CR2032"),
    ("aqara", "water leak", "CR2032"),
    ("aqara", "vibration", "CR2032"),
    ("aqara", "button", "CR2032"),
    ("lumi", "magnet", "CR1632"),
    ("xiaomi", "temperature", "CR2032"),
    ("aqara", "cube", "CR2450"),
    ("aqara", "fp1e", "CR2450"),
    ("aqara", "wireless switch", "CR2032"),
    ("aqara", "wireless mini switch", "CR2032"),
    ("aqara", "wireless remote switch", "CR2032"),
    ("aqara", "opple", "CR2032"),
    ("aqara", "high precision motion", "CR2450"),
    ("lumi", "sensor_ht", "CR2032"),
    ("aqara", "radiator thermostat", "AA"),
    ("aqara", "e1", "CR2032"),
    ("xiaomi", "lywsd03mmc", "CR2032"),

    # --- Sonoff (Zigbee) --- P-Series (pile plus grosse) avant la version de base
    ("sonoff", "snzb-01p", "CR2477"),
    ("sonoff", "snzb-02d", "CR2450"),
    ("sonoff", "snzb-02p", "CR2477"),
    ("sonoff", "snzb-02", "CR2450"),
    ("sonoff", "snzb-03p", "CR2477"),
    ("sonoff", "snzb-03", "CR2450"),
    ("sonoff", "snzb-04p", "CR2477"),
    ("sonoff", "snzb-04", "CR2450"),
    ("sonoff", "snzb-01", "CR2032"),
    ("sonoff", "trvzb", "AA"),

    # --- IKEA (ancienne et nouvelle gamme, Zigbee) ---
    ("ikea", "motion sensor", "CR2032"),
    ("ikea", "open/close", "CR2032"),
    ("ikea", "shortcut button", "CR2032"),
    ("ikea", "remote control", "CR2032"),
    ("ikea", "vallhorn", "AAA"),
    ("ikea", "parasoll", "AAA"),
    ("ikea", "somrig", "AAA"),
    ("ikea", "rodret", "AAA"),
    ("ikea", "styrbar", "AAA"),
    ("ikea", "symfonisk", "CR2032"),
    ("ikea", "styrman", "CR2032"),

    # --- MOES / Tuya generique (Zigbee/WiFi) ---
    ("moes", "door", "CR2032"),
    ("moes", "temperature", "CR2032"),
    ("tuya", "fingerbot", "CR2"),
    ("tuya", "light sensor", "CR2032"),
    ("tuya", "smart knob", "CR2032"),
    # Verifier soil_3 AVANT soil (model_id "ts0601_soil_3" contient "soil"
    # mais pas l'inverse) — sinon le match generique l'emporterait a tort.
    ("tuya", "soil_3", "AAA"),
    ("tuya", "soil_2", "AA"),
    ("tuya", "soil", "AA"),
    ("tuya", "ts0201", "AAA"),
    ("tuya", "ts0601_trv", "AA"),
    ("tuya", "zb-radar", "CR2450"),
    ("moes", "rad_valv", "AA"),
    ("_tz", "door", "CR2032"),
    ("_tz", "motion", "CR2450"),
    ("tuya", "door", "CR2032"),

    # --- Third Reality ---
    ("third reality", "button", "CR2032"),
    # Corrige 2026-09-07 : CR2450 etait une supposition non verifiee, la
    # vraie fiche produit confirme 2x AAA (deja applique en live via
    # learn_device sur zigbee_washing, maintenant aussi fixe ici).
    ("third reality", "motion", "AAA"),
    ("third reality", "watering kit", "AA"),
    ("third reality", "water", "AAA"),
    ("third reality", "door", "AAA"),

    # --- SwitchBot (Bluetooth) ---
    ("switchbot", "bot", "AA"),
    ("switchbot", "curtain", "Pack Li-ion proprietaire"),
    ("switchbot", "blindtilt", "Pack Li-ion proprietaire"),
    ("switchbot", "meter", "AAA"),
    ("switchbot", "contact sensor", "CR2450"),
    ("switchbot", "motion", "AAA"),
    ("switchbot", "hub", "Unknown"),

    # --- Blueforcer AWTRIX (pack rechargeable soude, non remplacable) ---
    ("blueforcer", "awtrix", "Pack Li-ion proprietaire"),

    # --- Zooz (Z-Wave) ---
    ("zooz", "motion", "CR123A"),
    ("zooz", "4-in-1", "CR123A"),
    ("zooz", "water", "CR123A"),
    # ZEN37 : pile LIR2032 rechargeable, souvent SOUDEE sur la carte
    # (v2.0+) — non remplacable malgre l'apparence CR2032.
    ("zooz", "zen37", "Pack Li-ion proprietaire"),
    ("zooz", "wall remote", "Pack Li-ion proprietaire"),

    # --- NEO / Tuya siren (Zigbee) ---
    ("neo", "nas-ab02b2", "CR123A"),
    ("neo", "alarm", "CR123A"),

    # --- Orbit / B-hyve (irrigation) ---
    ("orbit", "ht25", "AA"),
    ("b-hyve", "ht25", "AA"),

    # --- Ecolink (Z-Wave) ---
    ("ecolink", "door", "CR123A"),
    ("ecolink", "motion", "AA"),
    ("ecolink", "tilt", "CR123A"),
    ("ecolink", "garage", "CR123A"),

    # --- Fibaro (Z-Wave) ---
    ("fibaro", "door/window sensor 2", "ER14250"),
    ("fibaro", "door/window", "CR123A"),
    ("fibaro", "motion", "CR123A"),
    ("fibaro", "flood", "CR123A"),
    ("fibaro", "keyfob", "CR2450"),
    ("fibaro", "button", "ER14250"),

    # --- Ambient Weather --- modele generique non expose par l'integration
    # locale (awnet_local, identifiants MAC seulement) ; AA confirme pour le
    # module PM2.5 et convention generale de la gamme de capteurs exterieurs.
    ("ambient weather", "", "AA"),

    # --- Verrous / deadbolt (toutes marques) ---
    ("schlage", "", "AA"),
    ("yale", "", "AA"),
    ("kwikset", "", "AA"),
    ("august", "", "CR123A"),
    ("danalock", "", "CR123A"),
    ("shenzhen kaadas", "", "AA"),
    ("kaadas", "", "AA"),

    # --- Airthings (Bluetooth) ---
    ("airthings", "wave", "AA"),

    # --- Probe Plus (Bluetooth, pack rechargeable soude) ---
    ("probe plus", "", "Pack Li-ion proprietaire"),

    # --- PANDA e-ink ESL (Bluetooth) ---
    ("panda", "ble price tag", "CR2450"),

    # --- Uni-T (Bluetooth) ---
    ("uni-t", "ut353bt", "AAA"),

    # --- Moes (Zigbee) ---
    ("moes", "ir remote", "AAA"),
    ("moes", "ufo-r11", "AAA"),

    # --- Capteurs TPMS (pneus) — CR1632 x4 remplacable en externe sur les
    # modeles genre "TPMSII TypeA/SY36201" (fiche produit confirmee par
    # l'utilisateur, malgre l'idee recue que ces capteurs sont scelles).
    # Modele exact varie par capteur (identifiant unique), match sur le
    # fabricant seul.
    ("tpms", "", "CR1632"),

    # --- Philips Hue / Signify (Zigbee) ---
    ("signify", "rwl021", "CR2032"),
    ("signify", "rwl022", "CR2032"),
    ("signify", "dimmer switch", "CR2032"),
    ("philips", "dimmer switch", "CR2032"),
    ("philips", "hue motion", "AAA"),
    ("signify", "sml001", "AAA"),
    ("signify", "sml002", "AAA"),
    ("signify", "sml003", "AA"),
    ("signify", "outdoor motion", "AA"),
    ("signify", "motion sensor", "AAA"),
    ("philips", "hue tap dial", "CR2032"),
    ("signify", "smart button", "CR2032"),
    ("philips", "tap", "Unknown"),

    # --- Ring (Z-Wave) ---
    ("ring", "contact sensor", "CR1632"),
    ("ring", "motion detector", "AA"),
    ("ring", "keypad", "Pack Li-ion proprietaire"),
    ("ring", "glassbreak", "CR123A"),
    ("ring", "range extender", "Pack Li-ion proprietaire"),

    # --- Aeotec (Z-Wave) ---
    ("aeotec", "door sensor 7", "AAA"),
    ("aeotec", "multisensor 6", "CR123A"),
    ("aeotec", "trisensor", "CR123A"),
    ("aeotec", "recessed door", "CR2"),
    ("aeotec", "water sensor 7", "CR123A"),

    # --- Netatmo ---
    ("netatmo", "thermostat", "AAA"),
    ("netatmo", "valve", "AA"),
    ("netatmo", "weather", "AAA"),

    # --- Tado ---
    ("tado", "smart radiator thermostat", "AA"),
    ("tado", "wireless temperature", "AAA"),

    # --- Eve (Thread / Matter / BLE) ---
    ("eve", "door & window", "ER14250"),
    ("eve", "motion", "AAA"),
    ("eve", "weather", "CR2450"),
    ("eve", "thermo", "AA"),
    ("eve", "water guard", "AA"),

    # --- Samsung SmartThings / Samjin (Zigbee) ---
    ("samjin", "multi", "CR2032"),
    ("smartthings", "motion", "CR2450"),
    ("smartthings", "multipurpose", "CR2032"),

    # --- Frient / Develco (Zigbee) ---
    ("frient", "door", "CR2032"),
    ("develco", "door", "CR2032"),
    ("frient", "motion", "AA"),

    # --- Sensative (Z-Wave) ---
    ("sensative", "strip", "CR2450"),

    # --- YoLink (LoRa) --- specs confirmees (fiches produit officielles)
    ("yolink", "doorsensor", "AA"),
    ("yolink", "motionsensor", "AAA"),
    ("yolink", "leaksensor", "AAA"),
    ("yolink", "siren", "AA"),

    # --- Reolink (Bluetooth/WiFi cameras, quand a pile) ---
    ("reolink", "argus", "Pack Li-ion proprietaire"),

    # --- Nabu Casa / HA Voice PE (pile rechargeable interne) ---
    ("nabu casa", "voice", "Pack Li-ion proprietaire"),

    # --- PetSafe (WiFi) — piles de secours seulement, pas l'alimentation
    # principale (branche secteur), mais bien remplacables si installees.
    ("petsafe", "smartfeed", "D"),
]


def lookup_battery_type(manufacturer: str | None, model: str | None) -> str | None:
    """Cherche un type de pile connu par sous-chaine manufacturer+model.

    BUG CORRIGE (2026-09-07) : le model_substr doit matcher UNIQUEMENT dans
    le champ model, jamais dans manufacturer+model combines — sinon un
    model_substr generique comme "bot" matche par accident a l'interieur du
    nom du fabricant lui-meme (ex: "switchBOT" contient "bot"), causant de
    faux positifs sur des appareils totalement differents (Store/BlindTilt
    matchait a tort l'entree Bot -> AA a cause de ce chevauchement).
    """
    if not manufacturer and not model:
        return None
    manu = (manufacturer or "").lower()
    mdl = (model or "").lower()
    for manu_substr, model_substr, battery_type in KNOWN_DEVICE_BATTERY_TYPES:
        if manu_substr and manu_substr not in manu:
            continue
        if model_substr and model_substr not in mdl:
            continue
        return battery_type
    return None
