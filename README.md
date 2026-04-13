# Lark Financing Sync Agent Skill

一个为 Gemini CLI 设计的智能化融资信息同步插件。该插件能够自动抓取 IT 桔子最新的国内融资动态，利用 AI 实时搜寻补全企业工商全称、官网及业务背景，并结构化同步至飞书多维表格。

## 🚀 核心特性

- **自动采集**：基于 IT 桔子公开 RSS 订阅，实时获取最新融资快讯。
- **智能过滤**：AI 自动识别并保留国内初创融资（天使轮、A/B/C轮）及拟收购项目，过滤海外及后期干扰。
- **并行富化**：调用 `google_web_search` 并行补齐工商全称、官网、详细地址。
- **极简摘要**：AI 自动精炼业务描述与产品核心，严格控制在 30 字以内，完美适配移动端。
- **去重同步**：依赖底层 `upsert` 逻辑，基于数据源链接进行判重，确保 Bitable 数据不重复。

## 📦 安装说明

### 1. 环境准备
确保您的开发环境已安装以下依赖：
- **Python 3.10+**
- **Feishu Bitable**：需在飞书开发者后台创建应用并获取 `APP_ID`, `APP_SECRET`。

### 2. 安装 Skill
您可以直接从 GitHub 安装此 Skill：
```bash
gemini skills install https://github.com/charliebu/lark-financing-sync.git --scope user
```
安装完成后，请在 Gemini CLI 中执行 `/skills reload` 以加载。

## ⚙️ 配置要求

在您的项目根目录或 Skill 目录下确保存在 `.env` 文件，包含以下飞书 API 配置：
```env
FEISHU_APP_ID="your_app_id"
FEISHU_APP_SECRET="your_app_secret"
FEISHU_APP_TOKEN="your_bitable_token"
FEISHU_TABLE_ID="your_table_id"
```

## 🛠️ 使用方法

在 Gemini CLI 会话中，您可以输入以下指令触发：

- “同步融资快讯”
- “跑一遍融资信息”
- “更新今天的融资动态”

Skill 会自动执行 **抓取 -> 过滤 -> 搜索补全 -> 写入飞书** 的全流程。

## 📂 目录结构

```text
lark-financing-sync/
├── SKILL.md          # 插件核心逻辑与指令说明
├── README.md         # 项目文档
└── .gitignore        # Git 忽略配置
```

## 📄 开源协议

[MIT License](LICENSE)
