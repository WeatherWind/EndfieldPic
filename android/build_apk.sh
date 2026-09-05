#!/usr/bin/env bash
# 构建终末地大字生成器 APK（无需 Gradle，直接使用 aapt2/javac/d8/apksigner）
# 前置：JDK 17+，ANDROID_SDK 指向含 build-tools/34.0.0 与 platforms/android-34 的 SDK 目录
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
mkdir -p "$OUT/dex"
(cd "$OUT/classes" && java -cp "$(cygpath -m "$BT")/lib/d8.jar" com.android.tools.r8.D8 \
  --release --lib "$(cygpath -m "$PLATFORM")" --output "$(cygpath -m "$OUT/dex")" \
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
        if item.filename == "META-INF/":  # 旧签名残留不复制
            continue
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
cmd //c "$(cygpath -w "$BT")\\apksigner.bat" sign --ks "$(cygpath -w "$KS")" --ks-pass "pass:$KS_PASS" \
  --ks-key-alias endfield --key-pass "pass:$KS_PASS" \
  --out "$(cygpath -w "$ROOT/dist/终末地白色大字生成器.apk")" "$(cygpath -w "$OUT/app.aligned.apk")"
cmd //c "$(cygpath -w "$BT")\\apksigner.bat" verify --print-certs "$ROOT/dist/终末地白色大字生成器.apk" | head -4
ls -la "$ROOT/dist/"
echo "BUILD OK"
