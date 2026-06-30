"""
微信公众号 API 客户端

API 文档: https://developers.weixin.qq.com/doc/offiaccount/

个人订阅号可用接口:
  - token         获取 access_token
  - draft/add     创建草稿
  - draft/get     获取草稿列表
  - draft/delete  删除草稿
  - freepublish/submit  发布草稿 (每天1次, 个人号不可用)
  - material/add_material  上传图片素材
"""

import os
import time
import json
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_URL = "https://api.weixin.qq.com/cgi-bin"


class WeChatAPI:
    def __init__(self, appid: str = None, appsecret: str = None):
        self.appid = appid or os.getenv("WECHAT_APPID", "")
        self.appsecret = appsecret or os.getenv("WECHAT_APPSECRET", "")
        self._access_token = None
        self._token_expires = 0

    def get_access_token(self) -> str:
        """获取 access_token，自动缓存"""
        if self._access_token and time.time() < self._token_expires:
            return self._access_token

        url = f"{BASE_URL}/token"
        resp = requests.get(url, params={
            "grant_type": "client_credential",
            "appid": self.appid,
            "secret": self.appsecret,
        })
        data = resp.json()
        if "access_token" not in data:
            raise Exception(f"获取 access_token 失败: {data}")

        self._access_token = data["access_token"]
        self._token_expires = time.time() + data.get("expires_in", 7200) - 300
        return self._access_token

    def upload_cover_image(self, image_path: str) -> str:
        """
        上传封面图素材，返回 media_id。
        支持: jpg, png (<=10MB)
        对应 API: material/add_material
        """
        token = self.get_access_token()
        url = f"{BASE_URL}/material/add_material?access_token={token}&type=image"

        abs_path = Path(image_path)
        if not abs_path.is_absolute():
            abs_path = Path.cwd() / abs_path

        with open(abs_path, "rb") as f:
            resp = requests.post(url, files={"media": (abs_path.name, f)})

        data = resp.json()
        if "media_id" not in data:
            raise Exception(f"上传封面图素材失败: {data}")

        return data["media_id"]

    def upload_article_image(self, image_path: str) -> str:
        """
        上传文章内图片，返回可直接嵌入 <img src=""> 的 URL。
        对应 API: media/uploadimg（不是 material/add_material）
        """
        token = self.get_access_token()
        url = f"{BASE_URL}/media/uploadimg?access_token={token}"

        abs_path = Path(image_path)
        if not abs_path.is_absolute():
            abs_path = Path.cwd() / abs_path

        with open(abs_path, "rb") as f:
            resp = requests.post(url, files={"media": (abs_path.name, f)})

        data = resp.json()
        if "url" not in data:
            raise Exception(f"上传文章图片失败: {data}")

        return data["url"]

    def create_draft(self, title: str, content: str, thumb_media_id: str = None) -> str:
        """
        创建草稿。
        content 必须是微信公众号兼容的 HTML。
        返回 media_id。
        """
        token = self.get_access_token()
        url = f"{BASE_URL}/draft/add?access_token={token}"

        articles = [{
            "title": title,
            "author": "函关骑牛",
            "content": content,
            "content_source_url": "",
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
            "copyright_type": 1,
            "copyright_author": "函关骑牛",
            "copyright_source_url": "",
            "statement_type": "个人观点，仅供参考",
            "need_open_recommend": 1,
            "need_open_reward": 1,
            "reward_wording": "感谢支持",
        }]
        if thumb_media_id:
            articles[0]["thumb_media_id"] = thumb_media_id

        payload = {"articles": articles}
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        resp = requests.post(
            url,
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        data = resp.json()

        if "media_id" not in data:
            raise Exception(f"创建草稿失败: {data}")

        return data["media_id"]

    def delete_draft(self, media_id: str) -> dict:
        """删除草稿"""
        token = self.get_access_token()
        url = f"{BASE_URL}/draft/delete?access_token={token}"
        body = json.dumps({"media_id": media_id}, ensure_ascii=False).encode("utf-8")
        resp = requests.post(
            url,
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        data = resp.json()
        if data.get("errcode") != 0:
            raise Exception(f"删除草稿失败: {data}")
        return data

    def publish_draft(self, media_id: str) -> dict:
        """
        发布草稿（「自由发布」接口）。
        个人订阅号每天只能调用 1 次（通常返回 48001）。
        """
        token = self.get_access_token()
        url = f"{BASE_URL}/freepublish/submit?access_token={token}"

        payload = {"media_id": media_id}
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        resp = requests.post(
            url,
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        data = resp.json()

        if data.get("errcode") != 0:
            errmsg = data.get("errmsg", str(data))
            raise Exception(f"发布失败: {errmsg} (errcode={data.get('errcode')})")

        return {"publish_id": data.get("publish_id", ""), "msg_data_id": data.get("msg_data_id", [])}

    def check_permissions(self) -> dict:
        """检查当前账号有哪些 API 权限"""
        token = self.get_access_token()

        results = {}
        try:
            url = f"{BASE_URL}/draft/count?access_token={token}"
            resp = requests.get(url)
            data = resp.json()
            results["draft_count"] = "ok" if data.get("errcode") == 0 else data
        except Exception as e:
            results["draft_count"] = str(e)

        try:
            url = f"{BASE_URL}/freepublish/batchget?access_token={token}"
            resp = requests.post(url, json={"offset": 0, "count": 1})
            data = resp.json()
            results["freepublish"] = "ok" if data.get("errcode") == 0 else data
        except Exception as e:
            results["freepublish"] = str(e)

        return results


def load_env(env_path: str = None):
    """加载凭据。默认从 MCP 目录 .env 读取。"""
    if env_path is None:
        env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(str(env_path))


__all__ = ["WeChatAPI", "load_env"]
