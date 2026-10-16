"""Windows sistem tepsisi (bildirim alanı) simgesi: ek bağımlılık olmadan, ctypes ile Shell_NotifyIcon.

libzie penceresi kapatılınca uygulama arka planda çalışmaya devam eder; bu simge geri dönüş yoludur:
sol tık / çift tık → pencereyi göster, sağ tık → menü (Aç, Çıkış). Simge kendi iş parçacığında (gizli bir pencere ve ileti
döngüsüyle) çalışır; geri çağırmalar da bu iş parçacığında yapılır. Windows dışında `Tray.start()` False döner (özellik kapalı kalır).
"""
import sys
import threading
from pathlib import Path

import i18n

WINDOWS = sys.platform == "win32"
if WINDOWS:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    LRESULT = ctypes.c_ssize_t
    WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

    class WNDCLASSW(ctypes.Structure):
        _fields_ = [("style", wintypes.UINT), ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int), ("cbWndExtra", ctypes.c_int),
                    ("hInstance", wintypes.HINSTANCE), ("hIcon", wintypes.HICON), ("hCursor", wintypes.HANDLE),
                    ("hbrBackground", wintypes.HBRUSH), ("lpszMenuName", wintypes.LPCWSTR), ("lpszClassName", wintypes.LPCWSTR)]

    class GUID(ctypes.Structure):
        _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD), ("Data3", wintypes.WORD), ("Data4", ctypes.c_ubyte * 8)]

    class NOTIFYICONDATAW(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("hWnd", wintypes.HWND), ("uID", wintypes.UINT), ("uFlags", wintypes.UINT),
                    ("uCallbackMessage", wintypes.UINT), ("hIcon", wintypes.HICON), ("szTip", wintypes.WCHAR * 128),
                    ("dwState", wintypes.DWORD), ("dwStateMask", wintypes.DWORD), ("szInfo", wintypes.WCHAR * 256),
                    ("uTimeoutOrVersion", wintypes.UINT), ("szInfoTitle", wintypes.WCHAR * 64), ("dwInfoFlags", wintypes.DWORD),
                    ("guidItem", GUID), ("hBalloonIcon", wintypes.HICON)]

    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.DefWindowProcW.restype = LRESULT
    user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
    user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_int, ctypes.c_int,
                                       ctypes.c_int, ctypes.c_int, wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID]
    user32.CreateWindowExW.restype = wintypes.HWND
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.TrackPopupMenu.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.HWND, wintypes.LPVOID]
    user32.AppendMenuW.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_size_t, wintypes.LPCWSTR]
    user32.CreatePopupMenu.restype = wintypes.HMENU
    user32.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT, ctypes.c_int, ctypes.c_int, wintypes.UINT]
    user32.LoadImageW.restype = wintypes.HANDLE
    user32.LoadIconW.argtypes = [wintypes.HINSTANCE, ctypes.c_void_p]
    user32.LoadIconW.restype = wintypes.HICON
    shell32.ExtractIconW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT]
    shell32.ExtractIconW.restype = wintypes.HICON
    shell32.Shell_NotifyIconW.argtypes = [wintypes.DWORD, ctypes.POINTER(NOTIFYICONDATAW)]
    kernel32.GetModuleHandleW.restype = wintypes.HINSTANCE
    kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.DestroyWindow.argtypes = [wintypes.HWND]
    user32.DestroyMenu.argtypes = [wintypes.HMENU]
    user32.SetMenuDefaultItem.argtypes = [wintypes.HMENU, wintypes.UINT, wintypes.UINT]
    user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
    user32.RegisterWindowMessageW.argtypes = [wintypes.LPCWSTR]
    user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
    user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.DispatchMessageW.restype = LRESULT

WM_NULL, WM_DESTROY, WM_CLOSE, WM_QUERYENDSESSION, WM_ENDSESSION, WM_CONTEXTMENU = 0x0000, 0x0002, 0x0010, 0x0011, 0x0016, 0x007B
WM_LBUTTONUP, WM_LBUTTONDBLCLK, WM_RBUTTONUP, WM_APP = 0x0202, 0x0203, 0x0205, 0x8000
WM_TRAY, WM_STOP = WM_APP + 1, WM_APP + 2
NIM_ADD, NIM_MODIFY, NIM_DELETE = 0, 1, 2
NIF_MESSAGE, NIF_ICON, NIF_TIP, NIF_INFO = 0x1, 0x2, 0x4, 0x10
NIIF_INFO = 0x1
MF_STRING, MF_SEPARATOR = 0x0, 0x800
TPM_RIGHTBUTTON, TPM_RETURNCMD = 0x2, 0x100
ID_OPEN, ID_QUIT = 1, 2
ICON_FILE = Path(__file__).resolve().parent / "assets" / "icon.ico"


def system_lang():
    """Windows'un arayüz dili Türkçeyse 'tr', değilse 'en' (kullanıcı libzie'de dil seçmediyse tepsi menüsü bunu kullanır)."""
    try:
        return "tr" if ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF == 0x1F else "en"
    except Exception:  # noqa: BLE001
        return "en"


def load_icon():
    """Paketlenmiş uygulamada exe'nin kendi simgesi, kaynak koddan çalışırken assets/icon.ico; bulunamazsa sistem simgesi."""
    hicon = None
    if getattr(sys, "frozen", False):
        hicon = shell32.ExtractIconW(kernel32.GetModuleHandleW(None), sys.executable, 0)
        if hicon and int(ctypes.cast(hicon, ctypes.c_void_p).value or 0) > 1:
            return hicon
    if ICON_FILE.exists():
        h = user32.LoadImageW(None, str(ICON_FILE), 1, 0, 0, 0x10 | 0x40)  # IMAGE_ICON, LR_LOADFROMFILE | LR_DEFAULTSIZE
        if h:
            return h
    return user32.LoadIconW(None, 32512)  # IDI_APPLICATION


class Tray:
    """on_show(): pencereyi göster · on_quit(): uygulamayı kapat · lang(): 'tr'/'en' (menü her açılışta güncel dili okur)."""

    def __init__(self, on_show, on_quit, lang=system_lang):
        self.on_show, self.on_quit, self.lang = on_show, on_quit, lang
        self.hwnd = None
        self.ok = False
        self._ready = threading.Event()
        self._nid = None
        self._taskbar_msg = 0
        self._proc = None  # WNDPROC referansı, çöp toplayıcı silmesin

    def start(self):
        if not WINDOWS:
            return False
        threading.Thread(target=self._run, name="libzie-tepsi", daemon=True).start()
        self._ready.wait(5)
        return self.ok

    def stop(self):
        if self.ok and self.hwnd:
            user32.PostMessageW(self.hwnd, WM_STOP, 0, 0)

    def remove(self):
        """Simgeyi hemen kaldırır (os._exit ile ani kapanmadan önce; yoksa simge fare üstüne gelene dek hayalet olarak kalır)."""
        if self.ok and self._nid:
            shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(self._nid))

    def balloon(self, title, text):
        """Tepsi simgesinden kısa bir bildirim (yalnızca bilgi); simge yoksa sessizce atlanır."""
        if not (self.ok and self._nid):
            return
        nid = self._nid
        nid.uFlags |= NIF_INFO
        nid.szInfoTitle, nid.szInfo, nid.dwInfoFlags = title[:63], text[:255], NIIF_INFO
        shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid))
        nid.uFlags &= ~NIF_INFO

    # --- iş parçacığı
    def _add_icon(self):
        return bool(shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(self._nid)))

    def _run(self):
        try:
            hinst = kernel32.GetModuleHandleW(None)
            self._proc = WNDPROC(self._wndproc)
            cls = WNDCLASSW()
            cls.lpfnWndProc, cls.hInstance, cls.lpszClassName = self._proc, hinst, "LibzieTepsi"
            user32.RegisterClassW(ctypes.byref(cls))
            # Gizli, üst düzey bir pencere: Gezgin yeniden başlayınca gönderilen "TaskbarCreated" yalnızca bunlara ulaşır
            self.hwnd = user32.CreateWindowExW(0, "LibzieTepsi", "libzie", 0x80000000, 0, 0, 0, 0, None, None, hinst, None)
            self._taskbar_msg = user32.RegisterWindowMessageW("TaskbarCreated")
            nid = NOTIFYICONDATAW()
            nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
            nid.hWnd, nid.uID, nid.uFlags, nid.uCallbackMessage = self.hwnd, 1, NIF_MESSAGE | NIF_ICON | NIF_TIP, WM_TRAY
            nid.hIcon = load_icon()
            nid.szTip = "libzie"
            self._nid = nid
            self.ok = bool(self.hwnd) and self._add_icon()
        except Exception:  # noqa: BLE001 — tepsi olmadan da uygulama çalışır
            self.ok = False
        finally:
            self._ready.set()
        if not self.ok:
            return
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def _menu(self):
        lang = self.lang()
        menu = user32.CreatePopupMenu()
        user32.AppendMenuW(menu, MF_STRING, ID_OPEN, i18n.msg("tray.open", lang))
        user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
        user32.AppendMenuW(menu, MF_STRING, ID_QUIT, i18n.msg("tray.quit", lang))
        user32.SetMenuDefaultItem(menu, ID_OPEN, 0)
        pt = POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        user32.SetForegroundWindow(self.hwnd)  # menü dışına tıklanınca kapanması için gerekli
        cmd = user32.TrackPopupMenu(menu, TPM_RIGHTBUTTON | TPM_RETURNCMD, pt.x, pt.y, 0, self.hwnd, None)
        user32.PostMessageW(self.hwnd, WM_NULL, 0, 0)
        user32.DestroyMenu(menu)
        return cmd

    def _safe(self, fn):
        try:
            fn()
        except Exception:  # noqa: BLE001 — bir geri çağırma hatası ileti döngüsünü durdurmasın
            pass

    def _wndproc(self, hwnd, msg, wparam, lparam):
        if msg == WM_TRAY:
            event = lparam & 0xFFFF
            if event in (WM_LBUTTONUP, WM_LBUTTONDBLCLK):
                self._safe(self.on_show)
            elif event in (WM_RBUTTONUP, WM_CONTEXTMENU):
                cmd = self._menu()
                if cmd == ID_OPEN:
                    self._safe(self.on_show)
                elif cmd == ID_QUIT:
                    self._safe(self.on_quit)
            return 0
        if msg == self._taskbar_msg and self._taskbar_msg:
            self._add_icon()  # Gezgin yeniden başladı: simgeyi geri koy
            return 0
        if msg in (WM_CLOSE, WM_ENDSESSION) and (msg == WM_CLOSE or wparam):
            self._safe(self.on_quit)  # kurulum sihirbazı / oturum kapanışı
            return 0
        if msg == WM_QUERYENDSESSION:
            return 1
        if msg == WM_STOP:
            shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(self._nid))
            user32.DestroyWindow(hwnd)
            return 0
        if msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)
