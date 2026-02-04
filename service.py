import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon
import ftplib
import os
import time
import glob
import pickle
import threading
from datetime import datetime

ADDON = xbmcaddon.Addon('script.dame_ftp_upload')
DATA_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
STATE_FILE = os.path.join(DATA_PATH, 'file_states.pkl')

def log(msg):
    xbmc.log(f"[DAME FTP UPLOAD] {msg}", xbmc.LOGINFO)

def load_states():
    try:
        with open(STATE_FILE, 'rb') as f:
            return pickle.load(f)
    except:
        return {}

def save_states(states):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'wb') as f:
        pickle.dump(states, f)

def test_ftp():
    try:
        server = ADDON.getSetting('ftp_server')
        port = int(ADDON.getSetting('ftp_port'))
        user = ADDON.getSetting('ftp_user')
        pwd = ADDON.getSetting('ftp_password')
        passive = ADDON.getSetting('ftp_passive') == 'true'
        
        ftp = ftplib.FTP()
        ftp.connect(server, port)
        ftp.login(user, pwd)
        ftp.set_pasv(passive)
        ftp.quit()
        xbmcgui.Dialog().ok('Test OK', 'FTP spojenie úspešné.')
        log('Test connection successful')
    except Exception as e:
        xbmcgui.Dialog().ok('Test failed', str(e))
        log(f'Test connection failed: {e}')

def upload_file(ftp, local_path, remote_path):
    try:
        with open(local_path, 'rb') as f:
            ftp.storbinary(f'STOR {remote_path}', f)
        log(f'Uploaded: {local_path}')
        return True
    except Exception as e:
        log(f'Upload failed {local_path}: {e}')
        return False

def do_upload(force=False):
    source_base = xbmcvfs.translatePath(ADDON.getSetting('source_dir'))
    mask = ADDON.getSetting('file_mask')
    
    if not xbmcvfs.exists(source_base):
        log('Source dir not exists')
        return
    
    states = load_states() if not force else {}
    
    ftp_dir = ADDON.getSetting('ftp_dir').lstrip('/')
    server = ADDON.getSetting('ftp_server')
    port = int(ADDON.getSetting('ftp_port'))
    user = ADDON.getSetting('ftp_user')
    pwd = ADDON.getSetting('ftp_password')
    passive = ADDON.getSetting('ftp_passive') == 'true'
    
    try:
        ftp = ftplib.FTP()
        ftp.connect(server, port)
        ftp.login(user, pwd)
        ftp.cwd('/' + ftp_dir)
        ftp.set_pasv(passive)
    except Exception as e:
        log(f'FTP connect failed: {e}')
        return
    
    pattern = os.path.join(source_base, mask)
    files = glob.glob(pattern)
    
    progress = xbmcgui.DialogProgress()
    progress.create('FTP Upload', 'Pripojujem...')
    progress.update(0)
    
    uploaded = 0
    for i, local_file in enumerate(files):
        mtime = os.path.getmtime(local_file)
        state_mtime = states.get(os.path.basename(local_file), 0)
        
        if force or mtime > state_mtime:
            rel_path = os.path.basename(local_file)
            if upload_file(ftp, local_file, rel_path):
                states[rel_path] = mtime
                uploaded += 1
        
        pct = int((i + 1) / len(files) * 100)
        progress.update(pct, f'Spracovávam: {os.path.basename(local_file)}')
        if progress.iscanceled():
            break
    
    ftp.quit()
    progress.close()
    
    save_states(states)
    xbmcgui.Dialog().ok('Upload hotový', f'Nahralo sa {uploaded} súborov.')

if __name__ == '__main__':
    param = xbmc.executebuiltin('XBMC.RunPlugin({})'.format(xbmc.getsysarg(1)[1:]))
    if 'test' in xbmc.getsysarg(1):
        test_ftp()
    elif 'force' in xbmc.getsysarg(1):
        do_upload(True)
    else:
        do_upload()
