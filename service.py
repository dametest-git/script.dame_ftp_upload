#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon
import ftplib
import os
import glob
import pickle
import socket

ADDON = xbmcaddon.Addon('script.dame_ftp_upload')
DATA_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
STATE_FILE = os.path.join(DATA_PATH, 'file_states.pkl')

def log(msg):
    xbmc.log(f"[DAME_FTP_UPLOAD] {msg}", xbmc.LOGINFO)

def get_states():
    try:
        with open(STATE_FILE, 'rb') as f:
            return pickle.load(f)
    except:
        return {}

def save_states(states):
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, 'wb') as f:
            pickle.dump(states, f)
    except Exception as e:
        log(f"Save states error: {e}")

def ftp_connect():
    server = ADDON.getSetting('ftp_server')
    port = int(ADDON.getSetting('ftp_port') or 21)
    user = ADDON.getSetting('ftp_user')
    pwd = ADDON.getSetting('ftp_password')
    passive = ADDON.getSetting('ftp_passive') == 'true'
    ftp_dir = ADDON.getSetting('ftp_dir').lstrip('/')
    
    ftp = ftplib.FTP()
    ftp.connect(server, port, timeout=10)
    ftp.login(user, pwd)
    ftp.set_pasv(passive)
    ftp.cwd(f'/{ftp_dir}')
    return ftp

def test_connection():
    try:
        ftp = ftp_connect()
        ftp.quit()
        xbmcgui.Dialog().ok('Test úspešný', 'FTP pripojenie funguje.')
        log('FTP test OK')
        return True
    except Exception as e:
        xbmcgui.Dialog().ok('Test zlyhal', str(e))
        log(f"FTP test failed: {e}")
        return False

def upload_files(force=False):
    source_dir = xbmcvfs.translatePath(ADDON.getSetting('source_dir'))
    mask = ADDON.getSetting('file_mask') or 'epg*.xml'
    
    if not os.path.isdir(source_dir):
        xbmcgui.Dialog().ok('Chyba', f'Zdrojový adresár neexistuje: {source_dir}')
        return
    
    states = {} if force else get_states()
    pattern = os.path.join(source_dir, mask)
    files = glob.glob(pattern)
    
    if not files:
        xbmcgui.Dialog().ok('Žiadne súbory', f'Žiadne súbory pre masku: {mask}')
        return
    
    try:
        ftp = ftp_connect()
    except:
        return
    
    dialog = xbmcgui.DialogProgress()
    dialog.create('FTP Upload', 'Pripravujem...')
    dialog.update(0)
    
    count = 0
    total = len(files)
    for idx, fpath in enumerate(files):
        try:
            mtime = os.path.getmtime(fpath)
            fname = os.path.basename(fpath)
            if force or states.get(fname, 0) < mtime:
                with open(fpath, 'rb') as fl:
                    ftp.storbinary(f'STOR {fname}', fl)
                states[fname] = mtime
                count += 1
                log(f"Nahral: {fname}")
            
            pct = int(100 * (idx + 1) / total)
            dialog.update(pct, f"Nahrávam {fname}")
            if dialog.iscanceled():
                break
        except Exception as e:
            log(f"Chyba {fpath}: {e}")
    
    ftp.quit()
    dialog.close()
    save_states(states)
    xbmcgui.Dialog().ok('Hotovo', f"Nahralo {count}/{total} súborov.")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "upload"
    log(f"Spustené s parametrom: {mode}")
    
    if mode == "test":
        test_connection()
    elif mode == "force":
        upload_files(True)
    else:
        upload_files(False)
    xbmc.executebuiltin("XBMC.ActivateWindow(Home)")
