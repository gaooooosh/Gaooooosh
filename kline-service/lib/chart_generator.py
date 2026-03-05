"""
专业 K 线图生成模块

生成符合中国股市习惯的专业 K 线图（红涨绿跌）
"""

import io
from typing import List, Dict
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
import numpy as np


THEMES = {
    "light": {
        "bg": "#FFFFFF",
        "panel_bg": "#FAFAFA",
        "text": "#1A1A1A",
        "text_light": "#666666",
        "grid": "#E5E5E5",
        "up_body": "#DC2626",
        "down_body": "#059669",
        "up_alpha": 0.3,
        "down_alpha": 0.3,
        "ma5": "#EF4444",
        "ma10": "#F59E0B",
        "ma20": "#10B981",
        "vol_up": "#DC2626",
        "vol_down": "#059669",
        "border": "#DDDDDD",
        "axis_line": "#CCCCCC"
    },
    "dark": {
        "bg": "#131722",
        "panel_bg": "#1E222D",
        "text": "#D1D4DC",
        "text_light": "#8B949E",
        "grid": "#2A2E39",
        "up_body": "#EF4444",
        "down_body": "#10B981",
        "up_alpha": 0.3,
        "down_alpha": 0.3,
        "ma5": "#F87171",
        "ma10": "#FBBF24",
        "ma20": "#34D399",
        "vol_up": "#EF4444",
        "vol_down": "#10B981",
        "border": "#363A45",
        "axis_line": "#363A45"
    }
}


def calculate_ma(data: List[Dict], period: int) -> List[float]:
    """计算移动平均线"""
    ma = []
    closes = [d["close"] for d in data]
    for i in range(len(closes)):
        if i < period - 1:
            ma.append(None)
        else:
            ma.append(sum(closes[i-period+1:i+1]) / period)
    return ma


def generate_kline_chart(
    ohlc_data: List[Dict],
    title: str = "GitHub Contributions",
    theme: str = "light",
    width: int = 900,
    height: int = 400,
    show_volume: bool = True
) -> str:
    """生成专业风格 K 线图"""
    if not ohlc_data:
        return generate_empty_chart(title, theme, width, height)

    colors = THEMES.get(theme, THEMES["light"])
    dpi = 120

    fig = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi)

    if show_volume:
        gs = fig.add_gridspec(2, 1, height_ratios=[3.5, 1], hspace=0.03)
        ax_main = fig.add_subplot(gs[0])
        ax_vol = fig.add_subplot(gs[1])
    else:
        ax_main = fig.add_subplot(111)
        ax_vol = None

    fig.patch.set_facecolor(colors["bg"])
    ax_main.set_facecolor(colors["panel_bg"])
    if ax_vol:
        ax_vol.set_facecolor(colors["panel_bg"])

    n = len(ohlc_data)
    dates = [datetime.strptime(d["date"], "%Y-%m-%d") for d in ohlc_data]
    bar_width = max(0.4, min(0.8, 20 / n))

    # 绘制 K 线
    for i, item in enumerate(ohlc_data):
        is_up = item["close"] >= item["open"]
        body_fill = colors["up_body"] if is_up else colors["down_body"]
        alpha = colors["up_alpha"] if is_up else colors["down_alpha"]

        body_bottom = min(item["open"], item["close"])
        body_height = max(abs(item["close"] - item["open"]), 0.08)

        rect = Rectangle(
            (i - bar_width / 2, body_bottom),
            bar_width, body_height,
            facecolor=body_fill, edgecolor='none', alpha=alpha, zorder=2
        )
        ax_main.add_patch(rect)

    # 绘制均线
    ma_configs = [
        (5, colors["ma5"], "MA5", 2.5),
        (10, colors["ma10"], "MA10", 2.2),
        (20, colors["ma20"], "MA20", 1.8),
    ]
    for period, color, label, lw in ma_configs:
        if n >= period:
            ma = calculate_ma(ohlc_data, period)
            valid_x = [i for i, v in enumerate(ma) if v is not None]
            valid_y = [ma[i] for i in valid_x]
            ax_main.plot(valid_x, valid_y, color=color, linewidth=lw,
                        label=label, alpha=0.95, zorder=10)

    # 绘制成交量
    max_vol = 1
    if ax_vol:
        vol_width = bar_width * 0.8
        for i, item in enumerate(ohlc_data):
            vol = item.get("center_count", 0)
            if vol == 0:
                vol = abs(item["close"] - item["open"]) + 0.3
            max_vol = max(max_vol, vol)

            is_up = item["close"] >= item["open"]
            vol_color = colors["vol_up"] if is_up else colors["vol_down"]

            rect = Rectangle(
                (i - vol_width / 2, 0), vol_width, max(vol, 0.1),
                facecolor=vol_color, edgecolor='none', alpha=0.6, zorder=1
            )
            ax_vol.add_patch(rect)

    # 坐标轴设置
    max_price = max(d["high"] for d in ohlc_data)
    ax_main.set_xlim(-1, n)
    ax_main.set_ylim(0, max_price * 1.25)

    # X轴日期 - 优化：减少标签数量，避免重叠
    # 根据数据量动态调整标签间隔
    if n <= 30:
        tick_interval = max(1, n // 5)
    elif n <= 60:
        tick_interval = max(1, n // 6)
    else:
        tick_interval = max(1, n // 7)

    tick_positions = list(range(0, n, tick_interval))
    if tick_positions and tick_positions[-1] != n - 1:
        tick_positions.append(n - 1)

    ax_main.set_xticks(tick_positions)
    ax_main.set_xticklabels([])

    ax_main.yaxis.tick_right()
    ax_main.yaxis.set_label_position("right")
    ax_main.tick_params(axis='y', labelsize=9, colors=colors["text_light"])

    ax_main.grid(True, axis='y', color=colors["grid"], linestyle='-', linewidth=0.8, alpha=0.9)
    ax_main.set_axisbelow(True)

    for spine in ['top', 'left']:
        ax_main.spines[spine].set_visible(False)
    ax_main.spines['right'].set_color(colors["axis_line"])
    ax_main.spines['bottom'].set_color(colors["axis_line"])

    # 成交量图
    if ax_vol:
        ax_vol.set_xlim(-1, n)
        ax_vol.set_ylim(0, max_vol * 1.2)
        ax_vol.set_xticks(tick_positions)
        # 日期格式优化：只显示月-日，旋转30度避免重叠
        ax_vol.set_xticklabels(
            [dates[i].strftime("%m-%d") for i in tick_positions],
            fontsize=8, color=colors["text_light"], rotation=30, ha='right'
        )
        ax_vol.yaxis.tick_right()
        ax_vol.tick_params(axis='y', labelsize=8, colors=colors["text_light"])

        for spine in ['top', 'left', 'right']:
            ax_vol.spines[spine].set_visible(False)
        ax_vol.spines['bottom'].set_color(colors["axis_line"])
        ax_vol.grid(True, axis='y', color=colors["grid"], linestyle='--', linewidth=0.5, alpha=0.6)

    # ========== 左上角信息面板 ==========
    # 计算所需数据
    today = datetime.now().date()

    # 昨日收盘价（昨天的 close 值）
    yesterday_close = ohlc_data[-1]["close"] if ohlc_data else 0

    # 本月均价（本月数据的平均 close）
    current_month = today.month
    current_year = today.year
    month_data = [d for d in ohlc_data
                  if datetime.strptime(d["date"], "%Y-%m-%d").month == current_month
                  and datetime.strptime(d["date"], "%Y-%m-%d").year == current_year]
    month_avg = sum(d["close"] for d in month_data) / len(month_data) if month_data else 0

    # 现价（今日的 center_count 或 close）
    current_price = ohlc_data[-1].get("center_count", ohlc_data[-1]["close"]) if ohlc_data else 0

    # 涨跌计算
    if len(ohlc_data) >= 2:
        prev_close = ohlc_data[-2]["close"]
        change = current_price - prev_close
        change_pct = (change / prev_close * 100) if prev_close > 0 else 0
    else:
        change = 0
        change_pct = 0

    change_color = colors["up_body"] if change >= 0 else colors["down_body"]
    sign = "+" if change >= 0 else ""

    # 左上角信息框
    info_lines = [
        f"Prev Close: {yesterday_close:.1f}",
        f"Month Avg: {month_avg:.1f}",
        f"Current: {current_price:.1f} ({sign}{change_pct:.1f}%)"
    ]

    info_text = "\n".join(info_lines)
    ax_main.text(0.02, 0.96, info_text, transform=ax_main.transAxes, fontsize=9,
                 color=colors["text"], ha='left', va='top', fontweight='400',
                 linespacing=1.6,
                 bbox=dict(boxstyle='round,pad=0.5', facecolor=colors["panel_bg"],
                           edgecolor=colors["border"], alpha=0.95))

    # 右上角图例
    if n >= 5:
        legend_elements = [
            Line2D([0], [0], color=colors["ma5"], linewidth=2.5, label='MA5'),
            Line2D([0], [0], color=colors["ma10"], linewidth=2.2, label='MA10'),
            Line2D([0], [0], color=colors["ma20"], linewidth=1.8, label='MA20'),
        ]
        legend = ax_main.legend(handles=legend_elements, loc='upper right', frameon=True,
                                fontsize=9, fancybox=False, edgecolor=colors["border"],
                                framealpha=0.95, handlelength=1.5, borderpad=0.5)
        legend.get_frame().set_facecolor(colors["panel_bg"])
        for text in legend.get_texts():
            text.set_color(colors["text"])

    plt.tight_layout(pad=0.5)

    buffer = io.StringIO()
    plt.savefig(buffer, format='svg', facecolor=fig.get_facecolor(),
                edgecolor='none', bbox_inches='tight')
    plt.close(fig)

    return buffer.getvalue()


def generate_compact_kline(
    ohlc_data: List[Dict],
    theme: str = "light",
    width: int = 700,
    height: int = 200
) -> str:
    """紧凑型 K 线图"""
    if not ohlc_data:
        return generate_empty_chart("No Data", theme, width, height)

    colors = THEMES.get(theme, THEMES["light"])
    dpi = 120

    fig, ax = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
    fig.patch.set_facecolor(colors["bg"])
    ax.set_facecolor(colors["panel_bg"])

    n = len(ohlc_data)
    dates = [datetime.strptime(d["date"], "%Y-%m-%d") for d in ohlc_data]
    bar_width = max(0.5, min(0.85, 18 / n))

    for i, item in enumerate(ohlc_data):
        is_up = item["close"] >= item["open"]
        body_fill = colors["up_body"] if is_up else colors["down_body"]
        alpha = colors["up_alpha"] if is_up else colors["down_alpha"]

        body_bottom = min(item["open"], item["close"])
        body_height = max(abs(item["close"] - item["open"]), 0.08)

        rect = Rectangle((i - bar_width / 2, body_bottom), bar_width, body_height,
                          facecolor=body_fill, edgecolor='none', alpha=alpha, zorder=2)
        ax.add_patch(rect)

    for period, color, lw in [(5, colors["ma5"], 2.0), (10, colors["ma10"], 1.6)]:
        if n >= period:
            ma = calculate_ma(ohlc_data, period)
            valid_x = [i for i, v in enumerate(ma) if v is not None]
            valid_y = [ma[i] for i in valid_x]
            ax.plot(valid_x, valid_y, color=color, linewidth=lw, alpha=0.95, zorder=10)

    max_val = max(d["high"] for d in ohlc_data)
    ax.set_xlim(-0.5, n - 0.5)
    ax.set_ylim(0, max_val * 1.15)

    # 优化日期标签
    tick_step = max(1, n // 5)
    tick_pos = list(range(0, n, tick_step))
    ax.set_xticks(tick_pos)
    ax.set_xticklabels([dates[i].strftime("%m/%d") for i in tick_pos],
                       fontsize=8, color=colors["text_light"], rotation=30, ha='right')

    ax.yaxis.tick_right()
    ax.tick_params(axis='y', labelsize=8, colors=colors["text_light"])
    ax.grid(True, axis='y', color=colors["grid"], linewidth=0.6, alpha=0.8)

    for spine in ['top', 'left']:
        ax.spines[spine].set_visible(False)
    for spine in ['right', 'bottom']:
        ax.spines[spine].set_color(colors["axis_line"])

    plt.tight_layout()

    buffer = io.StringIO()
    plt.savefig(buffer, format='svg', facecolor=fig.get_facecolor(),
                edgecolor='none', bbox_inches='tight')
    plt.close(fig)

    return buffer.getvalue()


def generate_empty_chart(title: str = "No Data", theme: str = "light",
                         width: int = 700, height: int = 200) -> str:
    """空图表"""
    colors = THEMES.get(theme, THEMES["light"])
    dpi = 120

    fig, ax = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
    fig.patch.set_facecolor(colors["bg"])
    ax.set_facecolor(colors["panel_bg"])

    ax.text(0.5, 0.5, 'No contribution data', ha='center', va='center',
            fontsize=14, color=colors["text_light"], fontweight=500)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    buffer = io.StringIO()
    plt.savefig(buffer, format='svg', facecolor=fig.get_facecolor(),
                edgecolor='none', bbox_inches='tight')
    plt.close(fig)

    return buffer.getvalue()
