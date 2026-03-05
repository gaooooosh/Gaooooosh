"""
GitHub API 数据获取模块

获取 GitHub 用户的 contributions 数据
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re


def fetch_contributions_page(username: str) -> Optional[str]:
    """
    获取用户 contributions 页面

    Args:
        username: GitHub 用户名

    Returns:
        HTML 内容，失败返回 None
    """
    url = f"https://github.com/users/{username}/contributions"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching contributions page: {e}")
        return None


def parse_contributions_from_html(html_content: str) -> Dict[str, int]:
    """
    从 HTML 中解析 contributions 数据

    Args:
        html_content: GitHub contributions 页面 HTML

    Returns:
        日期到贡献等级的映射 {"2024-01-01": 1, ...}
    """
    contributions = {}

    # 匹配 data-date 和 data-level 属性
    # 格式: data-date="2024-01-01" ... data-level="3"
    pattern = r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)"'

    matches = re.findall(pattern, html_content)

    for date_str, level in matches:
        # 将 level 转换为估算的贡献数
        # level 0 = 0 贡献
        # level 1 = 1-3 贡献 (取中值 2)
        # level 2 = 4-6 贡献 (取中值 5)
        # level 3 = 7-9 贡献 (取中值 8)
        # level 4 = 10+ 贡献 (取 12)
        level_to_count = {
            "0": 0,
            "1": 2,
            "2": 5,
            "3": 8,
            "4": 12
        }
        contributions[date_str] = level_to_count.get(level, 0)

    return contributions


def get_daily_contributions(username: str, days: int = 90) -> List[Dict]:
    """
    获取指定天数的每日 contributions 数据

    Args:
        username: GitHub 用户名
        days: 获取最近多少天的数据

    Returns:
        每日贡献数据列表 [{"date": "2024-01-01", "count": 5}, ...]
    """
    html_content = fetch_contributions_page(username)
    if not html_content:
        return []

    all_contributions = parse_contributions_from_html(html_content)

    # 计算日期范围
    today = datetime.now().date()
    start_date = today - timedelta(days=days)

    # 过滤并排序数据
    daily_data = []
    for date_str, count in all_contributions.items():
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if start_date <= date <= today:
                daily_data.append({
                    "date": date_str,
                    "count": count
                })
        except ValueError:
            continue

    # 按日期排序
    daily_data.sort(key=lambda x: x["date"])

    return daily_data


def fill_missing_days(daily_data: List[Dict], days: int = 90) -> List[Dict]:
    """
    填充缺失的日期（贡献数为0）

    Args:
        daily_data: 已有的每日数据
        days: 总天数

    Returns:
        完整的每日数据列表
    """
    # 创建日期到数据的映射
    data_map = {item["date"]: item["count"] for item in daily_data}

    # 计算日期范围
    today = datetime.now().date()
    start_date = today - timedelta(days=days - 1)

    filled_data = []
    current_date = start_date
    while current_date <= today:
        date_str = current_date.strftime("%Y-%m-%d")
        filled_data.append({
            "date": date_str,
            "count": data_map.get(date_str, 0)
        })
        current_date += timedelta(days=1)

    return filled_data
