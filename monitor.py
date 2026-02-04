import xbmc
import time
from service import do_upload

class Monitor(xbmc.Monitor):
    def __init__(self):
        self.check_interval = 3 * 3600  # 3h v sekundách

    def onInit(self):
        if ADDON.getSetting('start_on_boot') == 'true':
            xbmc.executebuiltin('RunScript(script.dame_ftp_upload)')

monitor = Monitor()

while not xbmc.abortRequested():
    if ADDON.getSetting('check_regularly') == 'true':
        do_upload()
        time.sleep(int(ADDON.getSetting('check_frequency')) * 3600)
    if monitor.waitForAbort(1):
        break
