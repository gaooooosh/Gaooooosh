# GitHub Contributions K-Line Service

将 GitHub Contributions 数据以股票 K 线图（蜡烛图）形式展示的服务。

## 特性

- 📊 **K线图可视化** - 将每日贡献转换为股票风格的蜡烛图
- 🎨 **双主题支持** - 支持亮色/暗色主题
- 📱 **响应式** - 可自定义尺寸
- ⚡ **Serverless** - 部署在 Vercel，快速响应
- 🔄 **滑动窗口算法** - 平滑展示贡献趋势

## API 使用

```
GET /api/kline?user=<username>&days=<days>&window=<window>&theme=<theme>
```

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `user` | string | `gaooooosh` | GitHub 用户名 |
| `days` | int | `90` | 显示最近多少天 (7-365) |
| `window` | int | `7` | 滑动窗口大小 (3-21, 奇数) |
| `theme` | string | `light` | 主题: `light` 或 `dark` |
| `compact` | bool | `false` | 紧凑模式 |
| `width` | int | `800` | 图片宽度 |
| `height` | int | `400` | 图片高度 |

### 示例

```markdown
<!-- 基本用法 -->
![K-Line](https://your-app.vercel.app/api/kline?user=gaooooosh)

<!-- 暗色主题 -->
![K-Line Dark](https://your-app.vercel.app/api/kline?user=gaooooosh&theme=dark)

<!-- 紧凑模式 -->
![K-Line Compact](https://your-app.vercel.app/api/kline?user=gaooooosh&compact=true)
```

## K 线数据模型

使用滑动窗口算法，以每天为基准，取前后各 3 天（共 7 天）的数据：

```
Day:    -3   -2   -1    0   +1   +2   +3
        │    │    │    │    │    │    │
        └────┴────┴────┴────┴────┴────┘
              Open  ────────► Close
              │               │
              └── High / Low ─┘
```

- **Open**: 窗口起始日 contributions
- **High**: 窗口内最大 contributions
- **Low**: 窗口内最小 contributions
- **Close**: 窗口结束日 contributions

## 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 本地测试
python api/kline.py

# 访问
open http://localhost:8080/api/kline?user=gaooooosh
```

## 部署到 Vercel

1. Fork 此仓库
2. 在 Vercel 中导入项目
3. 部署完成！

## 文件结构

```
kline-service/
├── api/
│   └── kline.py              # API 入口
├── lib/
│   ├── __init__.py
│   ├── github_api.py         # GitHub 数据获取
│   ├── kline_converter.py    # K 线转换算法
│   └── chart_generator.py    # 图表生成
├── requirements.txt          # Python 依赖
├── vercel.json               # Vercel 配置
└── README.md                 # 本文件
```

## 技术栈

- **Python 3.9+**
- **matplotlib** - 图表生成
- **requests** - HTTP 请求
- **numpy** - 数据处理

## License

MIT
