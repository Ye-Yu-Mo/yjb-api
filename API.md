# 养基宝 API 文档

本文档整理自：

- 现有 Python 工具 `yjb_tool.py`
- 浏览器插件 `yjb_fund-2.0.0.xpi`
- App 抓包 `Raw_08-28-2026-20-48-20.folder`
- App 包 `养基宝.app` 中可提取的字符串

## 1. 两套 API

| 名称 | Base URL | 来源 | 状态 |
|---|---|---|---|
| 老接口 | `http://browser-plug-api.yangjibao.com` | 浏览器插件 | ✅ 稳定可用 |
| 新接口 | `https://app-api.yangjibao.com` | iOS App | 🟡 部分可用，部分需要 App secret |

命令行通过 `--api old|new` 切换，默认 `old`。

## 2. 认证方式

Token 统一保存在 `~/.yjb_token.json`：

```json
{
  "token": "your-token",
  "timestamp": 1700000000
}
```

请求头差异：

| 接口 | Authorization 示例 |
|---|---|
| 老接口 | `Authorization: <token>` |
| 新接口 | `Authorization: ios:<token>` |

## 3. 签名算法

当前已知的老接口/插件签名：

```text
sign_str = API路径 + token + 时间戳 + SECRET
Request-Sign = md5(sign_str)
```

示例：

```text
GET /users/v1/account
token = a29c...
timestamp = 1787921144
secret = YxmKSrQR4uoJ5lOoWIhcbd7SlUEh9OOc

sign_str = /users/v1/accounta29c...1787921144YxmKSrQR4uoJ5lOoWIhcbd7SlUEh9OOc
Request-Sign = md5(sign_str)
```

注意：

- 签名时只取路径部分，不带 query。
- 新接口部分接口会严格校验签名，目前旧 secret 在这些接口上返回 `401 非法请求`。
- App 包当前是加密状态（`cryptid=1`），暂时无法直接读取 App 端 secret。
- 等拿到脱壳后的 App 后，需要确认新接口 secret/算法是否变化。

## 4. 老接口端点（browser-plug-api）

| 方法 | 路径 | 说明 | CLI |
|---|---|---|---|
| GET | `/qr_code` | 获取登录二维码 | `--login` |
| GET | `/qr_code_state/{id}` | 轮询扫码状态 | `--login` 内部 |
| GET | `/user_account` | 账户列表 | `--accounts` |
| GET | `/account_collect` | 收益汇总 | 仪表盘 |
| GET | `/income_data?account_id={id}` | 单账户收益 | `--income-data ID` |
| GET | `/income_data?collect=true` | 汇总收益 | `--income-data` |
| GET | `/income_line_data?...` | 收益曲线 | `--income-chart` |
| GET | `/fund_hold?account_id={id}` | 基金持仓 | `--holdings ID` |
| POST | `/fund_hold` | 导入/新增持仓 | `--add-holdings` |
| DELETE | `/remove_fund_hold?...` | 删除持仓 | `--remove-holdings` |
| GET | `/index_data` | 指数行情 | 仪表盘 |
| GET | `/notice` | 系统公告 | `--notice` |
| GET | `/version_info` | 版本信息 | `--version-info` |
| GET | `/search_fund?keyword=` | 搜索基金 | `--search` |

## 5. 新接口端点（app-api）

### 5.1 登录/用户

| 方法 | 路径 | 说明 | 当前状态 |
|---|---|---|---|
| POST | `/send_code` | 发送验证码 | ✅ 可用 |
| POST | `/login` | 手机号+验证码登录 | ✅ 可用 |
| GET | `/users/v1/account` | 当前用户信息 | ✅ 可用 |
| GET | `/users/v1/user-account` | 基金账户列表 | ✅ 可用 |
| GET | `/users/v1/fund-group` | 基金分组 | ✅ 可用 |

### 5.2 行情/排行

| 方法 | 路径 | 说明 | 当前状态 |
|---|---|---|---|
| GET | `/market/v1/quote/index-data` | 指数行情 | ✅ 可用 |
| GET | `/market/v1/market-ranking/list` | 市场排行 | ✅ 可用 |
| GET | `/market/v1/market-ranking/etf-ranking` | ETF 排行 | ✅ 可用 |
| GET | `/market/v1/market-ranking/theme-ranking` | 板块排行 | ✅ 可用 |
| GET | `/fund_source_list` | 基金来源列表 | ✅ 可用 |
| GET | `/fund_up_down_distribution` | 涨跌分布 | ⏳ 需要新 secret |
| GET | `/market_buy_ranking` | 买入排行 | ⏳ 需要新 secret |

### 5.3 基金

| 方法 | 路径 | 说明 | 当前状态 |
|---|---|---|---|
| POST | `/content/v1/search/fund` | 搜索基金 | ✅ 可用 |
| GET | `/market/v1/fund/overview` | 基金概览 | ✅ 可用 |
| GET | `/users/v1/fund/detail` | 基金用户详情 | ✅ 可用 |
| POST | `/market/v1/fund/batch` | 批量基金信息 | ✅ 可用 |
| GET | `/position/v1/static/fund-accounts/{id}/funds` | 基金持仓 | ✅ 可用 |
| POST | `/market/v1/fund/relation-and-rank` | 关联/排名 | ✅ 可用 |
| GET | `/position/v1/static/fund/hold-stock` | 重仓股 | ✅ 可用 |
| GET | `/market/v1/fund/fund-stock-industry` | 基金行业持仓 | ✅ 可用 |
| GET | `/market/v1/fund-nav/fund-history-nav` | 历史净值 | ✅ 可用 |
| GET | `/market/v1/fund/increase-rate` | 实时涨幅 | ✅ 可用 |
| GET | `/market/v1/fund/gz-data` | 基金估值 | ✅ 可用 |
| GET | `/position/v1/user/funds/all-hold/simple` | 全部持仓简易列表 | ✅ 可用 |
| GET | `/position/v1/user/funds/all-optional/simple` | 全部自选简易列表 | ✅ 可用 |
| GET | `/account_collect` | 收益汇总 | ⏳ 需要新 secret |
| GET | `/income_line_data` | 收益曲线 | ⏳ 需要新 secret |
| GET | `/inner_notice` | 公告 | ⏳ 需要新 secret |

### 5.4 股票

| 方法 | 路径 | 说明 | 当前状态 |
|---|---|---|---|
| GET | `/position/v1/penetrate/hold/stock-overview` | 股票穿透汇总 | ✅ 可用 |
| GET | `/position/v1/penetrate/hold/accounts/{id}/stocks` | 股票穿透明细 | ✅ 可用 |
| GET | `/position/v1/profit-analysis/position-sector` | 持仓行业分析 | ✅ 可用 |
| GET | `/stock_account` | 股票账户 | ⏳ 需要新 secret |
| GET | `/stock_account_collect` | 股票收益汇总 | ⏳ 需要新 secret |
| GET | `/stock_hold` | 股票持仓 | ⏳ 需要新 secret |
| GET | `/stock_income_line_data` | 股票收益曲线 | ⏳ 需要新 secret |
| GET | `/stock_optional` | 股票自选 | ⏳ 需要新 secret |

### 5.5 自选/达人（部分可用）

| 方法 | 路径 | 说明 | 当前状态 |
|---|---|---|---|
| GET | `/users/v1/optional/talent/group/group-list` | 达人分组 | ✅ 可用 |
| GET | `/users/v1/optional/talent/list-relation` | 达人列表 | ✅ 可用 |
| GET | `/users/v1/optional/subject/group/group-list` | 题材分组 | ✅ 可用 |
| GET | `/users/v1/optional/subject/list` | 题材列表 | ✅ 可用 |
| GET | `/users/v1/optional/subject/header/dates` | 题材日期 | ✅ 可用 |
| POST | `/users/v1/optional/talent/operation/batch-add-talent-to-group` | 批量添加达人 | ✅ 可用 |

### 5.6 从 App 中额外发现、尚未全部接入的接口

App 包里还能提取到大量接口，例如：

- 搜索：`/content/v1/search/composite`、`/content/v1/search/talent`、`/content/v1/search/sector`
- 基金：`/market/v1/fund/batch/paginated`、`/market/v1/us-fund/fund-list`、`/market/v1/us-fund/index-list`
- 持仓管理：`/fund_hold_detail`、`/remove_account_all_fund`、`/fund_hold_sort_top`
- 自选管理：`/users/v1/optional/talent/group/create`、`/users/v1/optional/talent/group/delete`、`/users/v1/optional/talent/operation/move-to-group`
- 用户/客服：`/users/v1/customer-service-chats/identity`、`/users/v1/message/read`
- 股票：`/stock/v1/index-search/search`、`/stock/v1/relation-index/query-batch`、`/stock/v1/relation-index/default-list`

完整列表可参考 `/tmp/yjb_app_endpoints.txt`（当前环境临时文件，后续可整理进仓库）。

## 6. CLI 对应关系

| CLI | 接口 | 说明 |
|---|---|---|
| `--sms-login PHONE` | `POST /send_code` + `POST /login` | 新接口登录 |
| `--api new --new-user` | `GET /users/v1/account` | 用户信息 |
| `--api new --new-accounts` | `GET /users/v1/user-account` | 账户列表 |
| `--api new --new-index` | `GET /market/v1/quote/index-data` | 指数行情 |
| `--api new --new-search KEYWORD` | `POST /content/v1/search/fund` | 搜索基金 |
| `--api new --new-holdings [ID]` | `GET /position/v1/static/fund-accounts/{id}/funds` + `POST /market/v1/fund/batch` | 基金持仓 |
| `--api new --new-fund-detail ID` | 多个基金详情接口 | 基金详情 |
| `--api new --new-stock-penetrate [ID]` | 股票穿透接口 | 股票穿透 |
| `--api new --new-market-ranking` | `GET /market/v1/market-ranking/list` | 市场排行 |
| `--api new --new-etf-ranking` | `GET /market/v1/market-ranking/etf-ranking` | ETF 排行 |
| `--api new --new-theme-ranking` | `GET /market/v1/market-ranking/theme-ranking` | 板块排行 |

## 7. 待办

- [ ] 获取脱壳后的 App 可执行文件
- [ ] 逆向确认新接口签名 secret/算法
- [ ] 接入严格验签接口：`/account_collect`、`/income_line_data`、`/inner_notice`、`/stock_*`
- [ ] 将 App 中发现的更多接口逐步加入 CLI
- [ ] 整理完整接口清单到仓库（如 `docs/endpoints.json`）
