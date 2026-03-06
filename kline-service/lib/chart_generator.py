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
        "panel_bg": "#FFFFFF",  # 与背景统一
        "text": "#1A1A1A",
        "text_light": "#888888",  # 更淡的灰色，减少视觉干扰
        "grid": "#F5F5F5",  # 更淡的网格
        # 红涨绿跌 - 经典配色
        "up_body": "#E74C3C",
        "down_body": "#27AE60",
        "up_alpha": 0.9,
        "down_alpha": 0.9,
        # 均线配色 - 与K线形成对比：蓝、橙、紫
        "ma5": "#3498DB",   # 蓝色 - 与红色K线对比
        "ma10": "#F39C12",  # 橙色 - 中间色调
        "ma20": "#9B59B6",  # 紫色 - 与绿色K线对比
        "vol_up": "#E74C3C",
        "vol_down": "#27AE60",
        "border": "#FFFFFF",
        "axis_line": "#FFFFFF"  # 隐藏轴线
    },
    "dark": {
        "bg": "#0D1117",
        "panel_bg": "#0D1117",  # 与背景统一
        "text": "#E6EDF3",
        "text_light": "#6E7681",  # 更淡的灰色
        "grid": "#21262D",  # 更淡的网格
        # 暗色模式红绿
        "up_body": "#F85149",
        "down_body": "#3FB950",
        "up_alpha": 0.9,
        "down_alpha": 0.9,
        # 均线配色 - 暗色模式下更亮
        "ma5": "#58A6FF",   # 亮蓝色
        "ma10": "#F0883E",  # 亮橙色
        "ma20": "#A371F7",  # 亮紫色
        "vol_up": "#F85149",
        "vol_down": "#3FB950",
        "border": "#0D1117",
        "axis_line": "#0D1117"  # 隐藏轴线
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

    # 绘制 K 线 - 现代化设计，增加边框和阴影效果
    for i, item in enumerate(ohlc_data):
        is_up = item["close"] >= item["open"]
        body_fill = colors["up_body"] if is_up else colors["down_body"]
        alpha = colors["up_alpha"] if is_up else colors["down_alpha"]
        edge_color = colors["up_body"] if is_up else colors["down_body"]

        body_bottom = min(item["open"], item["close"])
        body_height = max(abs(item["close"] - item["open"]), 0.08)

        # K线主体 - 增加边框使线条更清晰
        rect = Rectangle(
            (i - bar_width / 2, body_bottom),
            bar_width, body_height,
            facecolor=body_fill, edgecolor=edge_color,
            alpha=alpha, linewidth=1.2, zorder=2
        )
        ax_main.add_patch(rect)

        # 绘制影线（误差线风格 - 细线）
        high = item.get("high", max(item["open"], item["close"]))
        low = item.get("low", min(item["open"], item["close"]))
        ax_main.plot([i, i], [low, body_bottom], color=edge_color, linewidth=0.8, alpha=0.6, zorder=1)
        ax_main.plot([i, i], [body_bottom + body_height, high], color=edge_color, linewidth=0.8, alpha=0.6, zorder=1)

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

    # 绘制成交量 - 现代化设计
    max_vol = 1
    if ax_vol:
        vol_width = bar_width * 0.85
        for i, item in enumerate(ohlc_data):
            vol = item.get("center_count", 0)
            if vol == 0:
                vol = abs(item["close"] - item["open"]) + 0.3
            max_vol = max(max_vol, vol)

            is_up = item["close"] >= item["open"]
            vol_color = colors["vol_up"] if is_up else colors["vol_down"]

            # 成交量柱状图 - 增加边框效果
            rect = Rectangle(
                (i - vol_width / 2, 0), vol_width, max(vol, 0.1),
                facecolor=vol_color, edgecolor=vol_color,
                alpha=0.65, linewidth=1.0, zorder=1
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
    ax_main.tick_params(axis='y', labelsize=10, colors=colors["text_light"])

    ax_main.grid(True, axis='y', color=colors["grid"], linestyle='--', linewidth=0.4, alpha=0.4)
    ax_main.set_axisbelow(True)

    # 隐藏所有轴线 - 极简设计
    for spine in ['top', 'left', 'right', 'bottom']:
        ax_main.spines[spine].set_visible(False)

    # 成交量图
    if ax_vol:
        ax_vol.set_xlim(-1, n)
        ax_vol.set_ylim(0, max_vol * 1.2)
        ax_vol.set_xticks(tick_positions)
        # 日期格式优化：只显示月-日，旋转30度避免重叠
        ax_vol.set_xticklabels(
            [dates[i].strftime("%m-%d") for i in tick_positions],
            fontsize=9, color=colors["text_light"], rotation=30, ha='right'
        )
        ax_vol.yaxis.tick_right()
        ax_vol.tick_params(axis='y', labelsize=9, colors=colors["text_light"])

        # 隐藏所有轴线 - 极简设计
        for spine in ['top', 'left', 'right', 'bottom']:
            ax_vol.spines[spine].set_visible(False)
        ax_vol.grid(True, axis='y', color=colors["grid"], linestyle='--', linewidth=0.4, alpha=0.4)

    # ========== 右上角图例 - 现代横向卡片设计 ==========
    if n >= 5:
        # 使用圆点标记 + 横向布局
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor=colors["ma5"],
                   markersize=8, label='MA5', linewidth=0),
            Line2D([0], [0], marker='o', color='w', markerfacecolor=colors["ma10"],
                   markersize=8, label='MA10', linewidth=0),
            Line2D([0], [0], marker='o', color='w', markerfacecolor=colors["ma20"],
                   markersize=8, label='MA20', linewidth=0),
        ]

        # 横向布局，圆角背景
        legend = ax_main.legend(handles=legend_elements, loc='upper right',
                                frameon=True, fancybox=True, shadow=False,
                                fontsize=10, ncol=3,  # 横向排列
                                handlelength=0.5, borderpad=0.6,
                                labelspacing=0.8, handletextpad=0.5,
                                columnspacing=1.5)

        # 设置背景样式
        legend.get_frame().set_facecolor(colors["panel_bg"])
        legend.get_frame().set_alpha(0.95)
        legend.get_frame().set_linewidth(0)
        legend.get_frame().set_edgecolor('none')

        # 设置文字样式
        for text in legend.get_texts():
            text.set_color(colors["text"])
            text.set_fontweight('600')
            text.set_fontsize(9)

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
        edge_color = colors["up_body"] if is_up else colors["down_body"]

        body_bottom = min(item["open"], item["close"])
        body_height = max(abs(item["close"] - item["open"]), 0.08)

        rect = Rectangle((i - bar_width / 2, body_bottom), bar_width, body_height,
                          facecolor=body_fill, edgecolor=edge_color,
                          alpha=alpha, linewidth=1.2, zorder=2)
        ax.add_patch(rect)

    for period, color, lw in [(5, colors["ma5"], 2.5), (10, colors["ma10"], 2.2)]:
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
                       fontsize=9, color=colors["text_light"], rotation=30, ha='right')

    ax.yaxis.tick_right()
    ax.tick_params(axis='y', labelsize=9, colors=colors["text_light"])
    ax.grid(True, axis='y', color=colors["grid"], linestyle='--', linewidth=0.4, alpha=0.4)

    # 隐藏所有轴线 - 极简设计
    for spine in ['top', 'left', 'right', 'bottom']:
        ax.spines[spine].set_visible(False)

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
