# 终末地风格白色大字生成器

为照片添加《明日方舟：终末地》风格的白色大字标题。字体与游戏内一致：**HarmonyOS Sans SC（鸿蒙黑体）**，免费可商用，已打包进 exe 与 APK，无任何运行时依赖。

## 下载使用

| 平台 | 产物 | 说明 |
|---|---|---|
| Windows | `dist\终末地白色大字生成器.exe` | 单文件（约 47 MB），双击即用 |
| Android 8.0+ | `dist\终末地白色大字生成器.apk` | 约 12.6 MB，安装后从相册选图、结果存入 `Pictures/EndfieldText` |
| 浏览器 | 直接打开 `web/index.html` | 与 APK 同一渲染核心，保存为下载 |

### 桌面版

1. 点「选择图片…」导入照片（建议 16:9）；
2. 输入大字（支持多行）、可选副标题小字；
3. 调整字重 / 字号 / 垂直位置 / 字距 / 阴影，实时预览；
4. 点「保存图片…」导出 PNG 或 JPG（**按原图分辨率输出**，1 亿像素级照片亦可）。

### Android 版

- 图片经系统相册选择器选取，竖拍照片自动按 EXIF 摆正；
- 画布输出上限 4096px（WebView 限制），长边超出会等比缩放；
- 保存写入系统相册 `Pictures/EndfieldText`（Android 10+ 无需存储权限）。

### 命令行（Windows，适合批量）

```
终末地白色大字生成器.exe 照片.jpg -t "第一行\n第二行" -s "SUBTITLE" -o 输出.png --crop169
```

参数：`-t` 大字（`\n` 换行，必填）、`-s` 副标题、`-w` 字重、`--size` 字号占高比%（默认 18）、`--pos` 垂直位置%（默认 45）、`--tracking` 字距%（默认 2）、`--subsize` 副标题字号%（默认 3.2）、`--no-shadow` 关闭阴影、`--crop169` 居中裁剪为 16:9。

## 从源码构建

### Windows exe

```
python -m pip install pillow pyinstaller
python -m PyInstaller --noconfirm --onefile --windowed --name "终末地白色大字生成器" --add-binary "app/fonts/*.ttf;fonts" app/endfield_textgen.py
```

### Android APK

无需 Gradle。前置：JDK 17+、Android SDK（build-tools 35.0.0 与 platforms/android-34，首次可用 sdkmanager 安装）。

```
# Linux / macOS / Git Bash
ANDROID_SDK=<SDK路径> bash android/build_apk.sh [版本名] [版本号]
```

脚本流程：aapt2 编译链接 → javac → d8（注意：build-tools 34 的 d8 存在 NPE bug，须用 35 的 d8.jar）→ zipalign → apksigner 签名。签名密钥 `android/release.keystore`（alias `endfield`，密码 `endfield2026`）随仓库保存以便复现构建，正式项目请勿效仿。

## 字体说明

终末地游戏内文字使用 HarmonyOS Sans（社区共识，另含思源黑体）；标题大字的超粗风格以 Black 字重还原（社区亦指出接近方正兰亭大黑简的厚重感，Black 为最接近的可自由分发替代）。字体版权归华为所有，随 [HarmonyOS Sans 官方发布](https://developer.huawei.com/consumer/cn/design/resource-V1/) 免费商用，授权文本见 `app/fonts/LICENSE.txt`。APK 内为 [fonttools](https://github.com/fonttools/fonttools) 转换的 woff2 版本。

## 版本历史

- **v1.1.0**：大尺寸图片支持（降采样预览 + 全分辨率导出 + EXIF 摆正）；新增 Android APK 与网页版；建立版本控制。
- **v1.0.0**：桌面版首发（HarmonyOS Sans 大字合成，GUI + 命令行）。

## 参考

- [huawei-fonts/HarmonyOS-Sans](https://github.com/huawei-fonts/HarmonyOS-Sans)
- [NGA：终末地式雷霆大字生成机（社区风格参考）](https://ngabbs.com/read.php?tid=47261696)
- [Naptie/endfield-docmaker](https://github.com/Naptie/endfield-docmaker)（终末地风格开源工具参考）
