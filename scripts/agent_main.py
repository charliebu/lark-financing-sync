import os
import json
import datetime
import sys
from dotenv import load_dotenv

# Path management
sys.path.append(os.path.join(os.getcwd(), "company crawl", "src"))
from core import FeishuClient

load_dotenv("company crawl/.env")

def standardize_city(city: str) -> str:
    """确保城市名称格式正确，且补齐'市'后缀"""
    if not city or city == "未知":
        return "未知"
    
    # 省份黑名单，防止出现“浙江市”这种错误
    provinces = ["北京", "上海", "天津", "重庆", "河北", "山西", "辽宁", "吉林", "黑龙江", "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北", "湖南", "广东", "海南", "四川", "贵州", "云南", "陕西", "甘肃", "青海", "台湾", "内蒙古", "广西", "西藏", "宁夏", "新疆", "香港", "澳门"]
    
    # 如果只有省份名，保留原样（或特殊处理，此处暂不强加“市”）
    if city in provinces:
        # 直辖市补齐“市”
        if city in ["北京", "上海", "天津", "重庆"]:
            return f"{city}市"
        return city

    # 复合路径处理（如“杭州/北京/深圳”），递归处理每一段
    if "/" in city:
        parts = [standardize_city(p.strip()) for p in city.split("/")]
        return "/".join(parts)

    # 如果已经有完整行政后缀，直接返回
    # 注意：'州' 比较特殊，苏州/杭州等需要补'市'，但'自治州'不需要
    if city.endswith("市") or city.endswith("自治州") or city.endswith("地区") or city.endswith("盟") or city.endswith("区") or city.endswith("县"):
        return city
    
    # 针对杭州、苏州、广州等以'州'结尾的城市名（通常为2个字）
    if city.endswith("州") and len(city) <= 3:
         return f"{city}市"

    return f"{city}市"

def sync_to_feishu(json_data: str):
    """
    接收 Agent 准备好的 JSON 字符串并推送到推送到飞书
    """
    fs = FeishuClient()
    app_token = os.getenv("FEISHU_APP_TOKEN")
    table_id = os.getenv("FEISHU_TABLE_ID")

    try:
        data_list = json.loads(json_data)
    except Exception as e:
        print(f"❌ JSON 解析失败: {e}")
        return

    print(f"🚀 正在同步 {len(data_list)} 家公司到飞书...")

    success_count = 0
    for entry in data_list:
        # 确保类型是列表
        tags = entry.get("company_type", ["初创项目"])
        if isinstance(tags, str): tags = [tags]

        city = standardize_city(entry.get("city", "未知"))

        now_ts = int(datetime.datetime.now().timestamp() * 1000)
        fields = {
            "企业名称(全称)": entry.get("full_name"),
            "企业简称": entry.get("short_name"),
            "企业类型": tags,
            "主要业务": str(entry.get("business", ""))[:30],
            "主要产品": str(entry.get("products", ""))[:30],
            "企业城市": city,
            "公司地址": entry.get("address", "无数据"),
            "公司网站": {"text": "官方网站", "link": entry.get("website", "")},
            "数据源链接": {"text": "IT桔子快讯", "link": entry.get("source_url", "")},
            "融资信息": entry.get("financing_info", ""),
            "创建时间": now_ts,
            "更新日期": now_ts
        }

        
        res = fs.upsert_bitable_record(app_token, table_id, fields)
        if res.get("code") == 0:
            print(f"   ✅ 同步成功: {fields['企业名称(全称)']}")
            success_count += 1
        else:
            print(f"   ❌ 同步失败: {fields['企业名称(全称)']} - {res.get('msg')}")

    print(f"\n✨ 任务完成！成功同步 {success_count} 家公司。")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.endswith(".json") and os.path.exists(arg):
            with open(arg, "r", encoding="utf-8") as f:
                sync_to_feishu(f.read())
        else:
            sync_to_feishu(arg)
    else:
        print("请提供 JSON 数据或 JSON 文件路径作为参数。")
