#!/usr/bin/env python3
"""
养基宝命令行工具
"""
import argparse
import hashlib
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import requests
except ImportError:
    print("错误：缺少 requests 库")
    print("安装：pip install requests")
    sys.exit(1)

# 常量
# 老接口：浏览器插件接口，当前默认使用，稳定可用
OLD_API_BASE = "http://browser-plug-api.yangjibao.com"
# 新接口：App 接口，部分接口需要 App 端 secret；目前先用同一套签名，能通的先通
NEW_API_BASE = "https://app-api.yangjibao.com"
# 默认 API，保留老接口作为 backup
API_BASE = OLD_API_BASE
SECRET = "YxmKSrQR4uoJ5lOoWIhcbd7SlUEh9OOc"
# 新接口 secret 暂用同一个，等解包后如果不同再替换
NEW_SECRET = SECRET
TOKEN_FILE = Path.home() / ".yjb_token.json"


# Token 管理
def load_token() -> Optional[str]:
    """从文件加载 token"""
    if not TOKEN_FILE.exists():
        return None
    try:
        with open(TOKEN_FILE, 'r') as f:
            data = json.load(f)
            return data.get('token')
    except Exception as e:
        print(f"警告：读取 token 失败: {e}")
        return None


def save_token(token: str):
    """保存 token 到文件"""
    try:
        with open(TOKEN_FILE, 'w') as f:
            json.dump({
                'token': token,
                'timestamp': int(time.time())
            }, f)
        os.chmod(TOKEN_FILE, 0o600)  # 只有所有者可读写
        print(f"Token 已保存到 {TOKEN_FILE}")
    except Exception as e:
        print(f"错误：保存 token 失败: {e}")


# API 签名
def generate_sign(path: str, token: str, timestamp: int, secret: str = SECRET) -> str:
    """生成 API 签名"""
    pathname = ""  # API base 的路径部分，这里是空字符串
    token = token or ""

    # 如果 path 包含查询参数，签名时只用路径部分
    sign_path = path.split('?')[0] if '?' in path else path

    sign_str = pathname + sign_path + token + str(timestamp) + secret
    return hashlib.md5(sign_str.encode()).hexdigest()


# HTTP 客户端
class YJBClient:
    """养基宝 API 客户端"""

    def __init__(self, token: Optional[str] = None, debug: bool = False, api: str = "old"):
        self.token = token or ""
        self.debug = debug
        self.api = api
        self.base = OLD_API_BASE if api == "old" else NEW_API_BASE
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })

    def request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """发送 API 请求"""
        url = self.base + path
        timestamp = int(time.time())
        secret = SECRET if self.api == "old" else NEW_SECRET
        sign = generate_sign(path, self.token, timestamp, secret)

        # App 新接口的 Authorization 是 ios:token，老接口是纯 token
        auth_value = f"ios:{self.token}" if self.api == "new" else self.token
        headers = {
            'Request-Time': str(timestamp),
            'Request-Sign': sign,
            'Authorization': auth_value
        }

        # 新接口尽量贴近 App 的请求头，降低被风控的概率
        if self.api == "new":
            headers.update({
                'Accept': '*/*',
                'Accept-Language': 'zh-Hans-CN;q=1.0, en-CN;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'User-Agent': 'YJB/2.0.13 (com.xiaoduotou.yjb; build:975; iOS 26.5.0) Alamofire/5.10.2 iPad8,6',
                'Cookie': 'cna=1c1bb34ac9014f8ab07e6e9943d98cb9',
            })

        if self.debug:
            print(f"\n[DEBUG] {method} {path}")
            print(f"[DEBUG] Headers: {headers}")

        try:
            resp = self.session.request(method, url, headers=headers, timeout=30, **kwargs)

            if self.debug:
                print(f"[DEBUG] Status: {resp.status_code}")
                print(f"[DEBUG] Response: {resp.text[:200]}")

            if resp.status_code == 429:
                raise Exception("请求频繁，请稍后再试")
            elif resp.status_code == 408:
                raise Exception("请求超时")
            elif resp.status_code == 401:
                raise Exception("未授权，请重新登录")
            elif resp.status_code != 200:
                raise Exception(f"服务请求异常 code: {resp.status_code}")

            data = resp.json()
            if data.get('code') != 200:
                raise Exception(data.get('message', '未知错误'))

            return data.get('data', {})

        except requests.exceptions.RequestException as e:
            raise Exception(f"网络错误: {e}")

    def get(self, path: str, **kwargs) -> Dict[str, Any]:
        """GET 请求"""
        return self.request('GET', path, **kwargs)

    def post(self, path: str, **kwargs) -> Dict[str, Any]:
        """POST 请求"""
        return self.request('POST', path, **kwargs)


# 二维码登录
def qrcode_login(debug: bool = False) -> str:
    """二维码登录"""
    client = YJBClient(debug=debug)

    print("正在获取登录二维码...")
    try:
        qr_data = client.get('/qr_code')
    except Exception as e:
        print(f"错误：获取二维码失败: {e}")
        sys.exit(1)

    qr_id = qr_data.get('id')
    qr_url = qr_data.get('url')

    if not qr_id or not qr_url:
        print("错误：二维码数据格式错误")
        sys.exit(1)

    # 检测依赖
    has_qrcode = False
    has_gui = False

    try:
        import qrcode
        has_qrcode = True
        try:
            from PIL import Image
            import tkinter as tk
            has_gui = True
        except ImportError:
            pass
    except ImportError:
        pass

    # 显示二维码
    root = None

    # 优先在终端显示
    if has_qrcode:
        try:
            import qrcode
            qr = qrcode.QRCode()
            qr.add_data(qr_url)
            qr.make(fit=True)

            print("\n请使用养基宝 APP 扫描二维码登录：\n")
            qr.print_ascii(invert=True)
            print()

        except Exception as e:
            if debug:
                print(f"[DEBUG] 终端显示失败: {e}")
            # 降级到链接
            print(f"\n请访问以下链接查看二维码：")
            print(f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={qr_url}")
            print(f"\n或直接扫描此链接：{qr_url}\n")
    else:
        # 没有 qrcode 库，打印链接
        print(f"\n请访问以下链接查看二维码：")
        print(f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={qr_url}")
        print(f"\n或直接扫描此链接：{qr_url}\n")

    # 轮询扫码状态
    print("等待扫码...")
    timeout = 120
    interval = 3
    elapsed = 0
    retry_count = 0
    max_retries = 3

    while elapsed < timeout:
        time.sleep(interval)
        elapsed += interval

        try:
            state_data = client.get(f'/qr_code_state/{qr_id}')
            state = state_data.get('state')
            retry_count = 0  # 重置重试计数

            # state: "1" = 等待扫码, 2 = 扫码成功
            if state == 2 or state == '2':
                token = state_data.get('token')
                if token:
                    print("✅ 登录成功！")
                    save_token(token)
                    return token
                else:
                    print("错误：未获取到 token")
                    sys.exit(1)
            elif state == "1":
                # 等待扫码，继续轮询
                pass
            else:
                # 未知状态
                if debug:
                    print(f"[DEBUG] 未知状态: {state}")

        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                print(f"网络错误次数过多: {e}")
                sys.exit(1)
            else:
                print(f"网络异常，正在重试... ({retry_count}/{max_retries})")
                if debug:
                    print(f"[DEBUG] 轮询错误: {e}")

    print("登录超时，请重试")
    sys.exit(1)


# 新接口手机验证码登录
def sms_login(phone: str, debug: bool = False) -> str:
    """App 新接口手机验证码登录"""
    # 登录前 App 会先生成一个设备标识作为临时 token
    device_id = str(uuid.uuid4()).upper()
    client = YJBClient(token=device_id, api="new", debug=debug)

    print(f"正在向 {phone} 发送验证码...")
    try:
        client.post('/send_code', json={"phone": phone})
    except Exception as e:
        print(f"错误：发送验证码失败: {e}")
        sys.exit(1)

    code = input("请输入收到的验证码: ").strip()
    if not code:
        print("错误：验证码不能为空")
        sys.exit(1)

    print("正在登录...")
    try:
        data = client.post('/login', json={
            "phone": phone,
            "mode": "phone",
            "verify_code": code,
            "invite_code": "",
            "is_band_wechat": 1,
        })
        token = data.get('token')
        if not token:
            print("错误：登录成功但未获取到 token")
            sys.exit(1)
        print("✅ 登录成功！")
        save_token(token)
        return token
    except Exception as e:
        print(f"错误：登录失败: {e}")
        sys.exit(1)


# 业务功能
def show_dashboard(client: YJBClient):
    """显示仪表盘"""
    print("=" * 60)
    print("📊 养基宝仪表盘")
    print("=" * 60)

    # 获取指数数据
    try:
        index_data = client.get('/index_data')
        print("\n📈 指数行情:")

        index_map = {
            '1.000001': '上证指数',
            '1.000300': '沪深300',
            '0.399001': '深证成指',
            '0.399006': '创业板指'
        }

        for code, name in index_map.items():
            if code in index_data:
                item = index_data[code]
                price = item.get('v', 'N/A')  # 'v' 是价格字段
                dir_val = item.get('dir', '0')
                try:
                    dir_float = float(dir_val)
                    icon = "🔴" if dir_float > 0 else "🟢" if dir_float < 0 else "⚪"
                    dir_str = f"{dir_float:+.2f}%"
                except:
                    icon = "⚪"
                    dir_str = "N/A"

                print(f"   {icon} {name:8s}  {price:>10s}    {dir_str}")

    except Exception as e:
        print(f"获取指数数据失败: {e}")

    # 获取收益数据
    try:
        account_data = client.get('/account_collect')
        print("\n💰 收益概览:")

        today_income = account_data.get('today_income', 0)
        today_rate = account_data.get('today_income_rate', 0)

        try:
            income_float = float(today_income)
            rate_float = float(today_rate)
            income_icon = "🔴" if income_float > 0 else "🟢" if income_float < 0 else "⚪"

            print(f"   {income_icon} 当日收益: ¥{income_float:.2f}")
            print(f"   {income_icon} 收益率:   {rate_float:+.2f}%")
        except:
            print(f"   当日收益: {today_income}")
            print(f"   收益率:   {today_rate}")

    except Exception as e:
        print(f"获取收益数据失败: {e}")

    print("\n" + "=" * 60)


def search_fund(client: YJBClient, keyword: str):
    """搜索基金"""
    print(f"\n🔍 搜索基金: {keyword}")
    print("-" * 60)

    try:
        funds = client.get(f'/search_fund?keyword={keyword}')

        if not funds:
            print("未找到相关基金")
            return

        for fund in funds:
            code = fund.get('code', 'N/A')
            name = fund.get('name', 'N/A')
            nav = fund.get('nav', 'N/A')
            rate = fund.get('day_growth_rate', 'N/A')

            print(f"{code:8s}  {name:30s}  净值: {nav:>8s}  涨跌: {rate:>8s}")

    except Exception as e:
        print(f"搜索失败: {e}")


def list_accounts(client: YJBClient):
    """列出账户"""
    print("\n📋 账户列表")
    print("-" * 60)

    try:
        # 获取账户列表（基本信息）
        user_data = client.get('/user_account')
        accounts = user_data.get('list', [])

        if not accounts:
            print("暂无账户")
            return

        # 获取账户收益数据
        collect_data = client.get('/account_collect')
        account_data = collect_data.get('account_data', [])

        # 构建 account_id -> 收益数据的映射
        income_map = {acc['account_id']: acc for acc in account_data}

        for acc in accounts:
            acc_id = acc.get('id', 'N/A')
            title = acc.get('title', 'N/A')
            count = acc.get('count', 0)

            # 从收益数据中获取
            income_data = income_map.get(acc_id, {})
            income = income_data.get('today_income', 0)
            rate = income_data.get('today_income_rate', 0)

            try:
                income_float = float(income)
                rate_float = float(rate)
                print(f"ID: {acc_id:<10}  {title:20s}  持仓: {count:2d}  收益: ¥{income_float:>8.2f}  {rate_float:+.2f}%")
            except:
                print(f"ID: {acc_id:<10}  {title:20s}  持仓: {count:2d}  收益: {income}  {rate}")

    except Exception as e:
        print(f"获取账户列表失败: {e}")


def show_holdings(client: YJBClient, account_id: str):
    """显示持仓"""
    print(f"\n💼 账户持仓 (ID: {account_id})")
    print("-" * 100)

    try:
        holdings = client.get(f'/fund_hold?account_id={account_id}')

        if not holdings:
            print("暂无持仓")
            return

        print(f"{'代码':<10s} {'名称':<25s} {'持有份额':<10s} {'当前净值':<10s} {'预估净值':<10s} {'预估涨跌':<10s} {'收益':<10s}")
        print("-" * 100)

        for holding in holdings:
            code = holding.get('code', 'N/A')
            name = holding.get('short_name', 'N/A')
            shares = str(holding.get('hold_share', 'N/A'))
            nav = str(holding.get('last_net', 'N/A'))
            income = str(holding.get('hold_earn', 'N/A'))

            # 预估净值信息（智能选择数据源）
            nv_info = holding.get('nv_info', {})

            # 优先级：gsz（实时估算） > vgsz（预估） > zsgz（昨日估算）
            vgsz = nv_info.get('gsz') or nv_info.get('vgsz') or nv_info.get('zsgz') or 'N/A'
            vgszzl = nv_info.get('gszzl') or nv_info.get('vgszzl') or nv_info.get('zsgzzl') or 'N/A'

            # 格式化预估涨跌幅
            if vgszzl != 'N/A' and vgszzl != '':
                try:
                    vgszzl_float = float(vgszzl)
                    vgszzl = f"{vgszzl_float:+.2f}%"
                except:
                    pass

            print(f"{code:<10s} {name:<25s} {shares:<10s} {nav:<10s} {vgsz:<10s} {vgszzl:<10s} {income:<10s}")

    except Exception as e:
        print(f"获取持仓失败: {e}")


def show_income_chart(client: YJBClient):
    """显示收益曲线"""
    print("\n📈 收益曲线")
    print("-" * 60)

    try:
        data = client.get('/income_line_data?collect=true&date_type=day')
        collect = data.get('collect', {})
        chart_data = collect.get('line_list', [])
        day = collect.get('day', 'N/A')

        if not chart_data:
            print("暂无数据")
            return

        print(f"日期: {day}")
        print(f"\n{'时间':<12s} {'收益率(%)':<12s}")
        print("-" * 60)

        # 只显示每小时的数据（每60条取一条）
        for i, item in enumerate(chart_data):
            if i % 60 == 0 or i == len(chart_data) - 1:
                time_str = item.get('time', 'N/A')
                rate = item.get('rate', 0)
                print(f"{time_str:<12s} {rate:<12}")

    except Exception as e:
        print(f"获取收益曲线失败: {e}")


def show_notice(client: YJBClient):
    """显示公告"""
    print("\n📢 系统公告")
    print("-" * 60)

    try:
        notices = client.get('/notice')

        if not notices:
            print("暂无公告")
            return

        for notice in notices:
            title = notice.get('title', 'N/A')
            content = notice.get('content', 'N/A')
            time_str = notice.get('create_time', 'N/A')

            print(f"\n标题: {title}")
            print(f"时间: {time_str}")
            print(f"内容: {content}")
            print("-" * 60)

    except Exception as e:
        print(f"获取公告失败: {e}")


def show_income_data(client: YJBClient, account_id: Optional[str] = None):
    """显示收益数据"""
    if account_id:
        print(f"\n💰 账户收益数据 (ID: {account_id})")
    else:
        print("\n💰 汇总收益数据")
    print("-" * 60)

    try:
        if account_id:
            data = client.get(f'/income_data?account_id={account_id}')
        else:
            data = client.get('/income_data?collect=true')

        # API 返回的是数字，不是字典
        if isinstance(data, (int, float)):
            print(f"累计收益: ¥{data:.2f}")
        else:
            # 如果是字典，尝试提取字段
            today_income = data.get('today_income', 'N/A')
            today_rate = data.get('today_income_rate', 'N/A')
            total_income = data.get('total_income', 'N/A')
            total_rate = data.get('total_income_rate', 'N/A')

            print(f"当日收益:   {today_income}")
            print(f"当日收益率: {today_rate}")
            print(f"累计收益:   {total_income}")
            print(f"累计收益率: {total_rate}")

    except Exception as e:
        print(f"获取收益数据失败: {e}")


# ========== 新接口（app-api）功能 ==========
def show_new_user(client: YJBClient):
    """新接口：当前用户信息"""
    print("\n👤 用户信息")
    print("-" * 60)
    try:
        data = client.get('/users/v1/account')
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"获取用户信息失败: {e}")


def show_new_accounts(client: YJBClient):
    """新接口：基金账户列表"""
    print("\n📋 新接口账户列表")
    print("-" * 60)
    try:
        data = client.get('/users/v1/user-account')
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"获取账户列表失败: {e}")


def show_new_index(client: YJBClient):
    """新接口：指数行情"""
    print("\n📈 新接口指数行情")
    print("-" * 60)
    try:
        data = client.get('/market/v1/quote/index-data')
        if isinstance(data, list):
            for item in data:
                code = item.get('code', 'N/A')
                name = item.get('name', 'N/A')
                v = item.get('v', 'N/A')
                dir_val = item.get('dir', 'N/A')
                print(f"{code:12s} {name:10s} {v:>12}  {dir_val:+.2f}%")
        else:
            print(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"获取指数行情失败: {e}")


def show_new_search_fund(client: YJBClient, keyword: str):
    """新接口：搜索基金"""
    print(f"\n🔍 新接口搜索基金: {keyword}")
    print("-" * 60)
    try:
        data = client.post('/content/v1/search/fund', json={"keyword": keyword})
        funds = data.get('funds', []) if isinstance(data, dict) else []
        if not funds:
            print("未找到相关基金")
            return
        for fund in funds:
            code = fund.get('code', 'N/A')
            fund_id = fund.get('fund_id', 'N/A')
            name = fund.get('name', 'N/A')
            print(f"ID: {fund_id:<10}  {code:8s}  {name}")
    except Exception as e:
        print(f"搜索失败: {e}")


def _new_first_account_id(client: YJBClient) -> Optional[str]:
    """获取新接口第一个基金账户 ID"""
    data = client.get('/users/v1/user-account')
    accounts = data.get('list', []) if isinstance(data, dict) else []
    if accounts:
        return str(accounts[0].get('id', ''))
    return None


def show_new_holdings(client: YJBClient, account_id: Optional[str] = None):
    """新接口：基金持仓（需要先用 fund/batch 补名称/净值）"""
    print("\n💼 新接口基金持仓")
    print("-" * 60)
    try:
        if not account_id:
            account_id = _new_first_account_id(client)
            if not account_id:
                print("暂无账户")
                return

        holdings_data = client.get(f'/position/v1/static/fund-accounts/{account_id}/funds')
        holdings = holdings_data.get('list', []) if isinstance(holdings_data, dict) else []
        if not holdings:
            print("暂无持仓")
            return

        fund_ids = [h.get('fund_id') for h in holdings if h.get('fund_id')]
        fund_map = {}
        if fund_ids:
            batch_data = client.post('/market/v1/fund/batch', json={
                "funds": [{"fund_id": fid, "data_source": "1"} for fid in fund_ids]
            })
            if isinstance(batch_data, list):
                fund_map = {item.get('fund_id'): item for item in batch_data}

        print(f"{'代码':<10s} {'名称':<30s} {'持有份额':<12s} {'市值':<12s} {'持有收益':<12s}")
        print("-" * 80)
        for h in holdings:
            fund_id = h.get('fund_id')
            info = fund_map.get(fund_id, {})
            code = info.get('code', str(fund_id))
            name = info.get('short_name', 'N/A')
            shares = h.get('hold_share', 'N/A')
            money = h.get('money', 'N/A')
            earn = h.get('hold_earn', 'N/A')
            print(f"{code:<10s} {name:<30s} {shares:<12} {money:<12} {earn:<12}")
    except Exception as e:
        print(f"获取持仓失败: {e}")


def show_new_fund_detail(client: YJBClient, fund_id: str):
    """新接口：基金详情/概览/关联/重仓"""
    print(f"\n🔎 新接口基金详情: {fund_id}")
    print("-" * 60)
    try:
        overview = client.get(f'/market/v1/fund/overview?data_source=1&fund_id={fund_id}')
        print("📌 概览")
        print(json.dumps(overview, ensure_ascii=False, indent=2)[:2000])

        detail = client.get(f'/users/v1/fund/detail?fund_id={fund_id}')
        print("\n📌 用户相关")
        print(json.dumps(detail, ensure_ascii=False, indent=2)[:1000])

        relation = client.post('/market/v1/fund/relation-and-rank', json={"fund_id": int(fund_id)})
        print("\n📌 关联/排名")
        print(json.dumps(relation, ensure_ascii=False, indent=2)[:1500])

        hold_stock = client.get(f'/position/v1/static/fund/hold-stock?fund_id={fund_id}&page=1&per_page=10')
        print("\n📌 重仓股")
        print(json.dumps(hold_stock, ensure_ascii=False, indent=2)[:2000])
    except Exception as e:
        print(f"获取基金详情失败: {e}")


def show_new_market_ranking(client: YJBClient):
    """新接口：市场排行"""
    print("\n🏆 新接口市场排行")
    print("-" * 60)
    try:
        data = client.get('/market/v1/market-ranking/list')
        print(json.dumps(data, ensure_ascii=False, indent=2)[:3000])
    except Exception as e:
        print(f"获取市场排行失败: {e}")


def show_new_fund_groups(client: YJBClient):
    """新接口：基金分组"""
    print("\n🗂️ 新接口基金分组")
    print("-" * 60)
    try:
        data = client.get('/users/v1/fund-group')
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"获取基金分组失败: {e}")


def show_new_stock_penetrate(client: YJBClient, account_id: Optional[str] = None):
    """新接口：股票穿透持仓"""
    print("\n📊 新接口股票穿透持仓")
    print("-" * 60)
    try:
        if not account_id:
            account_id = _new_first_account_id(client)
            if not account_id:
                print("暂无账户")
                return

        overview = client.get(f'/position/v1/penetrate/hold/stock-overview?account_id={account_id}')
        print("📌 汇总")
        print(json.dumps(overview, ensure_ascii=False, indent=2))

        stocks = client.get(f'/position/v1/penetrate/hold/accounts/{account_id}/stocks')
        print("\n📌 明细")
        if isinstance(stocks, list):
            for s in stocks:
                code = s.get('stock_code', 'N/A')
                name = s.get('stock_name', 'N/A')
                price = s.get('last_price', 'N/A')
                change = s.get('daily_change', 'N/A')
                ratio = s.get('holding_percentage', 'N/A')
                print(f"{code:10s} {name:20s} 价格:{price:<10} 涨跌:{change:<8} 占比:{ratio}%")
        else:
            print(json.dumps(stocks, ensure_ascii=False, indent=2)[:2000])
    except Exception as e:
        print(f"获取股票穿透持仓失败: {e}")


def show_new_all_hold_simple(client: YJBClient):
    """新接口：全部持仓/自选简易列表"""
    print("\n📦 新接口持仓/自选简易列表")
    print("-" * 60)
    try:
        hold = client.get('/position/v1/user/funds/all-hold/simple')
        print("持仓：")
        print(json.dumps(hold, ensure_ascii=False, indent=2)[:2000])

        optional = client.get('/position/v1/user/funds/all-optional/simple')
        print("\n自选：")
        print(json.dumps(optional, ensure_ascii=False, indent=2)[:2000])
    except Exception as e:
        print(f"获取持仓/自选列表失败: {e}")


def show_new_etf_ranking(client: YJBClient):
    """新接口：ETF 排行"""
    print("\n🏆 新接口 ETF 排行")
    print("-" * 60)
    try:
        data = client.get('/market/v1/market-ranking/etf-ranking')
        print(json.dumps(data, ensure_ascii=False, indent=2)[:3000])
    except Exception as e:
        print(f"获取 ETF 排行失败: {e}")


def show_new_theme_ranking(client: YJBClient):
    """新接口：板块排行"""
    print("\n🏆 新接口板块排行")
    print("-" * 60)
    try:
        data = client.get('/market/v1/market-ranking/theme-ranking')
        print(json.dumps(data, ensure_ascii=False, indent=2)[:3000])
    except Exception as e:
        print(f"获取板块排行失败: {e}")


def show_new_fund_nav(client: YJBClient, fund_id: str):
    """新接口：基金历史净值"""
    print(f"\n📈 基金历史净值: {fund_id}")
    print("-" * 60)
    try:
        data = client.get(f'/market/v1/fund-nav/fund-history-nav?fund_id={fund_id}')
        print(json.dumps(data, ensure_ascii=False, indent=2)[:3000])
    except Exception as e:
        print(f"获取历史净值失败: {e}")


def show_new_fund_rate(client: YJBClient, fund_id: str):
    """新接口：基金实时涨幅"""
    print(f"\n📈 基金实时涨幅: {fund_id}")
    print("-" * 60)
    try:
        data = client.get(f'/market/v1/fund/increase-rate?fund_id={fund_id}')
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"获取基金涨幅失败: {e}")


def show_new_fund_gz(client: YJBClient, fund_id: str):
    """新接口：基金估值数据"""
    print(f"\n📈 基金估值: {fund_id}")
    print("-" * 60)
    try:
        data = client.get(f'/market/v1/fund/gz-data?fund_id={fund_id}&source=1')
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"获取基金估值失败: {e}")


def show_new_profit_analysis(client: YJBClient):
    """新接口：持仓行业收益分析"""
    print("\n📊 新接口持仓行业分析")
    print("-" * 60)
    try:
        data = client.get('/position/v1/profit-analysis/position-sector')
        print(json.dumps(data, ensure_ascii=False, indent=2)[:3000])
    except Exception as e:
        print(f"获取行业分析失败: {e}")


def show_version_info(client: YJBClient):
    """显示插件/接口版本信息"""
    print("\n📦 版本信息")
    print("-" * 60)

    try:
        data = client.get('/version_info')
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"获取版本信息失败: {e}")


def add_holdings(client: YJBClient, payload: Dict[str, Any]):
    """导入/新增持仓（POST /fund_hold）"""
    print("\n➕ 导入基金持仓")
    print("-" * 60)

    try:
        account_id = payload.get('account_id')
        items = payload.get('items', [])
        if not account_id or not items:
            print("错误：需要提供 account_id 和 items")
            return

        # 和插件保持一致的请求体结构
        body = {
            "items": items,
            "account_id": int(account_id),
            "sync_optional": payload.get("sync_optional", 0),
        }
        data = client.post('/fund_hold', json=body)
        print("导入成功：")
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"导入持仓失败: {e}")


def remove_holdings(client: YJBClient, payload: Dict[str, Any]):
    """删除持仓（DELETE /remove_fund_hold）"""
    print("\n➖ 删除基金持仓")
    print("-" * 60)

    try:
        account_id = payload.get('account_id')
        fund_ids = payload.get('fund_ids', [])
        if not account_id or not fund_ids:
            print("错误：需要提供 account_id 和 fund_ids")
            return

        query = "?" + "&".join([f"fund_ids[]={fid}" for fid in fund_ids])
        query += f"&account_id={account_id}"
        data = client.request('DELETE', f'/remove_fund_hold{query}')
        print("删除成功：")
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"删除持仓失败: {e}")


def parse_json_arg(raw: str) -> Dict[str, Any]:
    """解析命令行传入的 JSON 字符串"""
    try:
        return json.loads(raw)
    except Exception as e:
        print(f"错误：JSON 解析失败: {e}")
        sys.exit(1)


# 命令行入口
def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='养基宝命令行工具')
    parser.add_argument('--api', choices=['old', 'new'], default='old', help='选择接口：old=老插件接口（默认），new=App新接口')
    parser.add_argument('--login', action='store_true', help='重新登录（老接口二维码）')
    parser.add_argument('--sms-login', type=str, metavar='PHONE', help='新接口手机验证码登录')
    parser.add_argument('--search', type=str, metavar='KEYWORD', help='搜索基金（老接口）')
    parser.add_argument('--accounts', action='store_true', help='列出所有账户（老接口）')
    parser.add_argument('--holdings', type=str, metavar='ID', help='查看账户持仓（老接口）')
    parser.add_argument('--income-chart', action='store_true', help='查看收益曲线')
    parser.add_argument('--income-data', type=str, nargs='?', const='', metavar='ID', help='查看收益数据（不指定ID则查看汇总）')
    parser.add_argument('--notice', action='store_true', help='查看系统公告')
    parser.add_argument('--version-info', action='store_true', help='查看版本信息（老接口）')
    parser.add_argument('--add-holdings', type=str, metavar='JSON', help='导入持仓（老接口），JSON 格式：{"account_id":123,"items":[{"fund_id":1058,"fund_code":"501060","hold_share":100,"hold_cost":1.0}]}')
    parser.add_argument('--remove-holdings', type=str, metavar='JSON', help='删除持仓（老接口），JSON 格式：{"account_id":123,"fund_ids":[1058,21778]}')

    # 新接口（app-api）命令
    parser.add_argument('--new-user', action='store_true', help='新接口：用户信息')
    parser.add_argument('--new-accounts', action='store_true', help='新接口：基金账户列表')
    parser.add_argument('--new-index', action='store_true', help='新接口：指数行情')
    parser.add_argument('--new-search', type=str, metavar='KEYWORD', help='新接口：搜索基金')
    parser.add_argument('--new-holdings', type=str, nargs='?', const='', metavar='ACCOUNT_ID', help='新接口：基金持仓（不指定ID则用第一个账户）')
    parser.add_argument('--new-fund-detail', type=str, metavar='FUND_ID', help='新接口：基金详情/概览/重仓')
    parser.add_argument('--new-market-ranking', action='store_true', help='新接口：市场排行')
    parser.add_argument('--new-fund-groups', action='store_true', help='新接口：基金分组')
    parser.add_argument('--new-stock-penetrate', type=str, nargs='?', const='', metavar='ACCOUNT_ID', help='新接口：股票穿透持仓')
    parser.add_argument('--new-all-hold', action='store_true', help='新接口：全部持仓/自选简易列表')
    parser.add_argument('--new-etf-ranking', action='store_true', help='新接口：ETF排行')
    parser.add_argument('--new-theme-ranking', action='store_true', help='新接口：板块排行')
    parser.add_argument('--new-fund-nav', type=str, metavar='FUND_ID', help='新接口：基金历史净值')
    parser.add_argument('--new-fund-rate', type=str, metavar='FUND_ID', help='新接口：基金实时涨幅')
    parser.add_argument('--new-fund-gz', type=str, metavar='FUND_ID', help='新接口：基金估值')
    parser.add_argument('--new-profit-analysis', action='store_true', help='新接口：持仓行业分析')

    parser.add_argument('--debug', action='store_true', help='显示详细调试信息')

    args = parser.parse_args()

    # 登录
    if args.login:
        qrcode_login(debug=args.debug)
        return
    if args.sms_login:
        sms_login(args.sms_login, debug=args.debug)
        return

    # 检查 token
    token = load_token()
    if not token:
        print("未登录，请先运行：python3 yjb_tool.py --login 或 python3 yjb_tool.py --sms-login 手机号")
        sys.exit(1)

    # 创建客户端
    client = YJBClient(token=token, debug=args.debug, api=args.api)

    # 执行功能
    try:
        if args.search:
            search_fund(client, args.search)
        elif args.accounts:
            list_accounts(client)
        elif args.holdings:
            show_holdings(client, args.holdings)
        elif args.income_chart:
            show_income_chart(client)
        elif args.income_data is not None:
            show_income_data(client, args.income_data if args.income_data else None)
        elif args.notice:
            show_notice(client)
        elif args.version_info:
            show_version_info(client)
        elif args.add_holdings:
            add_holdings(client, parse_json_arg(args.add_holdings))
        elif args.remove_holdings:
            remove_holdings(client, parse_json_arg(args.remove_holdings))
        elif args.new_user:
            show_new_user(client)
        elif args.new_accounts:
            show_new_accounts(client)
        elif args.new_index:
            show_new_index(client)
        elif args.new_search:
            show_new_search_fund(client, args.new_search)
        elif args.new_holdings is not None:
            show_new_holdings(client, args.new_holdings if args.new_holdings else None)
        elif args.new_fund_detail:
            show_new_fund_detail(client, args.new_fund_detail)
        elif args.new_market_ranking:
            show_new_market_ranking(client)
        elif args.new_fund_groups:
            show_new_fund_groups(client)
        elif args.new_stock_penetrate is not None:
            show_new_stock_penetrate(client, args.new_stock_penetrate if args.new_stock_penetrate else None)
        elif args.new_all_hold:
            show_new_all_hold_simple(client)
        elif args.new_etf_ranking:
            show_new_etf_ranking(client)
        elif args.new_theme_ranking:
            show_new_theme_ranking(client)
        elif args.new_fund_nav:
            show_new_fund_nav(client, args.new_fund_nav)
        elif args.new_fund_rate:
            show_new_fund_rate(client, args.new_fund_rate)
        elif args.new_fund_gz:
            show_new_fund_gz(client, args.new_fund_gz)
        elif args.new_profit_analysis:
            show_new_profit_analysis(client)
        else:
            # 默认显示仪表盘（老接口）
            show_dashboard(client)

    except Exception as e:
        print(f"\n错误: {e}")
        if "未授权" in str(e) or "401" in str(e):
            print("Token 可能已过期，请重新登录：python3 yjb_tool.py --login 或 python3 yjb_tool.py --sms-login 手机号")
        sys.exit(1)


if __name__ == '__main__':
    main()
