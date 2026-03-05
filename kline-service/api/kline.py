"""
K-Line API - Vercel Serverless Function

生成 GitHub Contributions K 线图

Usage:
    GET /api/kline?user=gaooooosh&days=90&window=7&theme=light&compact=false
"""

from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
import os

# 添加 lib 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.github_api import get_daily_contributions, fill_missing_days
from lib.kline_converter import convert_to_ohlc, add_ma_line
from lib.chart_generator import generate_kline_chart, generate_compact_kline


class handler(BaseHTTPRequestHandler):
    """Vercel Python Runtime Handler"""

    def log_message(self, format, *args):
        """禁用默认日志"""
        pass

    def do_GET(self):
        """处理 GET 请求"""
        try:
            # 解析查询参数
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)

            username = params.get('user', ['gaooooosh'])[0]
            days = int(params.get('days', ['90'])[0])
            window = int(params.get('window', ['7'])[0])
            theme = params.get('theme', ['light'])[0]
            compact = params.get('compact', ['false'])[0].lower() == 'true'
            width = int(params.get('width', ['800' if not compact else '600'][0]))
            height = int(params.get('height', ['400' if not compact else '200'][0]))

            # 验证参数
            if days < 7 or days > 365:
                days = 90
            if window < 3 or window > 21:
                window = 7
            if window % 2 == 0:
                window += 1  # 确保是奇数

            if theme not in ['light', 'dark']:
                theme = 'light'

            # 获取数据
            daily_data = get_daily_contributions(username, days)
            daily_data = fill_missing_days(daily_data, days)

            if not daily_data:
                svg_content = generate_empty_chart(f"No data for @{username}", theme, width, height)
            else:
                # 转换为 K 线数据
                ohlc_data = convert_to_ohlc(daily_data, window)

                # 添加均线
                ohlc_data = add_ma_line(ohlc_data, period=7)

                # 生成图表
                title = f"@{username}'s GitHub Contributions"
                if compact:
                    svg_content = generate_compact_kline(ohlc_data, theme, width, height)
                else:
                    svg_content = generate_kline_chart(
                        ohlc_data,
                        title=title,
                        theme=theme,
                        width=width,
                        height=height
                    )

            # 设置响应头
            self.send_response(200)
            self.send_header('Content-Type', 'image/svg+xml')
            self.send_header('Cache-Control', 'public, max-age=3600')  # 缓存1小时
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            # 发送响应
            self.wfile.write(svg_content.encode('utf-8'))

        except Exception as e:
            # 错误处理
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode('utf-8'))


# 本地测试入口
if __name__ == '__main__':
    from http.server import HTTPServer

    server = HTTPServer(('localhost', 8080), handler)
    print("Server running at http://localhost:8080")
    print("Try: http://localhost:8080/api/kline?user=gaooooosh&days=90")
    server.serve_forever()
