#!/usr/bin/env bash
# 构建终末地大字生成器 APK（无需 Gradle，直接使用 aapt2/javac/d8/apksigner）
# 前置：JDK 17+，ANDROID_SDK 指向含 build-tools/35.0.0 与 platforms/android-34 的 SDK 目录
# 兼容 Windows（Git Bash/MSYS）与 Linux/macOS CI 环境
set -euo pipefail

SDK="${ANDROID_SDK:-$PWD/.android-sdk}"
BT="$SDK/build-tools/35.0.0"
PLATFORM="$SDK/platforms/android-34/android.jar"
ROOT="$PWD"
OUT="$ROOT/android/build"
VERSION_NAME="${1:-1.1.0}"
VERSION_CODE="${2:-2}"
KS="$ROOT/android/release.keystore"
KS_PASS="${KS_PASS:-endfield2026}"

# MSYS/Git Bash 下需要转换路径；Linux/macOS 直接使用
mpath() {
  if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else printf '%s' "$1"; fi
}

mkdir -p "$OUT/gen" "$OUT/classes" "$OUT/dex" "$ROOT/dist"

echo "[1/6] aapt2 compile resources"
"$BT/aapt2" compile --dir "$ROOT/android/res" -o "$OUT/res.zip"

echo "[2/6] aapt2 link (manifest + assets)"
"$BT/aapt2" link -o "$OUT/app.base.apk" \
  -I "$PLATFORM" \
  --manifest "$ROOT/android/AndroidManifest.xml" \
  -A "$ROOT/web" \
  --min-sdk-version 24 --target-sdk-version 34 \
  --version-code "$VERSION_CODE" --version-name "$VERSION_NAME" \
  --java "$OUT/gen" --auto-add-overlay \
  "$OUT/res.zip"

echo "[3/6] javac"
javac --release 17 -encoding UTF-8 \
  -classpath "$PLATFORM" \
  -d "$OUT/classes" \
  "$OUT/gen/com/endfield/textgen/R.java" \
  "$ROOT/android/java/com/endfield/textgen/MainActivity.java"

echo "[4/6] d8 dex"
# 注意：build-tools 34 的 d8 存在 NPE bug，必须使用 35 的 d8.jar
(cd "$OUT/classes" && java -cp "$(mpath "$BT")/lib/d8.jar" com.android.tools.r8.D8 \
  --release --lib "$(mpath "$PLATFORM")" --output "$(mpath "$OUT/dex")" \
  $(find . -name '*.class'))

echo "[5/6] pack dex into apk"
python - "$OUT" <<'PYEOF'
import sys, zipfile, os
out = sys.argv[1]
base = os.path.join(out, "app.base.apk")
dex = os.path.join(out, "dex", "classes.dex")
merged = os.path.join(out, "app.unsigned.apk")
with zipfile.ZipFile(base) as zin, zipfile.ZipFile(merged, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        zout.writestr(item, zin.read(item.filename))
    zout.write(dex, "classes.dex")
print("merged ->", merged)
PYEOF

echo "[6/6] zipalign + sign"
if [ ! -f "$KS" ]; then
  keytool -genkeypair -keystore "$KS" -alias endfield -keyalg RSA -keysize 2048 \
    -validity 10000 -storepass "$KS_PASS" -keypass "$KS_PASS" \
    -dname "CN=Endfield TextGen, OU=FanTool, O=EndfieldPic"
fi
"$BT/zipalign" -f 4 "$OUT/app.unsigned.apk" "$OUT/app.aligned.apk"
OUT_APK="$ROOT/dist/EndfieldTextGen-$VERSION_NAME-android.apk"
if [ -f "$BT/apksigner" ]; then
  # Linux/macOS：apksigner 为 shell 脚本
  "$BT/apksigner" sign --ks "$KS" --ks-pass "pass:$KS_PASS" \
    --ks-key-alias endfield --key-pass "pass:$KS_PASS" \
    --out "$OUT_APK" "$OUT/app.aligned.apk"
  "$BT/apksigner" verify "$OUT_APK"
else
  # Windows：apksigner.bat 需经 cmd 调用
  cmd //c "$(cygpath -w "$BT")\\apksigner.bat" sign --ks "$(cygpath -w "$KS")" --ks-pass "pass:$KS_PASS" \
    --ks-key-alias endfield --key-pass "pass:$KS_PASS" \
    --out "$(cygpath -w "$OUT_APK")" "$(cygpath -w "$OUT/app.aligned.apk")"
fi
ls -la "$OUT_APK"
echo "BUILD OK"
