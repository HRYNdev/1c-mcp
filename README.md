# 1C MCP Server

MCP-сервер для подключения Claude к **1С:Предприятие** через стандартный OData REST API.

Работает с любой конфигурацией 1С, где включён OData: **УТ, УНФ, Бухгалтерия, ERP** и другие.

## Что умеет

Просто пишешь Claude на русском — он сам вызывает нужные инструменты:

| Что спросить | Что происходит |
|---|---|
| «Сколько болтов М8 на складе?» | поиск товара → остатки |
| «Покажи заказы ООО Ромашка» | поиск контрагента → заказы |
| «Создай заказ — 10 труб 50мм для ЗАО Промсталь» | поиск контрагента + товара + склада → создание заказа |
| «Топ-3 позиции по стоимости остатка» | остатки + цены → расчёт |

## Инструменты

| Инструмент | Описание |
|---|---|
| `get_warehouses` | список складов (кэш 5 мин) |
| `search_products` | поиск номенклатуры по названию |
| `get_stock` | остатки на складах |
| `get_prices` | актуальные цены |
| `find_counterparty` | поиск контрагентов по названию или ИНН |
| `get_orders` | список заказов покупателей |
| `get_order_details` | состав заказа |
| `create_order` | создание заказа покупателя |

## Требования

- Python 3.10+
- 1С:Предприятие 8.3 с включённым OData (HTTP-сервис)
- Claude Desktop

## Установка

```bash
git clone https://github.com/HRYNdev/1c-mcp.git
cd 1c-mcp
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

Создай `.env` из шаблона:

```bash
copy .env.example .env
```

Заполни `.env`:

```env
ONEC_BASE_URL=http://localhost/your_base/odata/standard.odata
ONEC_LOGIN=admin
ONEC_PASSWORD=your_password
```

## Подключение к Claude Desktop

Добавь в `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "1c-mcp": {
      "command": "C:\\path\\to\\1c-mcp\\.venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\1c-mcp\\server.py"],
      "env": {
        "ONEC_BASE_URL": "http://localhost/your_base/odata/standard.odata",
        "ONEC_LOGIN": "admin",
        "ONEC_PASSWORD": "your_password"
      }
    }
  }
}
```

Путь к конфигу:
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

## Тестирование без реальной 1С

В репозитории есть mock-сервер, который имитирует 1С OData:

```bash
.venv\Scripts\uvicorn mock_server.server:app --port 8181
```

В `.env` укажи:
```env
ONEC_BASE_URL=http://localhost:8181/odata/standard.odata
ONEC_LOGIN=admin
ONEC_PASSWORD=admin
```

Mock содержит тестовые данные: 8 товаров, 3 склада, 4 контрагента, остатки, цены и заказы.

## Как включить OData в 1С

1. Открой конфигуратор → **Администрирование → Публикация на веб-сервере**
2. Включи **OData REST-интерфейс**
3. Отметь объекты (справочники, документы, регистры), которые нужны
4. Опубликуй на локальном веб-сервере (Apache или IIS)

## Структура проекта

```
1c-mcp/
├── server.py          # MCP сервер (8 инструментов)
├── client.py          # HTTP клиент к 1С OData
├── requirements.txt
├── .env.example
└── mock_server/
    └── server.py      # Mock 1С OData для разработки
```

## Адаптация под вашу конфигурацию

Стандартные имена объектов OData могут отличаться в зависимости от конфигурации:

| Конфигурация | Номенклатура | Контрагенты |
|---|---|---|
| Бухгалтерия | `Catalog_Номенклатура` | `Catalog_Контрагенты` |
| УТ 11 | `Catalog_Номенклатура` | `Catalog_Партнеры` |
| УНФ | `Catalog_Номенклатура` | `Catalog_Контрагенты` |

Нужна адаптация под вашу конфигурацию — пишите в issues.

---

*Часть проекта [HomeLab-MCP](https://github.com/HRYNdev/HomeLab-MCP) — коллекции MCP серверов для автоматизации.*
