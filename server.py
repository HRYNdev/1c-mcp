"""
1С MCP Server — подключает Claude к 1С:Предприятие через OData.
Поддерживает: 1С:УТ, 1С:УНФ, 1С:Бухгалтерия и любую конфигурацию с OData.
"""
from fastmcp import FastMCP
from client import get, post, cached_get
from typing import Optional
import json

mcp = FastMCP(
    "1c-mcp",
    instructions=(
        "MCP сервер для работы с базой 1С:Предприятие. "
        "Используй инструменты для поиска товаров, остатков, цен, "
        "контрагентов и заказов. При создании заказа сначала найди "
        "контрагента и товары через поиск, затем используй их Ref_Key."
    ),
)


# ── 1. Склады ──────────────────────────────────────────────────────

@mcp.tool()
async def get_warehouses() -> dict:
    """Получить список всех складов. Результат кэшируется на 5 минут."""
    return await cached_get(
        "warehouses",
        "/Catalog_Склады",
        {"$filter": "DeletionMark eq false"},
    )


# ── 2. Поиск товаров ───────────────────────────────────────────────

@mcp.tool()
async def search_products(query: str, limit: int = 20) -> dict:
    """
    Поиск товаров/номенклатуры по названию.

    Args:
        query: строка поиска (часть названия, например "болт м8")
        limit: максимум результатов (по умолчанию 20)
    """
    return await get(
        "/Catalog_Номенклатура",
        {
            "$filter": f"contains(tolower(Description), '{query.lower()}') and DeletionMark eq false",
            "$top": limit,
            "$select": "Ref_Key,Code,Description,Артикул,ЕдиницаИзмерения",
        },
    )


# ── 3. Остатки на складах ──────────────────────────────────────────

@mcp.tool()
async def get_stock(
    product_key: Optional[str] = None,
    warehouse_key: Optional[str] = None,
) -> dict:
    """
    Получить остатки товаров на складах.

    Args:
        product_key: Ref_Key товара (если нужен конкретный товар)
        warehouse_key: Ref_Key склада (если нужен конкретный склад)

    Примеры вопросов:
        "Сколько болтов М8 на складе?" → search_products("болт м8") → get_stock(product_key=...)
        "Что есть на складе Москва?" → get_warehouses() → get_stock(warehouse_key=...)
    """
    filters = []
    if product_key:
        filters.append(f"Номенклатура_Key eq guid'{product_key}'")
    if warehouse_key:
        filters.append(f"Склад_Key eq guid'{warehouse_key}'")

    params: dict = {}
    if filters:
        params["$filter"] = " and ".join(filters)

    return await get(
        "/AccumulationRegister_ТоварыНаСкладах/Balance()",
        params,
    )


# ── 4. Цены ────────────────────────────────────────────────────────

@mcp.tool()
async def get_prices(product_key: Optional[str] = None) -> dict:
    """
    Получить актуальные цены номенклатуры.

    Args:
        product_key: Ref_Key товара (если None — вернёт все цены)
    """
    params: dict = {}
    if product_key:
        params["$filter"] = f"Номенклатура_Key eq guid'{product_key}'"

    return await get("/InformationRegister_ЦеныНоменклатуры/SliceLast()", params)


# ── 5. Поиск контрагентов ──────────────────────────────────────────

@mcp.tool()
async def find_counterparty(query: str = "", inn: str = "", limit: int = 10) -> dict:
    """
    Поиск контрагентов по названию или ИНН.

    Args:
        query: часть названия компании (например "ромашка")
        inn:   ИНН контрагента (точное совпадение)
        limit: максимум результатов
    """
    if inn:
        filter_str = f"ИНН eq '{inn}' and DeletionMark eq false"
    elif query:
        filter_str = f"contains(tolower(Description), '{query.lower()}') and DeletionMark eq false"
    else:
        filter_str = "DeletionMark eq false"

    return await get(
        "/Catalog_Контрагенты",
        {
            "$filter": filter_str,
            "$top": limit,
            "$select": "Ref_Key,Code,Description,ИНН,КПП,ЮрФизЛицо",
        },
    )


# ── 6. Заказы покупателей ─────────────────────────────────────────

@mcp.tool()
async def get_orders(
    counterparty_key: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
) -> dict:
    """
    Получить список заказов покупателей.

    Args:
        counterparty_key: Ref_Key контрагента для фильтрации
        status: статус заказа — "Новый", "ВРаботе", "Закрыт"
        limit: максимум заказов
    """
    filters = ["DeletionMark eq false"]
    if counterparty_key:
        filters.append(f"Контрагент_Key eq guid'{counterparty_key}'")
    if status:
        filters.append(f"СтатусЗаказа eq '{status}'")

    return await get(
        "/Document_ЗаказПокупателя",
        {
            "$filter": " and ".join(filters),
            "$top": limit,
            "$orderby": "Date desc",
            "$select": "Ref_Key,Number,Date,Контрагент,Склад_Key,СтатусЗаказа,Сумма,Posted",
        },
    )


# ── 7. Состав заказа ──────────────────────────────────────────────

@mcp.tool()
async def get_order_details(order_key: str) -> dict:
    """
    Получить подробный состав заказа: список товаров, количество, цены.

    Args:
        order_key: Ref_Key заказа (из get_orders)
    """
    return await get(f"/Document_ЗаказПокупателя(guid'{order_key}')/Товары")


# ── 8. Создать заказ ──────────────────────────────────────────────

@mcp.tool()
async def create_order(
    counterparty_key: str,
    items_json: str,
    warehouse_key: str = "wh-001",
) -> dict:
    """
    Создать заказ покупателя в 1С.

    Args:
        counterparty_key: Ref_Key контрагента (из find_counterparty)
        warehouse_key:    Ref_Key склада (из get_warehouses)
        items_json: JSON-строка со списком позиций, например:
            '[{"product_key": "p-001", "quantity": 10, "price": 12.50}]'
            product_key — Ref_Key товара из search_products
            quantity    — количество
            price       — цена за единицу

    Перед вызовом обязательно:
        1. Найди контрагента через find_counterparty
        2. Найди товары через search_products
        3. Уточни склад через get_warehouses
    """
    items = json.loads(items_json)
    body_items = []
    for item in items:
        qty   = float(item["quantity"])
        price = float(item["price"])
        body_items.append({
            "Номенклатура_Key": item["product_key"],
            "Количество": qty,
            "Цена": price,
            "Сумма": round(qty * price, 2),
        })

    return await post(
        "/Document_ЗаказПокупателя",
        {
            "Контрагент_Key": counterparty_key,
            "Склад_Key": warehouse_key,
            "Товары": body_items,
        },
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
