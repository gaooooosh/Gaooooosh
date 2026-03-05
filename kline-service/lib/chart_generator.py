"""
专业 K 线图生成模块

生成符合中国股市习惯的专业 K 线图（红涨绿跌）
"""

import io
from typing import List, Dict
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


# 统一配色 - 亮/暗主题只是颜色不同，布局完全一致
THEMES = {
    "light": {
        "bg": "#FFFFFF",
        "panel_bg": "#FAFAFA",
        "text": "#1A1A1A",
        "text_light": "#666666",
        "grid": "#E5E5E5",
        "up_body": "#DC2626",      # 阳线 - 红色
        "down_body": "#059669",    # 阴线 - 绿色
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
    title: str = "GitHub Contributions K-Line",
    theme: str = "light",
    width: int = 900,
    height: int = 450,
    show_volume: bool = True
) -> str:
    """生成专业风格 K 线图"""
    if not ohlc_data:
        return generate_empty_chart(title, theme, width, height)

    colors = THEMES.get(theme, THEMES["light"])
    dpi = 120

    # 创建图表
    fig = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi)

    # 布局：标题 + 主图 + 成交量
    if show_volume:
        gs = fig.add_gridspec(3, 1, height_ratios=[0.4, 3.5, 1], hspace=0.05)
        ax_title = fig.add_subplot(gs[0])
        ax_main = fig.add_subplot(gs[1])
        ax_vol = fig.add_subplot(gs[2])
    else:
        gs = fig.add_gridspec(2, 1, height_ratios=[0.4, 4], hspace=0.05)
        ax_title = fig.add_subplot(gs[0])
        ax_main = fig.add_subplot(gs[1])
        ax_vol = None

    # 背景色
    fig.patch.set_facecolor(colors["bg"])
    ax_title.set_facecolor(colors["bg"])
    ax_main.set_facecolor(colors["panel_bg"])
    if ax_vol:
        ax_vol.set_facecolor(colors["panel_bg"])

    n = len(ohlc_data)
    dates = [datetime.strptime(d["date"], "%Y-%m-%d") for d in ohlc_data]
    bar_width = max(0.5, min(0.85, 25 / n))

    # ========== 绘制 K 线（无影线）==========
    for i, item in enumerate(ohlc_data):
        is_up = item["close"] >= item["open"]
        body_fill = colors["up_body"] if is_up else colors["down_body"]
        alpha = colors["up_alpha"] if is_up else colors["down_alpha"]

        body_bottom = min(item["open"], item["close"])
        body_height = max(abs(item["close"] - item["open"]), 0.08)

        rect = Rectangle(
            (i - bar_width / 2, body_bottom),
            bar_width, body_height,
            facecolor=body_fill,
            edgecolor='none',
            alpha=alpha,
            linewidth=0,
            zorder=2
        )
        ax_main.add_patch(rect)

    # ========== 绘制均线（突出）==========
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

    # ========== 绘制成交量 ==========
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
                (i - vol_width / 2, 0),
                vol_width, max(vol, 0.1),
                facecolor=vol_color,
                edgecolor='none',
                alpha=0.6,
                zorder=1
            )
            ax_vol.add_patch(rect)

    # ========== 坐标轴设置 ==========
    max_price = max(d["high"] for d in ohlc_data)
    ax_main.set_xlim(-1, n)
    ax_main.set_ylim(0, max_price * 1.15)

    # X轴刻度
    tick_interval = max(1, n // 8)
    tick_positions = list(range(0, n, tick_interval))
    if tick_positions and tick_positions[-1] != n - 1:
        tick_positions.append(n - 1)

    ax_main.set_xticks(tick_positions)
    ax_main.set_xticklabels([])

    # Y轴在右侧
    ax_main.yaxis.tick_right()
    ax_main.yaxis.set_label_position("right")
    ax_main.tick_params(axis='y', labelsize=9, colors=colors["text_light"])
    ax_main.set_ylabel("Contributions", fontsize=10, color=colors["text_light"], labelpad=10)

    # 网格
    ax_main.grid(True, axis='y', color=colors["grid"], linestyle='-', linewidth=0.8, alpha=0.9)
    ax_main.set_axisbelow(True)

    # 边框
    for spine in ['top', 'left']:
        ax_main.spines[spine].set_visible(False)
    ax_main.spines['right'].set_color(colors["axis_line"])
    ax_main.spines['bottom'].set_color(colors["axis_line"])

    # 成交量图设置
    if ax_vol:
        ax_vol.set_xlim(-1, n)
        ax_vol.set_ylim(0, max_vol * 1.2)
        ax_vol.set_xticks(tick_positions)
        ax_vol.set_xticklabels([dates[i].strftime("%m-%d") for i in tick_positions],
                               fontsize=9, color=colors["text_light"])
        ax_vol.yaxis.tick_right()
        ax_vol.tick_params(axis='y', labelsize=8, colors=colors["text_light"])

        for spine in ['top', 'left', 'right']:
            ax_vol.spines[spine].set_visible(False)
        ax_vol.spines['bottom'].set_color(colors["axis_line"])
        ax_vol.grid(True, axis='y', color=colors["grid"], linestyle='--', linewidth=0.5, alpha=0.6)

    # ========== 标题区域 ==========
    ax_title.axis('off')

    latest = ohlc_data[-1]
    change = latest["close"] - latest["open"]
    change_pct = (change / latest["open"] * 100) if latest["open"] > 0 else 0
    change_color = colors["up_body"] if change >= 0 else colors["down_body"]
    sign = "+" if change >= 0 else ""

    ax_title.text(0.01, 0.8, title, fontsize=14, fontweight='bold',
                  color=colors["text"], transform=ax_title.transAxes, va='center')
    ax_title.text(0.01, 0.2, f"最新: {latest['close']:.1f}  {sign}{change:.1f} ({sign}{change_pct:.1f}%)",
                  fontsize=11, color=change_color, transform=ax_title.transAxes, va='center')

    # 图例
    if n >= 5:
        legend = ax_main.legend(loc='upper left', frameon=True, fontsize=10,
                                fancybox=False, edgecolor=colors["border"], framealpha=0.95)
        legend.get_frame().set_facecolor(colors["panel_bg"])
        for text in legend.get_texts():
            text.set_color(colors["text"])
            text.set_fontweight('500')

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

    # 均线
    for period, color, lw in [(5, colors["ma5"], 2.0), (10, colors["ma10"], 1.6)]:
        if n >= period:
            ma = calculate_ma(ohlc_data, period)
            valid_x = [i for i, v in enumerate(ma) if v is not None]
            valid_y = [ma[i] for i in valid_x]
            ax.plot(valid_x, valid_y, color=color, linewidth=lw, alpha=0.95, zorder=10)

    max_val = max(d["high"] for d in ohlc_data)
    ax.set_xlim(-0.5, n - 0.5)
    ax.set_ylim(0, max_val * 1.15)

    tick_step = max(1, n // 6)
    tick_pos = list(range(0, n, tick_step))
    ax.set_xticks(tick_pos)
    ax.set_xticklabels([dates[i].strftime("%m/%d") for i in tick_pos],
                       fontsize=8, color=colors["text_light"])

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

    ax.text(0.5, 0.5, '📊 暂无贡献数据', ha='center', va='center',
            fontsize=14, color=colors["text_light"], fontweight=500)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    buffer = io.StringIO()
    plt.savefig(buffer, format='svg', facecolor=fig.get_facecolor(),
                edgecolor='none', bbox_inches='tight')
    plt.close(fig)

    return buffer.getvalue()
