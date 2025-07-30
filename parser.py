import asyncio
import aiohttp
import pandas as pd
import logging
import time

MENU_URL = "https://static-basket-01.wb.ru/vol0/data/main-menu-ru-ru-v2.json"
EXCEL_FILE = "wildberries_categories.xlsx"
TIME_LIMIT = 60

#логги
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


async def fetch_json(session: aiohttp.ClientSession, url: str, params: dict = None) -> dict:
    try:
        async with session.get(url, params=params, timeout=10) as resp:
            if resp.status == 404:
                logging.debug(f"404: {url}")
                return {}
            resp.raise_for_status()
            return await resp.json()
    except asyncio.TimeoutError:
        logging.warning(f"таймаут запроса {url}")
    except aiohttp.ClientError as e:
        logging.warning(f"ошибка запроса {url}: {e}")
    except Exception as e:
        logging.error(f"не удалось декодить JSON с {url}: {e}")
    return {}


async def fetch_products(session: aiohttp.ClientSession, cat_id: int, shard: str) -> list[tuple]:
    if not shard:
        return []

    products = []
    page = 1
    while True:
        params = {"appType": 1, "curr": "rub", "page": page, "xsubject": cat_id}
        url = f"https://catalog.wb.ru/catalog/{shard}/catalog"
        data = await fetch_json(session, url, params=params)
        if not data:
            break

        items = data.get("data", {}).get("products", [])
        if not items:
            break

        for item in items:
            pid = item.get("id")
            pname = item.get("name", "")
            if pid:
                products.append((pid, pname, 99))
        page += 1

    logging.info(f"Собрано {len(products)} товаров (cat_id={cat_id})")
    return products


async def process_category(session: aiohttp.ClientSession, root: dict, writer, start_time: float):
    if time.time() - start_time > TIME_LIMIT:
        logging.warning(f"пропуск {root.get('name')} по времени")
        return

    root_name = root.get("name", "Category")
    sheet_name = "".join(ch if ch not in "[]*?/\\:" else "_" for ch in root_name)[:31]

    results = []
    tasks = []
    final_positions = []

    def recurse(cat: dict, level: int):
        cid = cat.get("id")
        name = cat.get("name", "")
        shard = cat.get("shard", "")
        results.append((cid, name, level))

        childs = cat.get("childs") or []
        if childs:
            for subcat in childs:
                recurse(subcat, level + 1)
        else:
            if shard:
                final_positions.append(len(results) - 1)
                tasks.append(fetch_products(session, cid, shard))

    recurse(root, 1)

    if tasks:
        logging.info(f"загружаем товары {root_name}...")
        products_lists = await asyncio.gather(*tasks)

        offset = 0
        for pos, prod_list in zip(final_positions, products_lists):
            insert_index = pos + 1 + offset
            for product in prod_list:
                results.insert(insert_index, product)
                insert_index += 1
                offset += 1

    #excel
    df = pd.DataFrame(results, columns=["ID", "Название", "Уровень"])
    df.to_excel(writer, sheet_name=sheet_name, index=False)


async def main():
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        logging.info("загрузка категорий...")
        menu_data = await fetch_json(session, MENU_URL)
        if not isinstance(menu_data, list):
            logging.error("ошибка json")
            return

        logging.info(f"найдено {len(menu_data)} корневых категорий.")
        with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl") as writer:
            for root in menu_data:
                if time.time() - start_time > TIME_LIMIT:
                    logging.warning("время вышло")
                    break
                logging.info(f"обрабатываем {root.get('name', 'Без имени')}...")
                await process_category(session, root, writer, start_time)

    logging.info(f"сохранен: {EXCEL_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
