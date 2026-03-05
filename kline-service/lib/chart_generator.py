"""
K线图生成模块

使用 matplotlib 生成股票风格 K 线图
"""

import io
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np


# 颜色主题配置
THEMES = {
    "light": {
        "background": "#ffffff",
        "text": "#24292f",
        "grid": "#e1e4e8",
        "up_color": "#1f883d",      # 绿色 - 上涨
        "down_color": "#cf222e",    # 红色 - 下跌
        "ma_color": "#0969da",      # 蓝色 - 均线
        "border": "#d0d7de"
    },
    "dark": {
        "background": "#0d1117",
        "text": "#c9d1d9",
        "grid": "#21262d",
        "up_color": "#3fb950",      # 绿色 - 上涨
        "down_color": "#f85149",    # 红色 - 下跌
        "ma_color": "#58a6ff",      # 蓝色 - 均线
        "border": "#30363d"
    }
}


def generate_kline_chart(
    ohlc_data: List[Dict],
    title: str = "GitHub Contributions K-Line",
    theme: str = "light",
    show_ma: bool = True,
    ma_period: int = 7,
    width: int = 800,
    height: int = 400
) -> str:
    """
    生成 K 线图并返回 SVG 字符串

    Args:
        ohlc_data: OHLC 数据列表
        title: 图表标题
        theme: 主题 ("light" 或 "dark")
        show_ma: 是否显示移动平均线
        ma_period: MA 周期
        width: 图片宽度
        height: 图片高度

    Returns:
        SVG 字符串
    """
    if not ohlc_data:
        return generate_empty_chart(title, theme, width, height)

    colors = THEMES.get(theme, THEMES["light"])

    # 设置 DPI
    dpi = 100
    fig, ax = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)

    # 设置背景色
    fig.patch.set_facecolor(colors["background"])
    ax.set_facecolor(colors["background"])

    # 准备数据
    dates = [datetime.strptime(d["date"], "%Y-%m-%d") for d in ohlc_data]
    x = np.arange(len(dates))

    # 绘制 K 线
    bar_width = 0.6

    for i, item in enumerate(ohlc_data):
        open_price = item["open"]
        close_price = item["close"]
        high_price = item["high"]
        low_price = item["low"]

        # 判断涨跌
        is_up = close_price >= open_price
        color = colors["up_color"] if is_up else colors["down_color"]

        # 绘制影线 (高低线)
        ax.plot([i, i], [low_price, high_price], color=color, linewidth=1, solid_capstyle='round')

        # 绘制实体
        body_bottom = min(open_price, close_price)
        body_height = abs(close_price - open_price)

        # 如果开平价相同，绘制细线
        if body_height == 0:
            body_height = 0.1  # 最小高度
            rect = Rectangle(
                (i - bar_width / 2, body_bottom),
                bar_width,
                body_height,
                facecolor=color,
                edgecolor=color,
                linewidth=0.5
            )
        else:
            rect = Rectangle(
                (i - bar_width / 2, body_bottom),
                bar_width,
                body_height,
                facecolor=color,
                edgecolor=color,
                linewidth=0.5
            )
        ax.add_patch(rect)

    # 绘制移动平均线
    if show_ma and len(ohlc_data) >= ma_period:
        ma_values = []
        for i in range(len(ohlc_data)):
            if i >= ma_period - 1:
                closes = [ohlc_data[j]["close"] for j in range(i - ma_period + 1, i + 1)]
                ma_values.append(sum(closes) / ma_period)
            else:
                ma_values.append(None)

        valid_indices = [i for i, v in enumerate(ma_values) if v is not None]
        valid_ma = [ma_values[i] for i in valid_indices]
        ax.plot(valid_indices, valid_ma, color=colors["ma_color"], linewidth=1.5,
                label=f'MA{ma_period}', alpha=0.8)

    # 设置坐标轴
    max_val = max(max(d["high"], 1) for d in ohlc_data)
    ax.set_xlim(-0.5, len(dates) - 0.5)
    ax.set_ylim(0, max_val * 1.15)

    # 设置 X 轴日期标签
    tick_step = max(1, len(dates) // 8)  # 最多显示8个标签
    tick_positions = list(range(0, len(dates), tick_step))
    tick_labels = [dates[i].strftime("%m/%d") for i in tick_positions]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, rotation=45, ha='right', fontsize=9)

    # 设置 Y 轴
    ax.set_ylabel('Contributions', fontsize=10, color=colors["text"])
    ax.tick_params(axis='y', labelsize=9)

    # 设置标题
    ax.set_title(title, fontsize=12, fontweight='bold', color=colors["text"], pad=10)

    # 设置网格
    ax.grid(True, axis='y', color=colors["grid"], linestyle='-', linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)

    # 设置边框颜色
    for spine in ax.spines.values():
        spine.set_color(colors["border"])

    # 设置刻度颜色
    ax.tick_params(axis='both', colors=colors["text"])
    ax.xaxis.label.set_color(colors["text"])
    ax.yaxis.label.set_color(colors["text"])

    # 添加图例
    if show_ma and len(ohlc_data) >= ma_period:
        legend = ax.legend(loc='upper left', framealpha=0.9, fontsize=9)
        legend.get_frame().set_facecolor(colors["background"])
        for text in legend.get_texts():
            text.set_color(colors["text"])

    # 调整布局
    plt.tight_layout()

    # 输出 SVG
    buffer = io.StringIO()
    plt.savefig(buffer, format='svg', facecolor=fig.get_facecolor(),
                edgecolor='none', bbox_inches='tight')
    plt.close(fig)

    return buffer.getvalue()


def generate_empty_chart(
    title: str = "GitHub Contributions K-Line",
    theme: str = "light",
    width: int = 800,
    height: int = 400
) -> str:
    """
    生成空图表（无数据时显示）

    Returns:
        SVG 字符串
    """
    colors = THEMES.get(theme, THEMES["light"])
    dpi = 100

    fig, ax = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
    fig.patch.set_facecolor(colors["background"])
    ax.set_facecolor(colors["background"])

    ax.text(0.5, 0.5, 'No contribution data available',
            ha='center', va='center', fontsize=14,
            color=colors["text"], transform=ax.transAxes)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    buffer = io.StringIO()
    plt.savefig(buffer, format='svg', facecolor=fig.get_facecolor(),
                edgecolor='none', bbox_inches='tight')
    plt.close(fig)

    return buffer.getvalue()


def generate_compact_kline(
    ohlc_data: List[Dict],
    theme: str = "light",
    width: int = 600,
    height: int = 200
) -> str:
    """
    生成紧凑型 K 线图（适合嵌入 README）

    Args:
        ohlc_data: OHLC 数据
        theme: 主题
        width: 宽度
        height: 高度

    Returns:
        SVG 字符串
    """
    if not ohlc_data:
        return generate_empty_chart("No Data", theme, width, height)

    colors = THEMES.get(theme, THEMES["light"])
    dpi = 100

    fig, ax = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
    fig.patch.set_facecolor(colors["background"])
    ax.set_facecolor(colors["background"])

    # 准备数据
    dates = [datetime.strptime(d["date"], "%Y-%m-%d") for d in ohlc_data]

    # 绘制 K 线（简化版）
    bar_width = 0.7

    for i, item in enumerate(ohlc_data):
        open_p = item["open"]
        close_p = item["close"]
        high_p = item["high"]
        low_p = item["low"]

        is_up = close_p >= open_p
        color = colors["up_color"] if is_up else colors["down_color"]

        # 影线
        ax.plot([i, i], [low_p, high_p], color=color, linewidth=0.8)

        # 实体
        body_bottom = min(open_p, close_p)
        body_height = max(abs(close_p - open_p), 0.1)

        rect = Rectangle(
            (i - bar_width / 2, body_bottom),
            bar_width, body_height,
            facecolor=color, edgecolor=color, linewidth=0.3
        )
        ax.add_patch(rect)

    # 设置坐标轴
    max_val = max(max(d["high"], 1) for d in ohlc_data)
    ax.set_xlim(-0.5, len(dates) - 0.5)
    ax.set_ylim(0, max_val * 1.1)

    # 简化的 X 轴标签
    tick_step = max(1, len(dates) // 6)
    tick_positions = list(range(0, len(dates), tick_step))
    tick_labels = [dates[i].strftime("%m/%d") for i in tick_positions]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, fontsize=8, color=colors["text"])

    # 隐藏 Y 轴刻度，只显示数值
    ax.tick_params(axis='y', labelsize=8, colors=colors["text"])
    ax.set_ylabel('', fontsize=8)

    # 网格
    ax.grid(True, axis='y', color=colors["grid"], linewidth=0.3, alpha=0.5)
    ax.set_axisbelow(True)

    # 边框
    for spine in ax.spines.values():
        spine.set_color(colors["border"])

    plt.tight_layout()

    buffer = io.StringIO()
    plt.savefig(buffer, format='svg', facecolor=fig.get_facecolor(),
                edgecolor='none', bbox_inches='tight')
    plt.close(fig)

    return buffer.getvalue()
