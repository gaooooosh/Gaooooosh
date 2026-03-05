"""
K线数据转换模块

将每日 contributions 数据转换为 OHLC (Open-High-Low-Close) 格式
使用滑动窗口算法
"""

from typing import List, Dict
from datetime import datetime


def convert_to_ohlc(daily_data: List[Dict], window_size: int = 7) -> List[Dict]:
    """
    将每日数据转换为 K 线 OHLC 格式

    使用滑动窗口：
    - Open: 窗口起始日 contributions
    - High: 窗口内最大 contributions
    - Low: 窗口内最小 contributions
    - Close: 窗口结束日 contributions

    Args:
        daily_data: 每日数据 [{"date": "2024-01-01", "count": 5}, ...]
        window_size: 滑动窗口大小（必须为奇数）

    Returns:
        OHLC 数据列表
    """
    if not daily_data or len(daily_data) < window_size:
        return []

    half_window = window_size // 2
    ohlc_data = []

    # 遍历数据，从能够形成完整窗口的位置开始
    for i in range(half_window, len(daily_data) - half_window):
        window = daily_data[i - half_window: i + half_window + 1]
        counts = [item["count"] for item in window]

        ohlc = {
            "date": daily_data[i]["date"],
            "open": counts[0],           # 窗口起始
            "high": max(counts),         # 窗口最高
            "low": min(counts),          # 窗口最低
            "close": counts[-1],         # 窗口结束
            "center_count": daily_data[i]["count"]  # 中心日实际贡献
        }
        ohlc_data.append(ohlc)

    return ohlc_data


def convert_to_weekly_ohlc(daily_data: List[Dict]) -> List[Dict]:
    """
    将每日数据按周聚合为 K 线格式

    每周的 OHLC:
    - Open: 周一 contributions
    - High: 本周最大 contributions
    - Low: 本周最小 contributions
    - Close: 周日 contributions

    Args:
        daily_data: 每日数据

    Returns:
        周 K 线数据列表
    """
    if not daily_data:
        return []

    weekly_data = []
    current_week = []
    current_week_num = None

    for item in daily_data:
        date = datetime.strptime(item["date"], "%Y-%m-%d")
        week_num = date.isocalendar()[:2]  # (year, week_number)

        if current_week_num is None:
            current_week_num = week_num

        if week_num != current_week_num:
            # 保存上一周数据
            if current_week:
                counts = [d["count"] for d in current_week]
                weekly_data.append({
                    "date": current_week[0]["date"],
                    "week_end": current_week[-1]["date"],
                    "open": counts[0],
                    "high": max(counts),
                    "low": min(counts),
                    "close": counts[-1]
                })

            # 开始新的一周
            current_week = [item]
            current_week_num = week_num
        else:
            current_week.append(item)

    # 处理最后一周
    if current_week:
        counts = [d["count"] for d in current_week]
        weekly_data.append({
            "date": current_week[0]["date"],
            "week_end": current_week[-1]["date"],
            "open": counts[0],
            "high": max(counts),
            "low": min(counts),
            "close": counts[-1]
        })

    return weekly_data


def add_ma_line(ohlc_data: List[Dict], period: int = 7) -> List[Dict]:
    """
    添加移动平均线数据

    Args:
        ohlc_data: OHLC 数据
        period: 均线周期

    Returns:
        添加了 MA 数据的列表
    """
    if len(ohlc_data) < period:
        return ohlc_data

    result = []
    for i, item in enumerate(ohlc_data):
        new_item = item.copy()
        if i >= period - 1:
            ma_values = [ohlc_data[j]["close"] for j in range(i - period + 1, i + 1)]
            new_item["ma"] = sum(ma_values) / period
        else:
            new_item["ma"] = None
        result.append(new_item)

    return result
