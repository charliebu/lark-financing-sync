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

## 3. 并行信息富化 (Parallel Enrichment)
利用 `google_web_search` 或 `web_fetch` 对初筛后的每家公司进行背景搜寻。建议分批次（如每批 5 家）并行搜索：
- **必填信息**：
    - **工商全称**：务必准确，如“北京极佳视界科技有限公司”。
    - **业务/产品描述**：由 AI 根据搜索结果总结，必须控制在 **30 个汉字以内**。
    - **标签**：如“具身智能”、“半导体检测”。
    - **官网/地址**：提取准确的 URL 和办公地址。
- **兜底策略**：若搜索无果，保留 IT 桔子的原始描述并适当精简。

## 4. 构造并执行同步
1. 将处理后的数据构造为 JSON 列表，字段映射如下：
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
3. 运行同步器：
```powershell
python "company crawl/src/agent_main.py" sync_payload.json
```

## 5. 清理与反馈
- 任务完成后，删除 `sync_payload.json`。
- 向用户汇报同步结果（成功数量、主要赛道分布）。

# 核心准则
- **精简描述**：业务与产品描述必须极简，方便移动端快速阅读。
- **准确性优先**：工商全称是去重的关键，务必通过搜索校验。
- **并行加速**：使用并行搜索工具以提高同步效率。
