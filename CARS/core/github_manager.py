import os
import base64
import hashlib
import requests
from datetime import datetime


class GitHubManager:
    def __init__(self, repo_owner: str, repo_name: str, token: str, branch: str = "main"):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.token = token
        self.branch = branch
        self.api_base = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.report = []
        self._remote_tree = {}

    def test_connection(self) -> bool:
        try:
            resp = requests.get(self.api_base, headers=self.headers, timeout=10)
            return resp.status_code == 200
        except:
            return False

    def _fetch_remote_tree(self):
        """Tüm repo ağacını (path → blob SHA) tek istekte al."""
        url = f"{self.api_base}/git/trees/{self.branch}?recursive=1"
        try:
            resp = requests.get(url, headers=self.headers, timeout=30)
            if resp.status_code == 200:
                tree = resp.json().get("tree", [])
                self._remote_tree = {
                    item["path"]: item["sha"]
                    for item in tree
                    if item["type"] == "blob"
                }
                self.report.append(f"✓ Repo ağacı alındı ({len(self._remote_tree)} dosya)")
            else:
                self.report.append("⚠️ Repo ağacı alınamadı, tüm dosyalar yüklenecek.")
                self._remote_tree = {}
        except Exception as e:
            self.report.append(f"⚠️ Ağaç hatası: {e}")
            self._remote_tree = {}

    @staticmethod
    def _compute_local_blob_sha(file_path: str) -> str:
        """Git blob SHA1'ini hesapla (blob <boyut>\0<veri>)."""
        if not os.path.exists(file_path):
            return ""
        with open(file_path, "rb") as f:
            content = f.read()
        header = f"blob {len(content)}\0".encode("utf-8")
        return hashlib.sha1(header + content).hexdigest()

    def push_file(self, local_path: str, repo_path: str, commit_msg: str = None) -> bool:
        """Dosyayı yalnızca değiştiyse yükle."""
        if not os.path.exists(local_path):
            self.report.append(f"⚠️ Bulunamadı: {repo_path}")
            return False

        # Uzak blob SHA (repo ağacından)
        remote_blob_sha = self._remote_tree.get(repo_path, "")

        # Yerel blob SHA hesapla
        local_blob_sha = self._compute_local_blob_sha(local_path)

        # Değişiklik yoksa atla
        if remote_blob_sha and local_blob_sha == remote_blob_sha:
            self.report.append(f"⊙ {repo_path} (değişmedi)")
            return True

        # Yükle
        with open(local_path, "rb") as f:
            content = f.read()
        content_b64 = base64.b64encode(content).decode("utf-8")

        url = f"{self.api_base}/contents/{repo_path}"
        body = {
            "message": commit_msg or f"Update {repo_path}",
            "content": content_b64,
            "branch": self.branch
        }
        if remote_blob_sha:
            body["sha"] = remote_blob_sha  # mevcut dosyanın SHA'sı (update için gerekli)

        resp = requests.put(url, headers=self.headers, json=body)
        if resp.status_code in (200, 201):
            self.report.append(f"✓ {repo_path}")
            # Ağacı güncelle (yeni SHA)
            new_sha = resp.json().get("content", {}).get("sha", "")
            if new_sha:
                self._remote_tree[repo_path] = new_sha
            return True
        else:
            self.report.append(f"✗ {repo_path} - HTTP {resp.status_code}")
            return False

    def push_directory(self, local_dir: str, repo_dir: str):
        """Klasördeki tüm dosyaları (sadece değişenleri) yükle."""
        if not os.path.exists(local_dir):
            return
        for root, dirs, files in os.walk(local_dir):
            for file in files:
                local_path = os.path.join(root, file)
                rel_path = os.path.relpath(local_path, local_dir)
                repo_path = f"{repo_dir}/{rel_path}".replace("\\", "/")
                self.push_file(local_path, repo_path)

    def full_sync(self, data_dir: str):
        """Hızlı tam senkronizasyon."""
        self.report = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Repo ağacını al (tek istek)
        self._fetch_remote_tree()

        # 2. data.json
        json_path = os.path.join(data_dir, "data.json")
        if os.path.exists(json_path):
            self.push_file(json_path, "data.json", f"Veri güncellemesi - {timestamp}")
        else:
            self.report.append("⚠️ data.json bulunamadı")

        # 3. Görseller
        self.push_directory(os.path.join(data_dir, "brands"), "brands")
        self.push_directory(os.path.join(data_dir, "cars"), "cars")

        return self.report