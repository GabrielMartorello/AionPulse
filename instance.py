# SPDX-License-Identifier: GPL-3.0-only
import ctypes
import hashlib
from ctypes import wintypes


class Instance:
    def __init__(self, path):
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
        self.kernel.CreateMutexW.restype = wintypes.HANDLE
        self.kernel.CreateEventW.argtypes = [
            ctypes.c_void_p,
            wintypes.BOOL,
            wintypes.BOOL,
            wintypes.LPCWSTR,
        ]
        self.kernel.CreateEventW.restype = wintypes.HANDLE
        self.kernel.SetEvent.argtypes = [wintypes.HANDLE]
        self.kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.kernel.WaitForSingleObject.restype = wintypes.DWORD
        name = "Local\\AionPulse-" + hashlib.sha256(str(path).encode()).hexdigest()[:24]
        self.mutex = self.kernel.CreateMutexW(None, False, name)
        if not self.mutex:
            raise ctypes.WinError(ctypes.get_last_error())
        self.existing = ctypes.get_last_error() == 183
        self.event = self.kernel.CreateEventW(None, False, False, name + "-show")
        if not self.event:
            raise ctypes.WinError(ctypes.get_last_error())
        if self.existing:
            self.kernel.SetEvent(self.event)

    def poll(self, root, show):
        if self.kernel.WaitForSingleObject(self.event, 0) == 0:
            show()
        root.after(250, lambda: self.poll(root, show))
