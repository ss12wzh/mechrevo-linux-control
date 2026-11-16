#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mrvupdate — mrv-ctl 自动更新 (纯标准库)

流程: GitHub Releases 检查最新 tag -> 语义化版本比较 -> 选择 *.deb 资产
      -> 下载到用户缓存目录 -> pkexec 调 apt 安装
设计:
  - 未授权网络只读, 只访问 api.github.com / github.com
  - 所有错误归类为 UpdateError(kind, msg), 便于 GUI 给出可读提示
  - 检查结果缓存 6 小时, 避免频繁请求触发 API 限流
"""

import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request

REPO = "ss12wzh/mechrevo-linux-control"
API_LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"
API_TAGS = f"https://api.github.com/repos/{REPO}/tags"
RELEASES_PAGE = f"https://github.com/{REPO}/releases"

CACHE_DIR = os.path.join(
    os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"), "mrv-ctl")
CACHE_FILE = os.path.join(CACHE_DIR, "update.json")
CACHE_TTL = 6 * 3600
TIMEOUT = 8
ASSET_RE = re.compile(r"^mrv-ctl_.+_all\.deb$", re.IGNORECASE)


class UpdateError(Exception):
    """kind: network | rate_limit | no_release | http | bad_json | download | install"""

    def __init__(self, kind, message):
        self.kind = kind
        self.message = message
        super().__init__(message)


def parse_version(text):
    """'v3.6.0' / '3.6.0-1' -> (3, 6, 0); 解析失败返回 None"""
    if not text:
        return None
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", str(text))
    if not m:
        return None
    return tuple(int(x) if x is not None else 0 for x in m.groups())


def _fetch_json(url, timeout=TIMEOUT):
    req = urllib.request.Request(url, headers={
        "User-Agent": "mrv-ctl-updater/1.0",
        "Accept": "application/vnd.github+json",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise UpdateError("no_release", "仓库还没有发布 Release")
        if e.code in (403, 429):
            raise UpdateError("rate_limit", "GitHub API 访问受限，请稍后再试")
        raise UpdateError("http", f"服务器返回 HTTP {e.code}")
    except urllib.error.URLError as e:
        raise UpdateError("network", f"网络不可用：{e.reason}")
    except ValueError:
        raise UpdateError("bad_json", "服务器响应不是有效 JSON")
    except Exception as e:                       # 超时等
        raise UpdateError("network", f"网络错误：{e}")


def _cache_read():
    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _cache_write(data):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        tmp = CACHE_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, CACHE_FILE)
    except OSError:
        pass


def _pick_asset(assets):
    """优先选 mrv-ctl_<ver>_all.deb; 没有则返回 None"""
    debs = [a for a in assets if ASSET_RE.match(a.get("name") or "")]
    if not debs:
        return None
    debs.sort(key=lambda a: a.get("size") or 0, reverse=True)
    return {"name": debs[0]["name"],
            "url": debs[0].get("browser_download_url"),
            "size": debs[0].get("size") or 0}


def check(current_version, force=False, timeout=TIMEOUT):
    """检查更新。
    返回 dict: available/version/tag/url/notes/asset/published/source
    网络失败抛 UpdateError; 有缓存且未过期时直接返回缓存。"""
    cache = _cache_read()
    if (not force and cache.get("info")
            and time.time() - (cache.get("ts") or 0) < CACHE_TTL):
        return cache["info"]

    info = None
    try:
        data = _fetch_json(API_LATEST, timeout)
        tag = (data.get("tag_name") or "").strip()
        version = tag.lstrip("vV")
        notes = (data.get("body") or "").strip()
        url = data.get("html_url") or RELEASES_PAGE
        info = {
            "available": False, "version": version, "tag": tag, "url": url,
            "notes": notes[:4000], "published": data.get("published_at") or "",
            "asset": _pick_asset(data.get("assets") or []), "source": "release",
        }
    except UpdateError as e:
        if e.kind != "no_release":
            raise
        # 没有 Release 时退化到 tags (没有 .deb 资产, 只能打开发布页)
        tags = _fetch_json(API_TAGS, timeout)
        if not isinstance(tags, list) or not tags:
            raise UpdateError("no_release", "仓库还没有发布任何版本")
        tag = (tags[0].get("name") or "").strip()
        info = {
            "available": False, "version": tag.lstrip("vV"), "tag": tag,
            "url": f"https://github.com/{REPO}/tree/{tag}",
            "notes": "", "published": "", "asset": None, "source": "tag",
        }

    cur = parse_version(current_version)
    new = parse_version(info["version"])
    info["available"] = bool(cur and new and new > cur)
    info["current"] = current_version
    _cache_write({"ts": time.time(), "info": info})
    return info


def download(url, dest, progress=None, timeout=60):
    """下载资产到 dest; progress(done, total) 回调 (total 可能为 0)。返回 dest"""
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "mrv-ctl-updater/1.0"})
    tmp = dest + ".part"
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r, open(tmp, "wb") as f:
            total = int(r.headers.get("Content-Length") or 0)
            done = 0
            while True:
                chunk = r.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if progress:
                    try:
                        progress(done, total)
                    except Exception:
                        pass
        os.replace(tmp, dest)
        return dest
    except UpdateError:
        raise
    except Exception as e:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise UpdateError("download", f"下载失败：{e}")


def install_deb(path):
    """通过 pkexec 调 apt 安装 (会弹系统授权框); 返回 (ok, 输出文本)"""
    if not os.path.exists(path):
        raise UpdateError("install", "更新包不存在")
    try:
        r = subprocess.run(
            ["pkexec", "/usr/bin/apt-get", "install", "-y", "--reinstall", path],
            capture_output=True, text=True, timeout=600)
    except FileNotFoundError:
        raise UpdateError("install", "找不到 pkexec，请手动执行：sudo apt install " + path)
    except subprocess.TimeoutExpired:
        raise UpdateError("install", "安装超时，请手动安装 " + path)
    if r.returncode != 0:
        msg = (r.stderr or r.stdout or "").strip().splitlines()
        raise UpdateError("install", "安装失败：" + (msg[-1] if msg else f"退出码 {r.returncode}"))
    return True, (r.stdout or "").strip()


def open_release_page(url=None):
    """用系统默认浏览器打开发布页"""
    try:
        subprocess.Popen(["xdg-open", url or RELEASES_PAGE],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except OSError:
        return False
