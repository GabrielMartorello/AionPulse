# SPDX-License-Identifier: GPL-3.0-only
import ctypes
from ctypes import wintypes


def apply_window_icon(root, path):
    user = ctypes.WinDLL("user32", use_last_error=True)
    user.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    user.GetAncestor.restype = wintypes.HWND
    user.LoadImageW.argtypes = [
        wintypes.HINSTANCE,
        wintypes.LPCWSTR,
        wintypes.UINT,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.UINT,
    ]
    user.LoadImageW.restype = wintypes.HANDLE
    user.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user.SendMessageW.restype = wintypes.LPARAM
    hwnd = user.GetAncestor(root.winfo_id(), 2)
    root._native_icons = []
    for kind, size in ((0, 16), (1, 32)):
        icon = user.LoadImageW(None, str(path), 1, size, size, 0x10)
        if not icon:
            raise ctypes.WinError(ctypes.get_last_error())
        user.SendMessageW(hwnd, 0x80, kind, icon)
        root._native_icons.append(icon)
