---
name: etoro
version: 1.1.0
description: 与 eToro API 交互的技能，可读取行情数据、组合与社交功能，并通过程序化方式执行交易。用于查询 eToro 余额、持仓、行情、执行买入/卖出、查看关注列表等操作。触发词：eToro、etoro、eToro 交易、eToro 持仓、eToro 余额、eToro 下单。
homepage: https://api-portal.etoro.com/
metadata: {"openclaw":{"emoji":"ߓ袬"category":"finance","api_base":"https://public-api.etoro.com/api/v1"}}
---

# eToro 公共 API 技能

Base URL: `https://public-api.etoro.com/api/v1`

## 简介

本技能用于以程序化方式操作用户的 eToro 账户，包括执行交易、查询行情与组合等。

## 认证与必需请求头

**密钥（从系统环境变量读取 —— 已配置，不要向用户索要）**

| 环境变量 | 用途 |
|---|---|
| `ETORO_PUBLIC_KEY` | Public API Key（应用级） |
| `ETORO_USER_KEY` | User Key（账户级） |
| `ETORO_ENVIRONMENT` | `real` 或 `demo`（密钥绑定的环境） |

在 shell 中直接用 `$ETORO_PUBLIC_KEY` / `$ETORO_USER_KEY` / `$ETORO_ENVIRONMENT` 展开，无需用户提供。

**请求头（每个请求都必须携带）：**
- `x-request-id`: 每个请求唯一的 UUID
- `x-api-key`: $ETORO_PUBLIC_KEY
- `x-user-key`: $ETORO_USER_KEY

示例：
```bash
curl -X GET "https://public-api.etoro.com/api/v1/watchlists" \
  -H "x-request-id: $(uuidgen)" \
  -H "x-api-key: $ETORO_PUBLIC_KEY" \
  -H "x-user-key: $ETORO_USER_KEY"
```

**环境 → 端点选择规则：**
- `ETORO_ENVIRONMENT=demo` → 使用 `/trading/execution/demo/*` 与 `/trading/info/demo/*`
- `ETORO_ENVIRONMENT=real` → 使用非 demo 端点（`/trading/execution/*`、`/trading/info/portfolio`、`/trading/info/real/pnl`）

## 请求约定
- **以下所有路径均相对于 Base URL**（其已包含 `/api/v1`）。
  例：`GET /watchlists` 表示 `GET https://public-api.etoro.com/api/v1/watchlists`。
- 查询参数放 URL 中，路径参数放 URL 路径中。
- 文档标记为 `array` 的查询参数，用**逗号分隔**发送（如 `instrumentIds=1001,1002`）。
- 分页参数各端点不同：
  - 搜索（Search）：`pageNumber`、`pageSize`
  - 用户搜索与交易历史：`page`、`pageSize`
  - 动态流（Feeds）：`take`、`offset`
  - 自选列表条目：`pageNumber`、`itemsPerPage`
- **请求体区分大小写（重要）：**
  - 交易执行用 **PascalCase** 字段（如 `InstrumentID`、`IsBuy`、`Leverage`）。
  - 平仓请求体用 `InstrumentId`（大写 I、小写 d）。
  - 自选列表条目用 `ItemId`、`ItemType`、`ItemRank`。
  - 动态流发帖请求体用 lower camel（`owner`、`message`、`tags`、`mentions`、`attachments`）。
- 部分响应对相似概念可能使用不同大小写（如 `instrumentId` 与 `InstrumentID`）。提取 ID 时若两者都存在，都要处理。

## 模拟盘 vs 实盘交易

- 测试与模拟交易使用 **demo 执行端点**（路径含 `/demo/`）。
- 实盘交易使用**非 demo 执行端点**。
- 组合与盈亏（Portfolio/PnL）：
  - 模拟盘：`/trading/info/demo/*`
  - 实盘：`/trading/info/portfolio` 与 `/trading/info/real/pnl`
- 确保密钥环境与端点匹配（虚拟 vs 实盘）。每个 User Key 绑定特定环境。

## 使用默认值（重要）

- 无需填写全部参数。例如用户未指定杠杆时，不要在 API 请求中发送该参数。

## 快速上手（模拟盘交易）

1) **用搜索解析 `instrumentId`**。
搜索请求必须带 `fields` 参数。

```bash
curl -X GET "https://public-api.etoro.com/api/v1/market-data/search?internalSymbolFull=BTC&fields=instrumentId,internalSymbolFull,displayname" \
  -H "x-api-key: $ETORO_PUBLIC_KEY" \
  -H "x-user-key: $ETORO_USER_KEY" \
  -H "x-request-id: $(uuidgen)"
```

2) **按金额下模拟盘市价单**（PascalCase 请求体）：
```bash
curl -X POST "https://public-api.etoro.com/api/v1/trading/execution/demo/market-open-orders/by-amount" \
  -H "x-api-key: $ETORO_PUBLIC_KEY" \
  -H "x-user-key: $ETORO_USER_KEY" \
  -H "x-request-id: $(uuidgen)" \
  -H "Content-Type: application/json" \
  -d '{
    "InstrumentID": 100000,
    "IsBuy": true,
    "Leverage": 1,
    "Amount": 100
  }'
```

## 常用 ID

- `instrumentId`: 来自搜索（Search）或工具元数据（Instruments）
- `positionId`: 来自组合端点（Portfolio）
- `orderId`: 来自执行响应或组合端点（Portfolio）
- `marketId`: 用于工具动态流端点（通常在工具元数据/搜索字段中）
- `userId`: 数字型 eToro 用户 ID（响应中常称为 **CID**；通过 People 端点/搜索获取）
- `watchlistId`: 来自自选列表的列表/创建端点
- `subPortfolioId`: 来自代理组合端点（Agent Portfolio，UUID）

## 行情数据（请求）

**搜索工具**
- `GET /market-data/search`
- 必填查询参数：`fields`（逗号分隔的工具字段列表）
- 可选：`searchText`、`pageSize`、`pageNumber`、`sort`
- Search 端点支持按返回字段过滤；精确查找代码时用 `internalSymbolFull` 作查询参数并核对完全匹配。
- 需要 ID 时推荐的最小 `fields`：工具标识符（可能是 `instrumentId` 或 `InstrumentID`）、`internalSymbolFull`、`displayname`（若要用动态流再加 `marketId`）。

**元数据**
- `GET /market-data/instruments`
  过滤器：`instrumentIds`、`exchangeIds`、`stocksIndustryIds`、`instrumentTypeIds`。

**价格与历史**
- `GET /market-data/instruments/rates`
  必填：`instrumentIds`（逗号分隔）。
- `GET /market-data/instruments/history/closing-price`
  返回所有工具的收盘历史价（批量）。
- `GET /market-data/instruments/{instrumentId}/history/candles/{direction}/{interval}/{candlesCount}`
  `direction`: `asc` 或 `desc`。`candlesCount` 最大 1000。
  仅使用受支持的 `interval` 取值（不确定时查文档确认）。

**参考数据**
- `GET /market-data/exchanges`（可选 `exchangeIds`）
- `GET /market-data/instrument-types`
- `GET /market-data/stocks-industries`（可选 `stocksIndustryIds`）

## 交易执行（请求）

> 需要具备相应权限（通常为 **Write**）且环境正确（模拟盘 vs 实盘）的密钥。

### 市价开仓（按金额）

端点：
- `POST /trading/execution/demo/market-open-orders/by-amount`
- `POST /trading/execution/market-open-orders/by-amount`

请求体（PascalCase, JSON）：
- **必填：** `InstrumentID`、`IsBuy`、`Leverage`、`Amount`
- **可选：** `StopLossRate`、`TakeProfitRate`、`IsTslEnabled`、`IsNoStopLoss`、`IsNoTakeProfit`

### 市价开仓（按手数/数量）

端点：
- `POST /trading/execution/demo/market-open-orders/by-units`
- `POST /trading/execution/market-open-orders/by-units`

请求体（PascalCase, JSON）：
- **必填：** `InstrumentID`、`IsBuy`、`Leverage`、`AmountInUnits`
- **可选：** `StopLossRate`、`TakeProfitRate`、`IsTslEnabled`、`IsNoStopLoss`、`IsNoTakeProfit`

### 取消市价开仓订单

端点：
- `DELETE /trading/execution/demo/market-open-orders/{orderId}`
- `DELETE /trading/execution/market-open-orders/{orderId}`

### 市价平仓订单

端点：
- `POST /trading/execution/demo/market-close-orders/positions/{positionId}`
- `POST /trading/execution/market-close-orders/positions/{positionId}`
- `DELETE /trading/execution/demo/market-close-orders/{orderId}`
- `DELETE /trading/execution/market-close-orders/{orderId}`

请求体（JSON）：
- **必填：** `InstrumentId`
- **可选：** `UnitsToDeduct`（数字或 `null`）

部分平仓：设置 `UnitsToDeduct`。
全部平仓：`UnitsToDeduct` 设为 `null`。
必须按 `positionId` 平仓，不能按代码。

### 触价单（限价单）

端点：
- `POST /trading/execution/demo/limit-orders`
- `DELETE /trading/execution/demo/limit-orders/{orderId}`
- `POST /trading/execution/limit-orders`
- `DELETE /trading/execution/limit-orders/{orderId}`

请求体（PascalCase, JSON）：
- **必填：** `InstrumentID`、`IsBuy`、`Leverage`、**`Rate`**，以及 **`Amount` 或 `AmountInUnits` 之一**
- **可选：** `StopLossRate`、`TakeProfitRate`、`IsTslEnabled`、`IsNoStopLoss`、`IsNoTakeProfit`
- **不要发送：** `IsDiscounted`、`CID`

## 交易信息与组合（请求）

- `GET /trading/info/demo/pnl`
- `GET /trading/info/real/pnl`
- `GET /trading/info/demo/portfolio`
- `GET /trading/info/portfolio`
  用于查询 `positionId` 与 `orderId`，配合平仓/撤单流程。
- `GET /trading/info/trade/history`
  必填：`minDate`（YYYY-MM-DD）。可选：`page`、`pageSize`。

## 余额（含多币种账户）

> 查询账户余额优先使用本组端点。`/trading/info/aggregate-portfolio` 只能看到 USD 投资账户（Trading 账户）；EUR/GBP 等 **Cash 货币账户** 余额必须用 `/balances` 系列读取。
> 需要 scope：`money.balance:read`（未授权时返回 `InsufficientPermissions`）。

- `GET /balances` — **聚合余额**（推荐，最简）。返回全部账户及各自货币：
  ```bash
  curl -X GET "https://public-api.etoro.com/api/v1/balances" \
    -H "x-request-id: $(cat /proc/sys/kernel/random/uuid)" \
    -H "x-api-key: $ETORO_PUBLIC_KEY" \
    -H "x-user-key: $ETORO_USER_KEY"
  ```
  返回示例：`{"gcid":..., "totalBalance":3.24, "displayCurrency":"USD", "balances":[{"accountId":"...","accountType":"Cash","balance":2.81,"currency":"EUR","displayBalance":3.24,"displayCurrency":"USD","exchangeRate":1.15253}]}`
- `GET /balances/{accountType}` — 按账户类型查询。**⚠️ accountType 必须小写**：`Cash`、`Trading`、`Crypto`、`Options`；`/balances/Cash` 会返回 404，正确写法 `/balances/cash`。
- `GET /balances/{accountType}/{accountId}` — 查询单个账户余额。
- 可选查询参数：`accountIds`（逗号分隔）、`displayCurrency`（ISO 4217，默认 USD，如 `EUR`）、`includeZeroBalances`（默认 false）、`expand=equityDetails`。
- 历史：`GET /balances/history`（全账户快照）、`GET /balances/{accountType}/history`（按类型历史）。
- Cash 账户流水：`GET /money/accounts/cash/{accountId}/transactions`（分页参数 `pageSize`/`pageToken`）。

## 自选列表（请求）

**用户自选列表**
- `GET /watchlists`
  可选：`itemsPerPageForSingle`、`ensureBuiltinWatchlists`、`addRelatedAssets`。
- `GET /watchlists/{watchlistId}`
  可选：`pageNumber`、`itemsPerPage`。
- `POST /watchlists`
  查询参数：`name`（必填）、`type`、`dynamicQuery`（可选）。（用查询参数，不是 JSON 请求体。）
- `PUT /watchlists/{watchlistId}`
  查询参数：`newName`（必填）。（用查询参数，不是 JSON 请求体。）
- `DELETE /watchlists/{watchlistId}`

**自选列表条目（请求体结构）**

`WatchlistItemDto` 字段：
- `ItemId`（必填，int）
- `ItemType`（必填，string：`Instrument` 或 `Person`）
- `ItemRank`（可选，int）

端点：
- `POST /watchlists/{watchlistId}/items`
- `PUT /watchlists/{watchlistId}/items`
- `DELETE /watchlists/{watchlistId}/items`

请求体示例：
```json
[
  { "ItemId": 12345, "ItemType": "Instrument", "ItemRank": 1 },
  { "ItemId": 67890, "ItemType": "Instrument", "ItemRank": 2 }
]
```

**默认自选列表**
- `POST /watchlists/default-watchlist/selected-items`
- `GET /watchlists/default-watchlists/items`
  可选：`itemsLimit`、`itemsPerPage`。
- `POST /watchlists/newasdefault-watchlist`
  查询参数：`name`（必填）、`type`、`dynamicQuery`（可选）。
- `PUT /watchlists/setUserSelectedUserDefault/{watchlistId}`
- `PUT /watchlists/rank/{watchlistId}`
  查询参数：`newRank`（必填）。

**公开自选列表**
- `GET /watchlists/public/{userId}`
- `GET /watchlists/public/{userId}/{watchlistId}`

## 动态流（Feeds，请求）

**读取动态流**
- `GET /feeds/instrument/{marketId}`
  可选：`requesterUserId`、`take`、`offset`、`badgesExperimentIsEnabled`、`reactionsPageSize`。
- `GET /feeds/user/{userId}`
  可选：`requesterUserId`、`take`、`offset`、`badgesExperimentIsEnabled`、`reactionsPageSize`。

说明：
- `marketId` 与某工具关联（通常在工具元数据/搜索的 `fields` 中可获得）。
- `userId` 是数字型用户标识（CID）。若只有用户名，通过 People 端点查询数字 ID（见下方「用户信息与分析」）。

**发帖**
- `POST /feeds/post`
- 请求体字段（lower camel, JSON）：
  - `owner`（int）
  - `message`（string）
  - `tags`: `{ "tags": [{ "name": "...", "id": "..." }] }`
  - `mentions`: `{ "mentions": [{ "userName": "...", "id": "...", "isDirect": true }] }`
  - `attachments`: 对象数组，含 `url`、`title`、`host`、`description`、`mediaType`，以及可选的 `media`。

最小示例：
```json
{ "message": "Hello eToro feed!" }
```

## 精选列表与推荐（请求）

- `GET /curated-lists`
- `GET /market-recommendations/{itemsCount}`

## 热门投资者（跟随/复制）

- `GET /pi-data/copiers`

## 用户信息与分析（请求）

- `GET /user-info/people`
  可选：`usernames`、`cidList`。
  用于在需要数字 `userId`（动态流/公开自选列表）时映射 **username ↔ CID (userId)**。
- `GET /user-info/people/search`
  必填：`period`。可选：`page`、`pageSize`、`sort`、`popularInvestor`、`gainMax`、`maxDailyRiskScoreMin`、`maxDailyRiskScoreMax`、`maxMonthlyRiskScoreMin`、`maxMonthlyRiskScoreMax`、`weeksSinceRegistrationMin`、`countryId`、`instrumentId`、`instrumentPctMin`、`instrumentPctMax`、`isTestAccount` 及其他过滤器。
- `GET /user-info/people/{username}/gain`
- `GET /user-info/people/{username}/daily-gain`
  必填：`minDate`、`maxDate`、`type`（`Daily` 或 `Period`）。
- `GET /user-info/people/{username}/portfolio/live`
- `GET /user-info/people/{username}/tradeinfo`
  必填：`period`（如 `LastTwoYears`）。

## 代理组合（子组合）

代理组合是独立的子账户，拥有自己的虚拟余额，可通过复制交易让代理独立交易。`investmentAmountInUsd` 从**你的**余额中扣除以复制子组合——仓位按比例镜像（如 $2k 投资 / $10k 虚拟余额 = 20% 仓位比例）。`userToken` 密钥**仅在创建时返回一次**。

- `GET /sub-portfolios` — 列出你的所有代理组合。
- `POST /sub-portfolios` — 创建代理组合。
  必填请求体：`investmentAmountInUsd`、`subPortfolioName`（6–10 字符）、`userTokenName`、`scopeIds`。
  可选：`subPortfolioDescription`、`ipsWhitelist`、`expiresAt`。
- `DELETE /sub-portfolios/{subPortfolioId}` — 永久删除（吊销令牌、停止镜像）。
- `POST /sub-portfolios/{subPortfolioId}/user-tokens` — 创建令牌。
  必填请求体：`userTokenName`、`scopeIds`。可选：`ipsWhitelist`、`expiresAt`。
- `PATCH /sub-portfolios/{subPortfolioId}/user-tokens/{userTokenId}` — 更新令牌（至少一个：`scopeIds`、`ipsWhitelist`、`expiresAt`）。
- `DELETE /sub-portfolios/{subPortfolioId}/user-tokens/{userTokenId}` — 吊销令牌。

Scope ID：200 = real:read、201 = demo:read、202 = real:write、203 = demo:write。

## 响应与数据结构

响应结构与完整示例参考：
- https://api-portal.etoro.com/
- MCP server: `https://api-portal.etoro.com/mcp`
