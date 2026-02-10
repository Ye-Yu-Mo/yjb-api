#!/usr/bin/env python3
"""
测试脚本：打印所有 API 的完整响应
"""
import json
import sys
from pathlib import Path

# 导入主程序的模块
sys.path.insert(0, str(Path(__file__).parent))
from yjb_tool import YJBClient, load_token

def print_api_response(name: str, data: dict):
    """格式化打印 API 响应"""
    print("\n" + "=" * 80)
    print(f"📡 {name}")
    print("=" * 80)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print()


def main():
    # 加载 token
    token = load_token()
    if not token:
        print("错误：未登录，请先运行：python3 yjb_tool.py --login")
        sys.exit(1)

    # 创建客户端
    client = YJBClient(token=token, debug=False)

    print("🔍 开始测试所有 API...")

    # 1. 搜索基金
    try:
        data = client.get('/search_fund?keyword=110011')
        print_api_response("搜索基金 (/search_fund?keyword=110011)", data)
    except Exception as e:
        print(f"❌ 搜索基金失败: {e}\n")

    # 2. 账户列表
    accounts_data = None
    try:
        accounts_data = client.get('/user_account')
        print_api_response("账户列表 (/user_account)", accounts_data)
    except Exception as e:
        print(f"❌ 账户列表失败: {e}\n")

    # 3. 持仓（使用第一个账户）
    if accounts_data and isinstance(accounts_data, dict):
        accounts = accounts_data.get('list', [])
        if accounts:
            account_id = accounts[0].get('id')
            try:
                data = client.get(f'/fund_hold?account_id={account_id}')
                print_api_response(f"持仓 (/fund_hold?account_id={account_id})", data)
            except Exception as e:
                print(f"❌ 持仓失败: {e}\n")

    # 4. 收益曲线
    try:
        data = client.get('/income_line_data?collect=true&date_type=day')
        print_api_response("收益曲线 (/income_line_data?collect=true&date_type=day)", data)
    except Exception as e:
        print(f"❌ 收益曲线失败: {e}\n")

    # 5. 收益数据
    try:
        data = client.get('/income_data?collect=true')
        print_api_response("收益数据 (/income_data?collect=true)", data)
    except Exception as e:
        print(f"❌ 收益数据失败: {e}\n")

    # 6. 系统公告
    try:
        data = client.get('/notice')
        print_api_response("系统公告 (/notice)", data)
    except Exception as e:
        print(f"❌ 系统公告失败: {e}\n")

    print("✅ 测试完成！")


if __name__ == '__main__':
    main()
