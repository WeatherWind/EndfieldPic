package com.endfield.textgen;

import android.Manifest;
import android.app.Activity;
import android.content.ContentValues;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.media.MediaScannerConnection;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Base64;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;

/**
 * 终末地风格白色大字生成器（Android）
 * WebView 承载 web/index.html，字体与渲染算法与桌面版一致；
 * 通过 EndfieldSaver JS 桥把画布结果分块传回原生并写入系统相册。
 */
public class MainActivity extends Activity {

    private static final int REQ_FILE = 1;
    private static final int REQ_PERM = 2;

    private WebView webView;
    private ValueCallback<Uri[]> filePathCallback;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        webView = new WebView(this);
        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true);
        s.setAllowFileAccess(true);
        s.setDomStorageEnabled(true);
        webView.setBackgroundColor(0xFF14161A);
        webView.addJavascriptInterface(new Saver(), "EndfieldSaver");
        webView.setWebViewClient(new WebViewClient());
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView v, ValueCallback<Uri[]> cb,
                                             FileChooserParams params) {
                if (filePathCallback != null) filePathCallback.onReceiveValue(null);
                filePathCallback = cb;
                Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("image/*");
                startActivityForResult(Intent.createChooser(intent, "选择图片"), REQ_FILE);
                return true;
            }
        });
        setContentView(webView);
        webView.loadUrl("file:///android_asset/index.html");

        if (Build.VERSION.SDK_INT <= 28
                && checkSelfPermission(Manifest.permission.WRITE_EXTERNAL_STORAGE)
                        != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE}, REQ_PERM);
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == REQ_FILE && filePathCallback != null) {
            filePathCallback.onReceiveValue(
                    WebChromeClient.FileChooserParams.parseResult(resultCode, data));
            filePathCallback = null;
        } else {
            super.onActivityResult(requestCode, resultCode, data);
        }
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }

    /** JS 桥：saveBegin → saveChunk×N → saveEnd，避免单条超大字符串卡 IPC。 */
    private class Saver {
        private ByteArrayOutputStream buffer;
        private String name;
        private String mime = "image/png";

        @JavascriptInterface
        public void saveBegin(String fileName) {
            name = fileName;
            buffer = new ByteArrayOutputStream();
        }

        @JavascriptInterface
        public void saveMimeType(String m) {
            mime = m;
        }

        @JavascriptInterface
        public void saveChunk(String base64) {
            if (buffer != null) {
                byte[] chunk = Base64.decode(base64, Base64.DEFAULT);
                buffer.write(chunk, 0, chunk.length);
            }
        }

        @JavascriptInterface
        public String saveEnd() {
            if (buffer == null || name == null) return null;
            byte[] data = buffer.toByteArray();
            buffer = null;
            final String path = writeToGallery(name, data);
            runOnUiThread(() -> Toast.makeText(MainActivity.this,
                    path == null ? "保存失败" : "已保存到相册 EndfieldText",
                    Toast.LENGTH_LONG).show());
            return path;
        }
    }

    private String writeToGallery(String name, byte[] data) {
        try {
            if (Build.VERSION.SDK_INT >= 29) {
                ContentValues cv = new ContentValues();
                cv.put(MediaStore.Images.Media.DISPLAY_NAME, name);
                cv.put(MediaStore.Images.Media.MIME_TYPE, mimeOf(name));
                cv.put(MediaStore.Images.Media.RELATIVE_PATH,
                        Environment.DIRECTORY_PICTURES + "/EndfieldText");
                cv.put(MediaStore.Images.Media.IS_PENDING, 1);
                Uri uri = getContentResolver().insert(
                        MediaStore.Images.Media.getContentUri(
                                MediaStore.VOLUME_EXTERNAL_PRIMARY), cv);
                try (OutputStream os = getContentResolver().openOutputStream(uri)) {
                    os.write(data);
                }
                cv.clear();
                cv.put(MediaStore.Images.Media.IS_PENDING, 0);
                getContentResolver().update(uri, cv, null, null);
                return Environment.DIRECTORY_PICTURES + "/EndfieldText/" + name;
            }
            File dir = new File(Environment.getExternalStoragePublicDirectory(
                    Environment.DIRECTORY_PICTURES), "EndfieldText");
            if (!dir.exists()) dir.mkdirs();
            File file = new File(dir, name);
            try (FileOutputStream fos = new FileOutputStream(file)) {
                fos.write(data);
            }
            MediaScannerConnection.scanFile(this,
                    new String[]{file.getAbsolutePath()}, null, null);
            return file.getAbsolutePath();
        } catch (Exception e) {
            return null;
        }
    }

    private static String mimeOf(String name) {
        return name.toLowerCase().endsWith(".png") ? "image/png" : "image/jpeg";
    }
}
