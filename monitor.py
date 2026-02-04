#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xbmc
import threading
import time
import xbmcaddon

from service import log, upload_files

ADDON = xbmcaddon.Addon('script.dame_ftp_upload')

def periodic_check():
    while not xbmc.abortRequested():
        if ADDON.getSetting("check_regularly") == "true":
            freq = float(ADDON.getSetting("check_frequency")) * 3600
            upload_files()
            time.sleep(max(freq, 3600))  # Min 1h
        else:
            time.sleep(1800)  # Check settings 30min

if __name__ == '__main__':
    log("Service spustený")
    if ADDON.getSetting("start_on_boot") == "true":
        upload_files()
    
    check_thread = threading.Thread(target=periodic_check, daemon=True)
    check_thread.start()
    
    while not xbmc.abortRequested():
        xbmc.sleep(1000)
    log("Service ukončený")
