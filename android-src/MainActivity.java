package br.com.wildlog.app;

import android.app.DownloadManager;
import android.content.Context;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.webkit.DownloadListener;
import android.widget.Toast;
import android.util.Base64;
import com.getcapacitor.BridgeActivity;
import java.io.File;
import java.io.FileOutputStream;

public class MainActivity extends BridgeActivity {

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        getBridge().getWebView().setDownloadListener(new DownloadListener() {
            @Override
            public void onDownloadStart(String url, String userAgent,
                String contentDisposition, String mimeType, long contentLength) {

                String filename = "FAUNA_download.xlsx";
                if (contentDisposition != null && contentDisposition.contains("filename=")) {
                    filename = contentDisposition
                        .replaceAll(".*filename=[\"']?([^\"';\n]+)[\"']?.*", "$1").trim();
                } else if (url.contains("FAUNA_")) {
                    int i = url.lastIndexOf("FAUNA_");
                    filename = url.substring(i).replaceAll("[?#].*", "");
                    if (!filename.endsWith(".xlsx")) filename += ".xlsx";
                }

                if (url.startsWith("data:")) {
                    try {
                        String b64 = url.substring(url.indexOf(",") + 1);
                        byte[] bytes = Base64.decode(b64, Base64.DEFAULT);
                        File dir = Environment.getExternalStoragePublicDirectory(
                            Environment.DIRECTORY_DOWNLOADS);
                        if (!dir.exists()) dir.mkdirs();
                        File out = new File(dir, filename);
                        FileOutputStream fos = new FileOutputStream(out);
                        fos.write(bytes);
                        fos.close();
                        Toast.makeText(MainActivity.this,
                            "Salvo em Downloads: " + filename,
                            Toast.LENGTH_LONG).show();
                    } catch (Exception e) {
                        Toast.makeText(MainActivity.this,
                            "Erro ao salvar: " + e.getMessage(),
                            Toast.LENGTH_LONG).show();
                    }
                    return;
                }

                try {
                    DownloadManager.Request req = new DownloadManager.Request(Uri.parse(url));
                    req.setMimeType(mimeType);
                    req.setTitle(filename);
                    req.setDescription("WildLog exportacao");
                    req.setNotificationVisibility(
                        DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
                    req.setDestinationInExternalPublicDir(
                        Environment.DIRECTORY_DOWNLOADS, filename);
                    DownloadManager dm = (DownloadManager)
                        getSystemService(Context.DOWNLOAD_SERVICE);
                    dm.enqueue(req);
                    Toast.makeText(MainActivity.this,
                        "Baixando: " + filename, Toast.LENGTH_SHORT).show();
                } catch (Exception e) {
                    Toast.makeText(MainActivity.this,
                        "Erro: " + e.getMessage(), Toast.LENGTH_LONG).show();
                }
            }
        });
    }
}
