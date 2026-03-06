"""
统计数据 API - Vercel Serverless Function

返回 GitHub Contributions 统计数据（JSON 格式）

Usage:
    GET /api/stats?user=gaooooosh&days=90
"""

import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import sys
import os

# 添加 lib 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.github_api import get_daily_contributions, fill_missing_days


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

            # 验证参数
            if days < 7 or days > 365:
                days = 90

            # 获取数据
            daily_data = get_daily_contributions(username, days)
            daily_data = fill_missing_days(daily_data, days)

            if not daily_data:
                stats = {
                    "username": username,
                    "error": "No data available"
                }
            else:
                # 计算统计数据
                today = datetime.now().date()

                # 昨日提交量
                yesterday = today - timedelta(days=1)
                yesterday_data = [d for d in daily_data if d['date'] == yesterday.strftime('%Y-%m-%d')]
                yesterday_count = yesterday_data[0]['count'] if yesterday_data else 0

                # 本月数据
                current_month = today.month
                current_year = today.year
                month_data = [d for d in daily_data
                              if datetime.strptime(d['date'], '%Y-%m-%d').month == current_month
                              and datetime.strptime(d['date'], '%Y-%m-%d').year == current_year]

                # 本月平均提交量
                month_avg = sum(d['count'] for d in month_data) / len(month_data) if month_data else 0

                # 本月总提交量
                month_total = sum(d['count'] for d in month_data)

                # 今日提交量
                today_data = [d for d in daily_data if d['date'] == today.strftime('%Y-%m-%d')]
                today_count = today_data[0]['count'] if today_data else 0

                # 涨跌计算（对比昨日）
                change = today_count - yesterday_count
                change_pct = (change / yesterday_count * 100) if yesterday_count > 0 else 0

                stats = {
                    "username": username,
                    "today": today_count,
                    "yesterday": yesterday_count,
                    "month": {
                        "average": round(month_avg, 1),
                        "total": month_total,
                        "days": len(month_data)
                    },
                    "change": {
                        "value": change,
                        "percentage": round(change_pct, 1)
                    }
                }

            # 设置响应头
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'public, max-age=1800')  # 缓存30分钟
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            # 发送响应
            self.wfile.write(json.dumps(stats, ensure_ascii=False, indent=2).encode('utf-8'))

        except Exception as e:
            # 错误处理
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({"error": str(e)}, ensure_ascii=False)
            self.wfile.write(error_response.encode('utf-8'))


# 本地测试入口
if __name__ == '__main__':
    from http.server import HTTPServer

    server = HTTPServer(('localhost', 8081), handler)
    print("Stats API running at http://localhost:8081")
    print("Try: http://localhost:8081/api/stats?user=gaooooosh&days=90")
    server.serve_forever()
