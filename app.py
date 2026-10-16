"""libzie masaüstü uygulaması: yerel sunucuyu başlatır ve kendi penceresinde (Windows'ta Edge WebView2) açar.

Geliştirme için `python server.py` yeterli; bu dosya yalnızca paketlenen uygulamanın girişidir.
Başka bir libzie zaten çalışıyorsa (aynı yerel sunucu) yeni sunucu açmaz, ona bağlanır; çalışan bir masaüstü örneği varsa
(pencere tepside gizli olabilir) yeni pencere açmak yerine onu öne getirir.
Pencere kapatılınca (Ayarlar → Genel'deki seçenek açıksa) uygulama sistem tepsisinde çalışmaya devam eder; çıkış tepsi menüsündendir.
"""
import threading

import webview

import guncelleme
import i18n
import server
import tepsi


def main():
    url, srv = server.start()
    if srv is None and server.request_show(url):
        return  # çalışan masaüstü örneği öne getirildi
    if srv:
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    window = webview.create_window("libzie", server.launch_url(url), width=1280, height=820, min_size=(900, 600), background_color="#0e1a2b")
    state = {"quitting": False}

    def show():
        try:
            window.show()
            window.restore()
            window.on_top = True   # öne getirmek için kısa süreliğine üstte tut
            window.on_top = False
        except Exception:  # noqa: BLE001 — pencere kapanırken gelen tık hata vermesin
            pass

    def quit_app():
        state["quitting"] = True
        tray.remove()
        try:
            window.destroy()
        except Exception:  # noqa: BLE001
            pass

    tray = tepsi.Tray(show, quit_app, server.ui_lang)
    if tray.start():
        server.DESKTOP = True
        server.DESKTOP_HOOKS["show"] = show
        guncelleme.EXIT_HOOKS.append(tray.remove)

        def on_closing():
            # Kapatma düğmesi: seçenek açıksa pencere gizlenir ve uygulama tepside çalışır (False = kapatmayı iptal et)
            if state["quitting"] or not server.tray_enabled():
                return True
            window.hide()
            settings = server.read_settings()
            if not settings.get("tray_ipucu"):  # ilk seferde nerede olduğunu söyle
                settings["tray_ipucu"] = True
                server.write_settings(settings)
                tray.balloon("libzie", i18n.msg("tray.hint", server.ui_lang()))
            return False

        window.events.closing += on_closing
    webview.start()
    tray.remove()
    if srv:
        srv.shutdown()


if __name__ == "__main__":
    main()
