# -*- coding: utf-8 -*-
"""
终末地风格白色大字生成器
《明日方舟：终末地》标题大字风格：HarmonyOS Sans SC 超粗黑体、纯白大字、
水平居中、带轻微字距，可叠加副标题小字。
"""
import argparse
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageTk

# 允许处理超大图片（如 1 亿像素级照片、全景图）
Image.MAX_IMAGE_PIXELS = None

IMAGE_EXTS = [".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"]

BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(BASE_DIR, "fonts")
FONTS = {
    "Black（终末地大字）": "HarmonyOS_Sans_SC_Black.ttf",
    "Bold（标题）": "HarmonyOS_Sans_SC_Bold.ttf",
    "Medium（副标题）": "HarmonyOS_Sans_SC_Medium.ttf",
}


def resource(name):
    return os.path.join(FONT_DIR, name)


def measure_tracked(draw, text, font, tracking):
    """带字距的文本宽度（tracking 为像素）。"""
    if not text:
        return 0
    w = 0
    for ch in text:
        bbox = draw.textbbox((0, 0), ch, font=font)
        w += (bbox[2] - bbox[0]) + tracking
    return max(w - tracking, 0)


def fit_font_size(draw, text, font_path, tracking_ratio, max_width, start_size):
    """从 start_size 逐步缩小，直到文本宽度不超过 max_width。"""
    size = start_size
    while size > 8:
        font = ImageFont.truetype(font_path, size)
        tracking = size * tracking_ratio
        if measure_tracked(draw, text, font, tracking) <= max_width:
            return font, tracking, size
        size = max(int(size * 0.96), 8) if size > 40 else size - 1
    font = ImageFont.truetype(font_path, size)
    return font, size * tracking_ratio, size


def draw_tracked_line(draw, xy, text, font, tracking, fill):
    """逐字符绘制以实现字距。xy 为该行左上角基准。"""
    x, y = xy
    for ch in text:
        bbox = draw.textbbox((0, 0), ch, font=font)
        draw.text((x - bbox[0], y), ch, font=font, fill=fill)
        x += (bbox[2] - bbox[0]) + tracking
    return x - tracking  # 实际占用宽度


def render_text_layer(width, height, main_text, sub_text, weight_key,
                      size_ratio, position_y, tracking_ratio,
                      subtitle_size_ratio, shadow, main_color=(255, 255, 255, 255),
                      sub_color=(230, 230, 230, 235)):
    """在透明层上渲染大字与副标题，返回 RGBA Image。"""
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    lines = [ln for ln in main_text.split("\n") if ln.strip()]
    if not lines:
        return layer


    main_path = resource(FONTS[weight_key])
    sub_path = resource(FONTS["Medium（副标题）"])

    max_w = int(width * 0.85)
    start = int(height * size_ratio)
    probe = ImageDraw.Draw(layer)

    fonts, trackings = [], []
    for ln in lines:
        f, t, _ = fit_font_size(probe, ln, main_path, tracking_ratio, max_w, start)
        fonts.append(f)
        trackings.append(t)

    line_h = []
    for f in fonts:
        asc, desc = f.getmetrics()
        line_h.append(asc + desc)
    total_h = sum(line_h) + int(line_h[0] * 0.18) * (len(lines) - 1)

    sub_font = None
    sub_h = 0
    sub_tracking = 0
    if sub_text.strip():
        sub_size = max(int(height * subtitle_size_ratio), 10)
        sub_font = ImageFont.truetype(sub_path, sub_size)
        sub_tracking = sub_size * 0.10
        sub_h = sum(sub_font.getmetrics()) + int(height * 0.02)

    y0 = int((height - total_h - sub_h) * (position_y / 100.0))

    def draw_group(target_draw, shadow_pass=False):
        y = y0
        for ln, f, t, lh in zip(lines, fonts, trackings, line_h):
            lw = measure_tracked(target_draw, ln, f, t)
            x = (width - lw) / 2
            draw_tracked_line(target_draw, (x, y), ln, f, t,
                              (255, 255, 255, 255) if shadow_pass else main_color)
            y += lh + int(lh * 0.18)
        if sub_font and sub_text.strip():
            sw = measure_tracked(target_draw, sub_text, sub_font, sub_tracking)
            draw_tracked_line(target_draw, ((width - sw) / 2, y + int(height * 0.01)),
                              sub_text, sub_font, sub_tracking,
                              (255, 255, 255, 255) if shadow_pass else sub_color)

    if shadow:
        shadow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow_layer)
        draw_group(sd, shadow_pass=True)
        blur = max(int(height * size_ratio * 0.045), 3)
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(blur))
        shadow_layer.putalpha(shadow_layer.getchannel("A").point(lambda a: (a * 55) // 100))
        layer.alpha_composite(shadow_layer)
        del shadow_layer

    draw_group(ImageDraw.Draw(layer))
    return layer


def compose(photo, main_text, sub_text, weight_key, size_ratio, position_y,
            tracking_ratio, subtitle_size_ratio, shadow, force_169):
    """主入口：输入 PIL 图像，返回合成后的 RGBA 图像（原图不被修改）。"""
    img = photo.convert("RGBA")
    if force_169:
        w, h = img.size
        target = 16 / 9
        if abs(w / h - target) > 0.005:
            if w / h > target:
                nw = int(h * target)
                x0 = (w - nw) // 2
                img = img.crop((x0, 0, x0 + nw, h))
            else:
                nh = int(w / target)
                y0 = (h - nh) // 2
                img = img.crop((0, y0, w, y0 + nh))
    text_layer = render_text_layer(img.width, img.height, main_text, sub_text,
                                   weight_key, size_ratio, position_y,
                                   tracking_ratio, subtitle_size_ratio, shadow)
    img.alpha_composite(text_layer)
    return img


def load_image(path):
    """读取图片并按 EXIF 方向摆正（手机照片常见竖拍旋转）。"""
    with Image.open(path) as im:
        return ImageOps.exif_transpose(im).convert("RGBA")


class App(tk.Tk):
    PREVIEW_W = 880        # 预览显示宽度
    PREVIEW_SRC_W = 1400   # 预览合成所用源图上限，超大图先降采样再实时预览

    def __init__(self):
        super().__init__()
        self.title("终末地风格白色大字生成器 · HarmonyOS Sans")
        self.configure(bg="#1a1d21")
        self.photo = None          # 原始 PIL 图（全分辨率）
        self.preview_base = None   # 预览用降采样图
        self.result = None         # 当前预览结果（预览分辨率）
        self.preview_img = None    # PhotoImage 引用
        self.out_path = ""
        self._refresh_job = None

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#1a1d21")
        style.configure("TLabel", background="#1a1d21", foreground="#e8e8e8")
        style.configure("Hint.TLabel", background="#1a1d21", foreground="#8a9097")
        style.configure("TButton", background="#2e343b", foreground="#ffffff", padding=6)
        style.map("TButton", background=[("active", "#3d454e")])
        style.configure("TScale", background="#1a1d21")
        style.configure("TCheckbutton", background="#1a1d21", foreground="#e8e8e8")

        top = ttk.Frame(self)
        top.pack(fill="x", padx=12, pady=(10, 4))
        ttk.Button(top, text="选择图片…", command=self.pick_image).pack(side="left")
        self.img_label = ttk.Label(top, text="未选择图片（建议 16:9）", style="Hint.TLabel")
        self.img_label.pack(side="left", padx=10)

        self.canvas = tk.Label(self, bg="#0d0e10")
        self.canvas.pack(fill="both", expand=True, padx=12, pady=8)

        row1 = ttk.Frame(self)
        row1.pack(fill="x", padx=12, pady=2)
        ttk.Label(row1, text="大字（可换行）").pack(anchor="w")
        self.text_var = tk.StringVar(value="这片大地")
        entry = tk.Entry(row1, textvariable=self.text_var, font=("Microsoft YaHei UI", 14),
                         bg="#22262b", fg="#ffffff", insertbackground="#ffffff",
                         relief="flat")
        entry.pack(fill="x", pady=(2, 4))
        entry.bind("<KeyRelease>", lambda e: self.refresh())

        row2 = ttk.Frame(self)
        row2.pack(fill="x", padx=12, pady=2)
        ttk.Label(row2, text="副标题（可选，小字）").pack(anchor="w")
        self.sub_var = tk.StringVar(value="ARKNIGHTS: ENDFIELD")
        entry2 = tk.Entry(row2, textvariable=self.sub_var, font=("Microsoft YaHei UI", 11),
                          bg="#22262b", fg="#bbbbbb", insertbackground="#ffffff",
                          relief="flat")
        entry2.pack(fill="x", pady=(2, 4))
        entry2.bind("<KeyRelease>", lambda e: self.refresh())

        row3 = ttk.Frame(self)
        row3.pack(fill="x", padx=12, pady=4)
        ttk.Label(row3, text="字重").pack(side="left")
        self.weight_var = tk.StringVar(value="Black（终末地大字）")
        cb = ttk.Combobox(row3, textvariable=self.weight_var, state="readonly",
                          values=list(FONTS.keys()), width=18)
        cb.pack(side="left", padx=(6, 16))
        cb.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        self.force169_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(row3, text="裁剪为16:9", variable=self.force169_var,
                        command=self.refresh).pack(side="left", padx=(0, 16))
        self.shadow_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(row3, text="阴影", variable=self.shadow_var,
                        command=self.refresh).pack(side="left")

        sliders = ttk.Frame(self)
        sliders.pack(fill="x", padx=12)
        self._slider(sliders, "字号（占高比 %）", "size_var", 12, 40, 18.0)
        self._slider(sliders, "垂直位置 %（0顶 100底）", "pos_var", 0, 100, 45.0)
        self._slider(sliders, "字距 %", "track_var", 0, 15, 2.0)
        self._slider(sliders, "副标题字号 %", "subsize_var", 1, 12, 3.2)

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=12, pady=(6, 12))
        ttk.Button(bottom, text="保存图片…", command=self.save).pack(side="right")
        self.status_label = ttk.Label(bottom, text="选择图片后开始", style="Hint.TLabel")
        self.status_label.pack(side="right", padx=12)
        ttk.Label(bottom, text="终末地字体：HarmonyOS Sans SC（免费商用）",
                  style="Hint.TLabel").pack(side="left")

        self.minsize(920, 700)

    def _slider(self, parent, label, attr, lo, hi, init):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", pady=1)
        ttk.Label(frame, text=label, width=22).pack(side="left")
        var = tk.DoubleVar(value=init)
        setattr(self, attr, var)
        s = ttk.Scale(frame, from_=lo, to=hi, variable=var, orient="horizontal")
        s.pack(side="left", fill="x", expand=True, padx=8)
        val = ttk.Label(frame, width=5, style="Hint.TLabel")
        val.pack(side="left")
        var.trace_add("write", lambda *a, v=var, l=val: l.config(text=f"{v.get():.1f}"))
        val.config(text=f"{init:.1f}")
        s.bind("<ButtonRelease>", lambda e: self.refresh())
        s.bind("<B1-Motion>", lambda e: self.refresh())

    def pick_image(self):
        path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片", " ".join("*" + e for e in IMAGE_EXTS)), ("所有文件", "*.*")])
        if not path:
            return
        try:
            self.photo = load_image(path)
        except Exception as ex:
            messagebox.showerror("错误", f"无法打开图片：{ex}")
            return
        self.out_path = os.path.splitext(path)[0] + "_endfield.png"
        w, h = self.photo.size
        if w > self.PREVIEW_SRC_W:
            nh = max(int(h * self.PREVIEW_SRC_W / w), 1)
            self.preview_base = self.photo.resize((self.PREVIEW_SRC_W, nh), Image.BILINEAR)
        else:
            self.preview_base = self.photo
        self.img_label.config(text=os.path.basename(path) + f"  ({w}×{h})")
        self.refresh()

    def current_params(self):
        return dict(
            main_text=self.text_var.get(),
            sub_text=self.sub_var.get(),
            weight_key=self.weight_var.get(),
            size_ratio=self.size_var.get() / 100.0,
            position_y=self.pos_var.get(),
            tracking_ratio=self.track_var.get() / 100.0,
            subtitle_size_ratio=self.subsize_var.get() / 100.0,
            shadow=self.shadow_var.get(),
            force_169=self.force169_var.get(),
        )

    def refresh(self):
        """防抖：连续输入/拖动滑条时只在中断后合成一次预览。"""
        if self.photo is None:
            return
        if self._refresh_job is not None:
            self.after_cancel(self._refresh_job)
        self._refresh_job = self.after(140, self._do_refresh)

    def _do_refresh(self):
        self._refresh_job = None
        result = compose(self.preview_base, **self.current_params())
        self.result = result
        pw = min(self.PREVIEW_W, result.width)
        ph = max(int(result.height * pw / result.width), 1)
        prev = result.resize((pw, ph), Image.LANCZOS)
        self.preview_img = ImageTk.PhotoImage(prev)
        self.canvas.config(image=self.preview_img)
        ow, oh = self.photo.size
        self.status_label.config(
            text=f"预览 {result.width}×{result.height} · 保存时按原图 {ow}×{oh} 输出")

    def save(self):
        if self.photo is None:
            messagebox.showinfo("提示", "请先选择图片")
            return
        path = filedialog.asksaveasfilename(
            title="保存图片", defaultextension=".png",
            initialfile=os.path.basename(self.out_path or "output_endfield.png"),
            filetypes=[("PNG 图片", "*.png"), ("JPEG 图片", "*.jpg")])
        if not path:
            return
        self.config(cursor="watch")
        self.status_label.config(text="正在按原图分辨率渲染…")
        self.update_idletasks()
        try:
            result = compose(self.photo, **self.current_params())
            if path.lower().endswith((".jpg", ".jpeg")):
                result.convert("RGB").save(path, quality=95)
            else:
                result.save(path)
        except Exception as ex:
            messagebox.showerror("错误", f"保存失败：{ex}")
        finally:
            self.config(cursor="")
            self.status_label.config(text="已保存 " + path)


def run_cli(args):
    photo = load_image(args.input)
    out = compose(photo, main_text=args.text, sub_text=args.subtitle or "",
                  weight_key=args.weight, size_ratio=args.size / 100.0,
                  position_y=args.pos, tracking_ratio=args.tracking / 100.0,
                  subtitle_size_ratio=args.subsize / 100.0,
                  shadow=not args.no_shadow, force_169=args.crop169)
    out_path = args.output or os.path.splitext(args.input)[0] + "_endfield.png"
    if out_path.lower().endswith((".jpg", ".jpeg")):
        out.convert("RGB").save(out_path, quality=95)
    else:
        out.save(out_path)
    print("已保存：" + out_path)


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("--cli", "-c") or (
            len(sys.argv) > 1 and not sys.argv[1].startswith("-") and os.path.isfile(sys.argv[1])):
        import argparse as ap
        p = ap.ArgumentParser(description="终末地风格白色大字生成器（命令行模式）")
        p.add_argument("input", help="输入图片")
        p.add_argument("-t", "--text", required=True, help="大字内容，\\n 换行")
        p.add_argument("-s", "--subtitle", default="", help="副标题")
        p.add_argument("-w", "--weight", default="Black（终末地大字）", choices=list(FONTS))
        p.add_argument("--size", type=float, default=18.0, help="字号占高比%%（默认18）")
        p.add_argument("--pos", type=float, default=45.0, help="垂直位置%%（默认45）")
        p.add_argument("--tracking", type=float, default=2.0, help="字距%%（默认2）")
        p.add_argument("--subsize", type=float, default=3.2, help="副标题字号%%（默认3.2）")
        p.add_argument("--no-shadow", action="store_true", help="关闭阴影")
        p.add_argument("--crop169", action="store_true", help="裁剪为16:9")
        p.add_argument("-o", "--output", default=None, help="输出路径")
        run_cli(p.parse_args(sys.argv[1:]))
        return
    App().mainloop()


if __name__ == "__main__":
    main()
