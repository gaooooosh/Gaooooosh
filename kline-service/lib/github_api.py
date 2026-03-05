"""
GitHub API 数据获取模块

获取 GitHub 用户的 contributions 数据
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re


def fetch_contributions_svg(username: str) -> Optional[str]:
    """
    获取用户 contributions SVG 页面

    Args:
        username: GitHub 用户名

    Returns:
        SVG 文本内容，失败返回 None
    """
    url = f"https://github.com/{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching GitHub page: {e}")
        return None


def parse_contributions_from_html(html_content: str) -> Dict[str, int]:
    """
    从 HTML 中解析 contributions 数据

    Args:
        html_content: GitHub 用户主页 HTML

    Returns:
        日期到贡献数的映射 {"2024-01-01": 5, ...}
    """
    contributions = {}

    # 匹配 contribution tile 元素
    # 格式: data-date="2024-01-01" data-level="3"
    # 或者: <rect ... data-date="2024-01-01" data-count="5" .../>
    pattern = r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*(?:data-level|data-count)'

    # 更精确的匹配模式
    rect_pattern = r'<rect[^>]*data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-count="(\d+)"[^>]*/>'
    tool_tip_pattern = r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d)"'

    # 尝试匹配带 data-count 的 rect 元素
    matches = re.findall(rect_pattern, html_content)

    if matches:
        for date_str, count in matches:
            contributions[date_str] = int(count)
    else:
        # 尝试匹配带 data-level 的元素
        # 需要结合 tooltip 信息来估算数量
        matches = re.findall(tool_tip_pattern, html_content)
        level_to_count = {
            "0": 0,
            "1": 1,
            "2": 3,
            "3": 6,
            "4": 10
        }
        for date_str, level in matches:
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
    html_content = fetch_contributions_svg(username)
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
    if not daily_data:
        # 如果没有数据，生成空的占位数据
        today = datetime.now().date()
        return [
            {"date": (today - timedelta(days=i)).strftime("%Y-%m-%d"), "count": 0}
            for i in range(days - 1, -1, -1)
        ]

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
