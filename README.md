# 养基宝 Python 工具

一个用于查询养基宝基金收益的命令行工具。

## 功能特性

- 同时支持老接口和 App 新接口，可通过 `--api` 切换
- 老接口：二维码登录
- 新接口：手机验证码登录
- 自动保存和加载 Token
- 查看账户收益仪表盘
- 搜索基金（老/新接口都支持）
- 查看账户列表
- 查看基金持仓
- 查看收益曲线
- 查看系统公告
- 新接口：基金详情、市场排行、ETF/板块排行、股票穿透持仓、基金分组、持仓行业分析等

## 安装依赖

### 基础依赖（必需）

```bash
pip install requests
```

### 可选依赖（强烈推荐）

安装后可以弹窗显示二维码，扫码更方便：

```bash
pip install qrcode[pil]
```

**说明**：
- macOS/Linux 系统自带 tkinter，无需额外安装
- 如果没有安装 qrcode，程序会提供在线二维码生成链接

## 使用方法

### 0. 测试API连接

如果遇到问题，可以先运行测试脚本：

```bash
python3 test_api.py
```

这会显示详细的API请求和响应信息。

### 1. 首次使用 - 登录（带调试信息）

```bash
python3 yjb_tool.py --login --debug
```

程序会显示二维码链接和详细的调试信息，使用养基宝APP扫描登录。Token会自动保存到 `~/.yjb_token.json`。

### 2. 查看仪表盘（默认）

```bash
python3 yjb_tool.py
```

显示指数行情和收益概览。

### 3. 搜索基金

```bash
python3 yjb_tool.py --search 110011
```

### 4. 查看账户列表

```bash
python3 yjb_tool.py --accounts
```

### 5. 查看账户持仓

```bash
python3 yjb_tool.py --holdings <账户ID>
```

### 6. 查看收益曲线

```bash
python3 yjb_tool.py --income-chart
```

### 7. 查看系统公告

```bash
python3 yjb_tool.py --notice
```

### 8. 查看版本信息

```bash
python3 yjb_tool.py --version-info
```

### 9. 导入持仓

```bash
python3 yjb_tool.py --add-holdings '{"account_id":123,"items":[{"fund_id":1058,"fund_code":"501060","hold_share":100,"hold_cost":1.0}]}'
```

### 10. 删除持仓

```bash
python3 yjb_tool.py --remove-holdings '{"account_id":123,"fund_ids":[1058,21778]}'
```

## 双 API 支持

本工具同时支持两套接口，可通过 `--api` 切换：

```bash
# 老接口（默认，稳定）
python3 yjb_tool.py --api old --accounts

# 新接口 App API
python3 yjb_tool.py --api new --new-user
```

- 老接口：`http://browser-plug-api.yangjibao.com`
- 新接口：`https://app-api.yangjibao.com`

新接口签名算法和 secret 已从解包 IPA 中逆向得到，核心接口均可调用，详见 `API.md`。

## 新接口（App API）命令

### 手机验证码登录

```bash
python3 yjb_tool.py --sms-login 18012345678
```

### 用户信息

```bash
python3 yjb_tool.py --api new --new-user
```

### 账户列表

```bash
python3 yjb_tool.py --api new --new-accounts
```

### 指数行情

```bash
python3 yjb_tool.py --api new --new-index
```

### 搜索基金

```bash
python3 yjb_tool.py --api new --new-search 110011
```

### 基金持仓

```bash
# 使用第一个账户
python3 yjb_tool.py --api new --new-holdings

# 指定账户
python3 yjb_tool.py --api new --new-holdings 18584587
```

### 基金详情/重仓

```bash
python3 yjb_tool.py --api new --new-fund-detail 1058
```

### 市场/ETF/板块排行

```bash
python3 yjb_tool.py --api new --new-market-ranking
python3 yjb_tool.py --api new --new-etf-ranking
python3 yjb_tool.py --api new --new-theme-ranking
```

### 基金分组、自选/持仓简易列表

```bash
python3 yjb_tool.py --api new --new-fund-groups
python3 yjb_tool.py --api new --new-all-hold
```

### 股票穿透持仓

```bash
python3 yjb_tool.py --api new --new-stock-penetrate
```

### 基金历史净值/实时涨幅/估值

```bash
python3 yjb_tool.py --api new --new-fund-nav 1058
python3 yjb_tool.py --api new --new-fund-rate 1058
python3 yjb_tool.py --api new --new-fund-gz 1058
```

### 持仓行业分析

```bash
python3 yjb_tool.py --api new --new-profit-analysis
```

### 基金收益汇总/收益曲线/公告

```bash
python3 yjb_tool.py --api new --new-account-collect
python3 yjb_tool.py --api new --new-income-chart
python3 yjb_tool.py --api new --new-notice
```

### 股票账户/收益/持仓/自选

```bash
python3 yjb_tool.py --api new --new-stock-accounts
python3 yjb_tool.py --api new --new-stock-collect
python3 yjb_tool.py --api new --new-stock-holdings
python3 yjb_tool.py --api new --new-stock-income
python3 yjb_tool.py --api new --new-stock-optional
```

### 基金涨跌分布

```bash
python3 yjb_tool.py --api new --new-fund-distribution
```

## 命令行参数

```
--api {old,new}       选择接口，默认 old
--login               老接口二维码登录
--sms-login PHONE     新接口手机验证码登录
--search KEYWORD      搜索基金（老接口）
--accounts            列出所有账户（老接口）
--holdings ID         查看账户持仓（老接口）
--income-chart        查看收益曲线
--income-data [ID]    查看收益数据
--notice              查看系统公告
--version-info        查看版本信息（老接口）
--add-holdings JSON   导入持仓（老接口）
--remove-holdings JSON 删除持仓（老接口）

# 新接口命令
--new-user            用户信息
--new-accounts        基金账户列表
--new-index           指数行情
--new-search KEYWORD  搜索基金
--new-holdings [ID]   基金持仓
--new-fund-detail ID  基金详情
--new-market-ranking  市场排行
--new-fund-groups     基金分组
--new-stock-penetrate [ID] 股票穿透持仓
--new-all-hold        持仓/自选简易列表
--new-etf-ranking     ETF排行
--new-theme-ranking   板块排行
--new-fund-nav ID     历史净值
--new-fund-rate ID    实时涨幅
--new-fund-gz ID      基金估值
--new-profit-analysis 持仓行业分析
--new-account-collect 基金收益汇总
--new-income-chart [ID] 基金收益曲线
--new-notice [PRODUCT_ID] 公告
--new-stock-accounts  股票账户
--new-stock-collect   股票收益汇总
--new-stock-holdings [ID] 股票持仓
--new-stock-income [ID] 股票收益曲线
--new-stock-optional  股票自选
--new-fund-distribution 基金涨跌分布

--debug               显示详细调试信息
```

## 故障排查

### 问题：获取二维码失败

1. 运行测试脚本查看详细错误：
   ```bash
   python3 test_api.py
   ```

2. 使用调试模式运行：
   ```bash
   python3 yjb_tool.py --login --debug
   ```

3. 检查网络连接是否正常
4. 确认API地址是否可访问：`http://browser-plug-api.yangjibao.com`

### 问题：Token过期

使用 `--login` 重新登录：
```bash
python3 yjb_tool.py --login
```

## 示例输出

### 仪表盘示例

```
============================================================
养基宝仪表盘
============================================================

📈 指数行情:
   🔴 上证指数:   3,234.56    +1.23%
   🔴 沪深300:    4,567.89    +0.98%
   🟢 深证成指:  11,234.56    -0.45%
   🔴 创业板指:   2,345.67    +1.56%

💰 收益概览:
   🔴 当日收益: ¥123.45
   🔴 收益率:   1.23%

============================================================
```

## 注意事项

1. Token 保存在 `~/.yjb_token.json`，请妥善保管
2. 老接口首次使用使用养基宝APP扫码登录：`python3 yjb_tool.py --login`
3. 新接口使用手机验证码登录：`python3 yjb_tool.py --sms-login 手机号`
4. 如果 Token 过期，根据接口选择重新登录
5. 当前新接口核心功能均可调用，老接口仍保留作为 backup，详见 `API.md`

## API 说明

本工具支持两套养基宝 API：
- 老接口：`http://browser-plug-api.yangjibao.com`
- 新接口：`https://app-api.yangjibao.com`
- 所有请求需要签名验证
- 完整接口状态和签名说明见 [API.md](API.md)

## 许可证

仅供学习和个人使用。
