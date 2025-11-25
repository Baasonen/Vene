# Asetukset

DEBUG_MODE = 0
FULLSCREEN = True

LIGHT_THEME = {
    "bg": "#ffffff",
    "fg": "#000000",
    "button_bg": "#f0f0f0",
    "entry_bg": "#ffffff"
}

DARK_THEME = {
    "bg": "#232327",
    "fg": "#FFFFFF",
    "button_bg": "#333237",
    "entry_bg": "#333237"
}

MAP_CONFIG = {
    "default_position": (60.185921, 24.825963),
    "default_zoom": 15,
    "offline_db": "offline_tiles.db", #jos haluaa käyttä jotain muuta, esim. ladata satelliittikuvan
    #Offline downloading
    "loader_enabled": False,  #käytä vain jos tarvii ladata lisää karttaa, aseta parametrit alla
    "top_left": (60.192612, 24.782965), #(60.19711, 24.81159)
    "bottom_right": (60.153433, 24.862890), #(60.18064, 24.85399)
    "zoom_min": 0,
    "zoom_max": 18, #Varovasti, zoom_level 20:n mittakaava on jo 1:500.
    "tile_server": "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"
}

CONTROLLER_CONFIG = {
    "deadzone": 0.07,  # 0.00 - 1.00
    "poll_interval": 50
}
