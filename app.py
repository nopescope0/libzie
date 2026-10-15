"""libzie masaüstü uygulaması: yerel sunucuyu başlatır ve kendi penceresinde (Windows'ta Edge WebView2) açar.

Geliştirme için `python server.py` yeterli; bu dosya yalnızca paketlenen uygulamanın girişidir.
Başka bir libzie zaten çalışıyorsa (aynı yerel sunucu) yeni sunucu açmaz, ona bağlanır.
"""
import threading

import webview

import server


def main():
    url, srv = server.start()
    if srv:
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    webview.create_window("libzie", url, width=1280, height=820, min_size=(900, 600), background_color="#0e1a2b")
    webview.start()
    if srv:
        srv.shutdown()


if __name__ == "__main__":
    main()
