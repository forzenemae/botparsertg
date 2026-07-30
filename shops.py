SHOPS = {
    "shop1": {
        "name": "Street Beat",
        "url": "https://www.avito.ru/moskva_i_mo/odezhda_obuv_aksessuary?context=H4sIAAAAAAAA_wE-AMH_YToyOntzOjk6ImZyb21fcGFnZSI7czo3OiJmaWx0ZXJzIjtzOjE0OiJoYXNFeHRyYVBhcmFtcyI7YjoxO302Cz8HPgAAAA&geoCoords=55.755814%2C37.617635&presentationType=serp&q=street%20beat%20чек&radius=0",
        "description": "STBT",
        "check_words": ["чек", "чеком", "с чеком", "оригинальный чек"]
    }
}

CURRENT_SHOP = "shop1"

def get_shop_url(shop_id: str) -> str:
    return SHOPS.get(shop_id, {}).get("url", "")

def get_shop_name(shop_id: str) -> str:
    return SHOPS.get(shop_id, {}).get("name", "Неизвестный магазин")

def get_shop_description(shop_id: str) -> str:
    return SHOPS.get(shop_id, {}).get("description", "")

def get_shop_check_words(shop_id: str) -> list:
    return SHOPS.get(shop_id, {}).get("check_words", ["чек"])