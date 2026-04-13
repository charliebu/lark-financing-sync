---
name: lark-financing-sync
description: 自动抓取 IT 桔子国内融资快讯，并通过 AI 实时搜寻补齐工商、官网、地址等信息后同步至飞书多维表格。
---

# Lark Financing Sync 工作流

当用户请求“同步融资快讯”、“跑一遍融资信息”或类似指令时，请严格遵循以下步骤：

## 1. 原始数据采集
运行以下命令获取 IT 桔子最新的原始快讯（前 50 条），无需 XCrawl API Key：
```powershell
python -c "import requests, xml.etree.ElementTree as ET, json; url='https://www.itjuzi.com/api/telegraph.xml'; r=requests.get(url, timeout=20); root=ET.fromstring(r.content); results=[{'title': item.find('title').text, 'url': item.find('link').text, 'description': item.find('description').text} for item in root.findall('.//item')[:50]]; print(json.dumps(results, ensure_ascii=False))"
```

## 2. 深度过滤与项目识别
对采集到的结果进行以下处理：
- **目标识别**：仅保留国内初创融资（天使轮、A/B/C轮）、拟收购（M&A）项目。
- **关键词过滤**：剔除包含 `Inc, LLC, India, Ltd (非China), 获得战略投资 (非初创), 拟上市, 递交招股书` 等关键词的海外或成熟期项目。
- **去重准备**：记录原始简称和 `url`。
## 3. 分布式富化与批次控制 (Optimization)
为了避免触发 API 频率限制或上下文过载，**严禁一次性处理超过 10 个项目**。请遵循以下策略：
- **小规模 (<=5个)**：直接在当前会话通过并行搜索处理。
- **大规模 (>5个)**：必须调用 `generalist` 子代理。
    - **指令示例**：`“调用 generalist 帮我处理这 10 个融资项目的搜索富化，每批处理 5 个，最后返回一个标准的 JSON 列表。”`
- **搜索优化**：
    - 优先检查 IT 桔子描述，若已包含“全称”和“官网”，则跳过该公司的搜索。
    - 搜索时将“官网”与“工商信息”合并为一个查询（例如：`“公司名 官网 工商全称”`）。

## 4. 构造并执行同步
1. 将处理后的数据构造为 JSON 列表，字段映射如下：
...

    - `full_name`: 工商全称
    - `short_name`: 原始简称
    - `company_type`: 类型标签列表
    - `business`: 精炼业务 (<30字)
    - `products`: 核心产品 (<30字)
    - `city`: 城市名 (需补齐“市”后缀)
    - `address`: 详细地址
    - `website`: 官网 URL
    - `source_url`: 原始快讯链接
    - `financing_info`: 融资轮次金额信息
2. 保存为 `sync_payload.json`。
3. 运行同步器（使用 Skill 目录下 `scripts/` 中的脚本）：
```powershell
python "scripts/agent_main.py" sync_payload.json
```

## 5. 清理与反馈
- 任务完成后，删除 `sync_payload.json`。
- 向用户汇报同步结果（成功数量、主要赛道分布）。

# 核心准则
- **精简描述**：业务与产品描述必须极简，方便移动端快速阅读。
- **准确性优先**：工商全称是去重的关键，务必通过搜索校验。
- **并行加速**：使用并行搜索工具以提高同步效率。
