"""
Mock-сервер 1С OData для разработки и тестирования 1c-mcp.
Имитирует стандартный OData интерфейс 1С:Предприятие 8.3.
Запуск: uvicorn mock_server.server:app --port 8080
"""
from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import uuid
from datetime import datetime
from typing import Optional

app = FastAPI(title="1С OData Mock", version="1.0")
security = HTTPBasic()

MOCK_USER = "admin"
MOCK_PASS = "admin"

# ── Тестовые данные ────────────────────────────────────────────────

WAREHOUSES = [
    {"Ref_Key": "wh-001", "Code": "000001", "Description": "Основной склад", "DeletionMark": False},
    {"Ref_Key": "wh-002", "Code": "000002", "Description": "Склад Москва",   "DeletionMark": False},
    {"Ref_Key": "wh-003", "Code": "000003", "Description": "Склад СПб",      "DeletionMark": False},
]

PRODUCTS = [
    {"Ref_Key": "p-001", "Code": "000001", "Description": "Болт М8х20",       "Артикул": "BM8-20",  "ЕдиницаИзмерения": "шт", "DeletionMark": False},
    {"Ref_Key": "p-002", "Code": "000002", "Description": "Болт М10х30",      "Артикул": "BM10-30", "ЕдиницаИзмерения": "шт", "DeletionMark": False},
    {"Ref_Key": "p-003", "Code": "000003", "Description": "Гайка М8",         "Артикул": "GM8",     "ЕдиницаИзмерения": "шт", "DeletionMark": False},
    {"Ref_Key": "p-004", "Code": "000004", "Description": "Труба 50мм",       "Артикул": "T-50",    "ЕдиницаИзмерения": "м",  "DeletionMark": False},
    {"Ref_Key": "p-005", "Code": "000005", "Description": "Труба 100мм",      "Артикул": "T-100",   "ЕдиницаИзмерения": "м",  "DeletionMark": False},
    {"Ref_Key": "p-006", "Code": "000006", "Description": "Фитинг угловой",   "Артикул": "FU-50",   "ЕдиницаИзмерения": "шт", "DeletionMark": False},
    {"Ref_Key": "p-007", "Code": "000007", "Description": "Шайба М8",         "Артикул": "SM8",     "ЕдиницаИзмерения": "шт", "DeletionMark": False},
    {"Ref_Key": "p-008", "Code": "000008", "Description": "Кабель ВВГ 3х2.5", "Артикул": "K-VVG",   "ЕдиницаИзмерения": "м",  "DeletionMark": False},
]

COUNTERPARTIES = [
    {"Ref_Key": "c-001", "Code": "000001", "Description": "ООО Ромашка",    "ИНН": "7701234567",  "КПП": "770101001", "ЮрФизЛицо": "ЮрЛицо",  "DeletionMark": False},
    {"Ref_Key": "c-002", "Code": "000002", "Description": "ИП Иванов А.С.", "ИНН": "771234567890","КПП": "",          "ЮрФизЛицо": "ФизЛицо", "DeletionMark": False},
    {"Ref_Key": "c-003", "Code": "000003", "Description": "ЗАО Промсталь",  "ИНН": "7700987654",  "КПП": "770101002", "ЮрФизЛицо": "ЮрЛицо",  "DeletionMark": False},
    {"Ref_Key": "c-004", "Code": "000004", "Description": "ООО ТехноСтрой", "ИНН": "7709876543",  "КПП": "770101003", "ЮрФизЛицо": "ЮрЛицо",  "DeletionMark": False},
]

STOCK = [
    {"Номенклатура_Key": "p-001", "Склад_Key": "wh-001", "КоличествоОстаток": 450.0},
    {"Номенклатура_Key": "p-001", "Склад_Key": "wh-002", "КоличествоОстаток": 120.0},
    {"Номенклатура_Key": "p-002", "Склад_Key": "wh-001", "КоличествоОстаток": 280.0},
    {"Номенклатура_Key": "p-003", "Склад_Key": "wh-001", "КоличествоОстаток": 800.0},
    {"Номенклатура_Key": "p-003", "Склад_Key": "wh-002", "КоличествоОстаток": 200.0},
    {"Номенклатура_Key": "p-004", "Склад_Key": "wh-001", "КоличествоОстаток": 75.0},
    {"Номенклатура_Key": "p-004", "Склад_Key": "wh-003", "КоличествоОстаток": 30.0},
    {"Номенклатура_Key": "p-005", "Склад_Key": "wh-001", "КоличествоОстаток": 40.0},
    {"Номенклатура_Key": "p-006", "Склад_Key": "wh-001", "КоличествоОстаток": 150.0},
    {"Номенклатура_Key": "p-007", "Склад_Key": "wh-001", "КоличествоОстаток": 1200.0},
    {"Номенклатура_Key": "p-008", "Склад_Key": "wh-002", "КоличествоОстаток": 500.0},
]

PRICES = [
    {"Номенклатура_Key": "p-001", "Цена": 12.50,  "Валюта": "RUB"},
    {"Номенклатура_Key": "p-002", "Цена": 18.00,  "Валюта": "RUB"},
    {"Номенклатура_Key": "p-003", "Цена": 7.00,   "Валюта": "RUB"},
    {"Номенклатура_Key": "p-004", "Цена": 350.00, "Валюта": "RUB"},
    {"Номенклатура_Key": "p-005", "Цена": 620.00, "Валюта": "RUB"},
    {"Номенклатура_Key": "p-006", "Цена": 85.00,  "Валюта": "RUB"},
    {"Номенклатура_Key": "p-007", "Цена": 4.50,   "Валюта": "RUB"},
    {"Номенклатура_Key": "p-008", "Цена": 95.00,  "Валюта": "RUB"},
]

ORDERS = [
    {
        "Ref_Key": "o-001", "Number": "000001", "Date": "2026-03-01T10:00:00",
        "Контрагент_Key": "c-001", "Контрагент": "ООО Ромашка",
        "Склад_Key": "wh-001", "СтатусЗаказа": "ВРаботе", "Сумма": 5625.0,
        "DeletionMark": False, "Posted": True,
    },
    {
        "Ref_Key": "o-002", "Number": "000002", "Date": "2026-03-05T14:30:00",
        "Контрагент_Key": "c-003", "Контрагент": "ЗАО Промсталь",
        "Склад_Key": "wh-001", "СтатусЗаказа": "ВРаботе", "Сумма": 26250.0,
        "DeletionMark": False, "Posted": True,
    },
    {
        "Ref_Key": "o-003", "Number": "000003", "Date": "2026-03-10T09:15:00",
        "Контрагент_Key": "c-002", "Контрагент": "ИП Иванов А.С.",
        "Склад_Key": "wh-002", "СтатусЗаказа": "Новый", "Сумма": 1800.0,
        "DeletionMark": False, "Posted": False,
    },
]

ORDER_ITEMS: dict[str, list] = {
    "o-001": [{"Номенклатура_Key": "p-001", "Номенклатура": "Болт М8х20",  "Количество": 450.0, "Цена": 12.50, "Сумма": 5625.0}],
    "o-002": [{"Номенклатура_Key": "p-004", "Номенклатура": "Труба 50мм",  "Количество": 75.0,  "Цена": 350.0, "Сумма": 26250.0}],
    "o-003": [{"Номенклатура_Key": "p-002", "Номенклатура": "Болт М10х30", "Количество": 100.0, "Цена": 18.0,  "Сумма": 1800.0}],
}

created_orders: list[dict] = []

# ── Auth ───────────────────────────────────────────────────────────

def check_auth(creds: HTTPBasicCredentials = Depends(security)):
    ok = secrets.compare_digest(creds.username, MOCK_USER) and \
         secrets.compare_digest(creds.password, MOCK_PASS)
    if not ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            headers={"WWW-Authenticate": "Basic"})

# ── Helpers ────────────────────────────────────────────────────────

def _filter_by_description(items: list[dict], filter_str: Optional[str]) -> list[dict]:
    if not filter_str:
        return items
    f = filter_str.lower()
    if "contains" in f and "description" in f:
        parts = f.split("'")
        search = parts[1] if len(parts) >= 2 else ""
        return [i for i in items if search in i.get("Description", "").lower()]
    if "инн eq" in f:
        parts = filter_str.split("'")
        inn = parts[1] if len(parts) >= 2 else ""
        return [i for i in items if i.get("ИНН", "") == inn]
    return items

def product_name(key: str) -> str:
    return next((p["Description"] for p in PRODUCTS if p["Ref_Key"] == key), key)

def warehouse_name(key: str) -> str:
    return next((w["Description"] for w in WAREHOUSES if w["Ref_Key"] == key), key)

# ── Endpoints ──────────────────────────────────────────────────────

@app.get("/odata/standard.odata/Catalog_Склады")
def get_warehouses(
    top: int = Query(100, alias="$top"),
    skip: int = Query(0, alias="$skip"),
    filter_: Optional[str] = Query(None, alias="$filter"),
    _=Depends(check_auth),
):
    items = [w for w in WAREHOUSES if not w["DeletionMark"]]
    items = _filter_by_description(items, filter_)
    return {"value": items[skip: skip + top]}


@app.get("/odata/standard.odata/Catalog_Номенклатура")
def get_products(
    top: int = Query(50, alias="$top"),
    skip: int = Query(0, alias="$skip"),
    filter_: Optional[str] = Query(None, alias="$filter"),
    _=Depends(check_auth),
):
    items = [p for p in PRODUCTS if not p["DeletionMark"]]
    items = _filter_by_description(items, filter_)
    return {"value": items[skip: skip + top]}


@app.get("/odata/standard.odata/Catalog_Контрагенты")
def get_counterparties(
    top: int = Query(20, alias="$top"),
    skip: int = Query(0, alias="$skip"),
    filter_: Optional[str] = Query(None, alias="$filter"),
    _=Depends(check_auth),
):
    items = [c for c in COUNTERPARTIES if not c["DeletionMark"]]
    items = _filter_by_description(items, filter_)
    return {"value": items[skip: skip + top]}


@app.get("/odata/standard.odata/AccumulationRegister_ТоварыНаСкладах/Balance()")
def get_stock(
    filter_: Optional[str] = Query(None, alias="$filter"),
    _=Depends(check_auth),
):
    result = []
    for s in STOCK:
        if s["КоличествоОстаток"] <= 0:
            continue
        if filter_:
            f = filter_.lower()
            if "номенклатура_key" in f:
                key = filter_.split("'")[1] if "'" in filter_ else ""
                if key and s["Номенклатура_Key"] != key:
                    continue
            if "склад_key" in f:
                key = filter_.split("'")[1] if "'" in filter_ else ""
                if key and s["Склад_Key"] != key:
                    continue
        result.append({
            **s,
            "Номенклатура": product_name(s["Номенклатура_Key"]),
            "Склад": warehouse_name(s["Склад_Key"]),
        })
    return {"value": result}


@app.get("/odata/standard.odata/InformationRegister_ЦеныНоменклатуры/SliceLast()")
def get_prices(
    filter_: Optional[str] = Query(None, alias="$filter"),
    _=Depends(check_auth),
):
    result = []
    for pr in PRICES:
        if filter_ and "номенклатура_key" in filter_.lower():
            key = filter_.split("'")[1] if "'" in filter_ else ""
            if key and pr["Номенклатура_Key"] != key:
                continue
        result.append({**pr, "Номенклатура": product_name(pr["Номенклатура_Key"])})
    return {"value": result}


@app.get("/odata/standard.odata/Document_ЗаказПокупателя")
def get_orders(
    top: int = Query(20, alias="$top"),
    skip: int = Query(0, alias="$skip"),
    filter_: Optional[str] = Query(None, alias="$filter"),
    _=Depends(check_auth),
):
    all_orders = [o for o in ORDERS if not o["DeletionMark"]] + created_orders
    filtered = _filter_by_description(all_orders, filter_)
    return {"value": filtered[skip: skip + top]}


@app.get("/odata/standard.odata/Document_ЗаказПокупателя(guid'{order_id}')/Товары")
def get_order_items(order_id: str, _=Depends(check_auth)):
    if order_id in ORDER_ITEMS:
        return {"value": ORDER_ITEMS[order_id]}
    created = next((o for o in created_orders if o["Ref_Key"] == order_id), None)
    if created:
        return {"value": created.get("_items", [])}
    raise HTTPException(404, f"Заказ {order_id} не найден")


@app.post("/odata/standard.odata/Document_ЗаказПокупателя")
def create_order(body: dict, _=Depends(check_auth)):
    new_id = f"o-{uuid.uuid4().hex[:6]}"
    number = f"{100 + len(created_orders) + 4:06d}"
    items = body.get("Товары", [])
    total = sum(i.get("Сумма", i.get("Количество", 0) * i.get("Цена", 0)) for i in items)
    cp_key = body.get("Контрагент_Key", "")
    order = {
        "Ref_Key": new_id,
        "Number": number,
        "Date": datetime.now().isoformat(),
        "Контрагент_Key": cp_key,
        "Контрагент": next((c["Description"] for c in COUNTERPARTIES if c["Ref_Key"] == cp_key), ""),
        "Склад_Key": body.get("Склад_Key", "wh-001"),
        "СтатусЗаказа": "Новый",
        "Сумма": round(total, 2),
        "DeletionMark": False,
        "Posted": False,
        "_items": items,
    }
    created_orders.append(order)
    return {k: v for k, v in order.items() if k != "_items"}


@app.post("/odata/standard.odata/Document_ЗаказПокупателя(guid'{order_id}')/Post()")
def post_order(order_id: str, _=Depends(check_auth)):
    order = next((o for o in created_orders if o["Ref_Key"] == order_id), None)
    if order:
        order["Posted"] = True
        order["СтатусЗаказа"] = "ВРаботе"
    return {}
