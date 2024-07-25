from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtCore import *
import requests

class RequestManager(QWebEngineUrlRequestInterceptor):
    """
    This subclass works as a gate. The WebView instances are sending their requests to this class.
    We then decide either that a request is valid and doesn't contain any ads (look at interceptRequest) or a request is an ad and we block it.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def setup(self):
        res = requests.get("https://easylist.to/easylist/easylist.txt").content.decode()
        self.blist = res.split("\n")
        for i in self.blist:
            if i.startswith("!") or i.startswith("##") or i.startswith("["):
                self.blist.remove(i)
        del self.blist[len(self.blist)-1]


    def interceptRequest(self, info):
        requrl = info.requestUrl().toString()
        for host in self.blist:
            if "*" in host:
                host = host.replace("*", "")
            if host in requrl:
                info.block(True)
                print(f"\n\nblocking {requrl}\n\n")
            else:
                pass