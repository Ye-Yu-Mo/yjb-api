# 养基宝 Python 工具

一个用于查询养基宝基金收益的命令行工具。

## 功能特性

- 二维码登录
- 自动保存和加载 Token
- 查看账户收益仪表盘
- 搜索基金
- 查看账户列表
- 查看基金持仓
- 查看收益曲线
- 查看系统公告

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

## 命令行参数

```
--login              重新登录
--search KEYWORD     搜索基金
--accounts           列出所有账户
--holdings ID        查看账户持仓
--income-chart       查看收益曲线
--notice             查看系统公告
--debug              显示详细调试信息
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
2. 首次使用需要使用养基宝APP扫码登录
3. 如果 Token 过期，使用 `--login` 重新登录

## API 说明

本工具使用养基宝官方API：
- Base URL: `http://browser-plug-api.yangjibao.com`
- 所有请求需要签名验证

## 许可证

仅供学习和个人使用。
