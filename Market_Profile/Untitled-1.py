# -*- coding: utf-8 -*-
"""
CLOUDFLARE MANIFEST OLUŞTURUCU (PNG/WEBP) — Çoklu Yayın Kökü Destekli
- Kaynak klasör ve manifest hedefi diyalogla seçilir
- PNG/WEBP dosyaları toplanır (isteğe bağlı alt klasörler)
- Seçili dosyalar ilk eşleşen yayın köküyle Cloudflare URL’ine çevrilir
- Manifest daima Cloudflare linklerinden oluşur; eşleşmeyenler atlanır
"""

import time
from pathlib import Path
from tkinter import Tk, filedialog, messagebox

# ====== YAYIN KÖKLERİ (local klasör → Cloudflare base URL) ======
# Not: Aşağıdaki local yolları kendi makinenle eşleştir (gerekirse değiştir).
PUBLISH_ROOTS = [
    {
        # 1) Asıl Pages kökün: Brochures/Brochures
        "local": r"C:\Users\EREN\Documents\GitHub\resimler\Brochures\Brochures",
        "url":   "https://resimler-211.pages.dev/Brochures/Brochures",
        # path içinde bu işaretçi görülürse (ör. farklı sürücüde kopya) yine bağlar:
        "marker_segments": ("Brochures", "Brochures"),
    },
    {
        # 2) Market_Profile (yayında ise bunu açık bırak; değilse sil/yorumla)
        "local": r"C:\Users\EREN\Documents\GitHub\resimler\Market_Profile",
        "url":   "https://resimler-211.pages.dev/Market_Profile",
        "marker_segments": ("Market_Profile",),
    },
    {
        # 3) LabelveTarihler (yayında ise bunu açık bırak; değilse sil/yorumla)
        "local": r"C:\Users\EREN\Documents\GitHub\resimler\LabelveTarihler",
        "url":   "https://resimler-211.pages.dev/LabelveTarihler",
        "marker_segments": ("LabelveTarihler",),
    },
]
# ================================================================

EXTENSIONS = {".png", ".webp"}
MANIFEST_NAME = "manifest.txt"
VERSION_STAMP = time.strftime("%Y%m%d%H%M%S")  # tüm satırlarda aynı v= kullanalım

def collect_images(root: Path, recursive: bool):
    exts = {e.lower() for e in EXTENSIONS}
    files = []
    if recursive:
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() in exts:
                files.append(p)
    else:
        for p in root.iterdir():
            if p.is_file() and p.suffix.lower() in exts:
                files.append(p)
    files.sort(key=lambda x: str(x).lower())
    return files

def try_map_with_root(p: Path, local_root: Path, base_url: str):
    """p'yi local_root'a göre göreli alıp Cloudflare URL üretmeye çalış."""
    try:
        rel = p.resolve().relative_to(local_root.resolve())
        rel_str = str(rel).replace("\\", "/")
        return f"{base_url.rstrip('/')}/{rel_str.lstrip('/')}?v={VERSION_STAMP}"
    except Exception:
        return None

def try_map_with_marker(p: Path, marker_segments: tuple[str, ...], base_url: str):
    """Yol içinde marker'ı bulup ondan sonrasını göreli alarak Cloudflare URL üret."""
    parts_lower = [s.lower() for s in p.resolve().parts]
    marker_lower = [s.lower() for s in marker_segments]
    n, m = len(parts_lower), len(marker_lower)
    for i in range(n - m + 1):
        if parts_lower[i:i+m] == marker_lower:
            # marker'dan sonrasını relative yap
            rel_parts = p.resolve().parts[i+m:]
            rel_str = "/".join(rel_parts).replace("\\", "/")
            return f"{base_url.rstrip('/')}/{rel_str.lstrip('/')}?v={VERSION_STAMP}"
    return None

def map_to_cloudflare_url(p: Path):
    """Sırayla tüm yayın köklerinde dene; ilk başarıyı döndür."""
    for entry in PUBLISH_ROOTS:
        local = Path(entry["local"])
        base_url = entry["url"]
        # 1) Doğrudan local köke göre dene
        url = try_map_with_root(p, local, base_url)
        if url:
            return url
        # 2) Marker ile dene (opsiyonel)
        marker = entry.get("marker_segments")
        if marker:
            url = try_map_with_marker(p, marker, base_url)
            if url:
                return url
    return None  # hiçbir kökle eşleşmedi

def write_manifest(dest_dir: Path, lines: list[str]) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    out = dest_dir / MANIFEST_NAME
    with out.open("w", encoding="utf-8") as f:
        for ln in lines:
            f.write(ln.strip() + "\n")
    return out

def main():
    root = Tk(); root.withdraw()

    src_dir = filedialog.askdirectory(title="Kaynak klasör (PNG/WEBP)")
    if not src_dir:
        return
    dst_dir = filedialog.askdirectory(title="manifest.txt nereye yazılsın?")
    if not dst_dir:
        return

    recursive = messagebox.askyesno("Alt klasörler", "Alt klasörler taransın mı?")

    images = collect_images(Path(src_dir), recursive)
    if not images:
        messagebox.showinfo("Bilgi", "Seçilen klasörde PNG/WEBP bulunamadı.")
        return

    lines = []
    skipped = 0
    for p in images:
        url = map_to_cloudflare_url(p)
        if url:
            lines.append(url)
        else:
            skipped += 1

    if not lines:
        # Kullanıcıya hangi kökleri beklediğimizi gösteren net uyarı
        roots_txt = "\n".join(f"- {r['local']}  →  {r['url']}" for r in PUBLISH_ROOTS)
        messagebox.showerror(
            "Hiç dosya eşlenmedi",
            "Cloudflare köklerine eşlenebilen dosya bulunamadı.\n\n"
            "Kontrol etmen gerekenler:\n"
            "1) Kaynak klasörün aşağıdaki local köklerin altında olmalı.\n"
            "2) Bu kökler gerçekten Pages'ta yayınlanıyor olmalı.\n\n"
            f"Tanımlı kökler:\n{roots_txt}"
        )
        return

    out_path = write_manifest(Path(dst_dir), lines)

    msg = (
        f"Toplam görsel: {len(images)}\n"
        f"Yazılan (Cloudflare): {len(lines)}\n"
        f"Atlanan (eşleşmedi): {skipped}\n\n"
        f"manifest.txt:\n{out_path}"
    )
    messagebox.showinfo("Bitti", msg)
    print(msg)
    print("Örnek (ilk 5 satır):")
    for ln in lines[:5]:
        print(ln)

if __name__ == "__main__":
    main()
