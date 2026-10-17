"""libzie desktop app: starts the local server and opens it in its own window (Edge WebView2 on Windows).

`python server.py` is enough for development; this file is only the entry point of the packaged app.
If another libzie is already running (the same local server) it does not start a new server but connects to it; if a desktop
instance is running (its window may be hidden in the tray) it brings that one forward instead of opening a new window.
When the window is closed (if the option in Settings → General is on) the app keeps running in the system tray; exit is from the tray menu.
"""
import threading

import webview

import i18n
import server
import tray as tray_icon
import updater


def main():
    url, srv = server.start()
    if srv is None and server.request_show(url):
        return  # the running desktop instance was brought forward
    if srv:
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    window = webview.create_window("libzie", server.launch_url(url), width=1280, height=820, min_size=(900, 600), background_color="#0e1a2b")
    state = {"quitting": False}

    def show():
        try:
            window.show()
            window.restore()
            window.on_top = True   # keep it on top briefly to bring it forward
            window.on_top = False
        except Exception:  # noqa: BLE001 — a click arriving while the window closes must not raise
            pass

    def quit_app():
        state["quitting"] = True
        tray.remove()
        try:
            window.destroy()
        except Exception:  # noqa: BLE001
            pass

    def check_updates():
        # Open the window and go to Settings → About: the version check starts by itself when the tab opens
        show()
        try:
            window.evaluate_js("openSettings('about')")
        except Exception:  # noqa: BLE001 — skip silently if the page has not loaded yet
            pass

    tray = tray_icon.Tray(show, quit_app, server.ui_lang, check_updates)
    if tray.start():
        server.DESKTOP = True
        server.DESKTOP_HOOKS["show"] = show
        updater.EXIT_HOOKS.append(tray.remove)

        def on_closing():
            # Close button: if the option is on the window is hidden and the app keeps running in the tray (False = cancel the close)
            if state["quitting"] or not server.tray_enabled():
                return True
            window.hide()
            settings = server.read_settings()
            if not settings.get("tray_hint_shown"):  # tell them where it went, the first time
                settings["tray_hint_shown"] = True
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
