import os
import json
import requests
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

class XCrawlClient:
    """仅负责 RSS 数据获取，以及执行搜索"""
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("XCRAWL_API_KEY")
        self.base_url = "https://run.xcrawl.com/v1"

    def fetch_itjuzi_rss(self) -> List[Dict[str, str]]:
        """获取 IT 桔子最新的融资快讯"""
        url = "https://www.itjuzi.com/api/telegraph.xml"
        try:
            response = requests.get(url, timeout=20)
            root = ET.fromstring(response.content)
            results = []
            for item in root.findall('.//item'):
                results.append({
                    "title": item.find('title').text,
                    "url": item.find('link').text,
                    "description": item.find('description').text
                })
            return results
        except Exception as e:
            print(f"IT 桔子 RSS 获取失败: {e}")
            return []

    def search_web(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        endpoint = f"{self.base_url}/search"
        payload = {"query": query, "limit": limit, "location": "CN", "language": "zh"}
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                # 返回包含 title, url, snippet 的列表
                return response.json().get("data", {}).get("data", [])
            return []
        except Exception as e:
            print(f"搜索失败: {e}")
            return []

class FeishuClient:
    def __init__(self, app_id: str = None, app_secret: str = None):
        self.app_id = app_id or os.getenv("FEISHU_APP_ID")
        self.app_secret = app_secret or os.getenv("FEISHU_APP_SECRET")
        self.token = self._get_tenant_access_token()

    def _get_tenant_access_token(self):
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = {"app_id": self.app_id, "app_secret": self.app_secret}
        response = requests.post(url, json=payload)
        return response.json().get("tenant_access_token")

    def list_bitable_records(self, app_token: str, table_id: str, filter_query: str = None):
        """列出所有记录，支持过滤"""
        headers = {"Authorization": f"Bearer {self.token}"}
        all_items = []
        page_token = ""
        while True:
            url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
            params = {"page_size": 100, "page_token": page_token}
            if filter_query:
                params["filter"] = filter_query
            res = requests.get(url, headers=headers, params=params).json()
            data = res.get("data", {})
            all_items.extend(data.get("items", []))
            page_token = data.get("page_token", "")
            if not page_token:
                break
        return all_items

    def update_bitable_record(self, app_token: str, table_id: str, record_id: str, fields: Dict[str, Any]):
        """更新单条记录"""
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        return requests.put(url, headers=headers, json={"fields": fields}).json()

    def upsert_bitable_record(self, app_token: str, table_id: str, fields: Dict[str, Any]):
        """
        [终极加固版] 通过全量拉取 数据源链接 进行本地判重，确保每条快讯唯一
        """
        source_url = fields.get("数据源链接", {}).get("link", "")
        if not source_url: return {"code": -1, "msg": "缺少数据源链接"}
        
        # 1. 翻页拉取当前表的所有记录
        headers = {"Authorization": f"Bearer {self.token}"}
        all_items = []
        page_token = ""
        
        try:
            while True:
                list_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
                params = {"page_size": 100, "page_token": page_token}
                res = requests.get(list_url, headers=headers, params=params).json()
                data = res.get("data", {})
                all_items.extend(data.get("items", []))
                page_token = data.get("page_token", "")
                if not page_token:
                    break
            
            target_record_id = None
            
            for item in all_items:
                # 获取该记录的数据源链接 URL
                curr_url = item.get("fields", {}).get("数据源链接", {}).get("link", "")
                if curr_url == source_url:
                    target_record_id = item.get("record_id")
                    break
            
            if target_record_id:
                # 2. 已存在，执行更新 (不更新创建时间)
                update_fields = fields.copy()
                if "创建时间" in update_fields:
                    del update_fields["创建时间"]
                
                update_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{target_record_id}"
                return requests.put(update_url, headers=headers, json={"fields": update_fields}).json()
            else:
                # 3. 不存在，执行新增
                add_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
                return requests.post(add_url, headers=headers, json={"fields": fields}).json()
        except Exception as e:
            return {"code": -1, "msg": str(e)}

    def delete_all_records(self, app_token: str, table_id: str):
        """清空表格"""
        list_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records?page_size=100"
        headers = {"Authorization": f"Bearer {self.token}"}
        res_data = requests.get(list_url, headers=headers).json()
        items = res_data.get("data", {}).get("items", [])
        record_ids = [item["record_id"] for item in items]
        if record_ids:
            delete_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_delete"
            requests.post(delete_url, headers=headers, json={"records": record_ids})
            print(f"成功删除 {len(record_ids)} 条记录。")
            return True
        return False
