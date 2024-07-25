from PyQt5.QtCore import *
from PyQt5.QtWidgets import QPushButton, QLineEdit, QGridLayout, QWidget, QApplication, QShortcut, QPlainTextEdit, QSplitter, QTabWidget, QTextEdit
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
import requests
import sys
from lxml.html import fromstring

class DevToolWidget(QWidget):
	def __init__(self, url:str, *args, **kwargs):
		super(DevToolWidget, self).__init__(*args, **kwargs)
		self.layout = QGridLayout()
		self.tabs = QTabWidget()
		self.webview = QWebEngineView()
		self.webview.load(QUrl(url))
		self.headers = QPlainTextEdit(self.getHeaders(url))
		self.headers.setReadOnly(True)
		self.source = QPlainTextEdit(self.getSource(url))
		self.source.setReadOnly(True)
		self.overview = QTextEdit(self.getOverview(url))
		self.overview.setReadOnly(True)
		self.splitter = QSplitter()
		self.splitter.addWidget(self.webview)
		self.splitter.addWidget(self.tabs)
		self.tabs.addTab(self.overview, "Overview")
		self.tabs.addTab(self.source, "Source")
		self.tabs.addTab(self.headers, "Headers")
		self.layout.addWidget(self.splitter, 1, 1)
		self.setLayout(self.layout)
		self.show()
	def getHeaders(self, url:str):
		req = requests.get(url)
		headers  = f"Status: {req.status_code}\n"
		for elm in req.headers:
			headers += f"{elm}: {req.headers[elm]}\n" if len(req.headers[elm]) < 30 else ""
		return headers
	def getSource(self, url:str):
		req = requests.get(url)
		return req.text
	def getOverview(self, url:str):
		response = requests.get(url)
		tree = fromstring(response.content)
		txt = "<h2>Site Information</h2>"
		txt += "<b>" + tree.findtext('.//title') + "</b><br>"
		if len(tree.xpath('/html/head/meta[@name="description"]/@content'))>0:
			txt += "" + tree.xpath('/html/head/meta[@name="description"]/@content')[0] + "<br><br>"
		if "Content-Type" in response.headers:
			txt += "Content Type: <br>" + response.headers["Content-Type"] + "<br><br>"
		txt += f"Total Response Time: <br>{response.elapsed.total_seconds()} seconds<br><br>"
		if len(tree.xpath('//meta[@name="viewport"]/@content'))>0:
			txt += "Viewport: <br>" + tree.xpath('//meta[@name="viewport"]/@content')[0] + "<br><br>"
		if len(tree.xpath('//meta[@charset]/@content'))>0:
			txt += "Charset: <br>" + tree.xpath('//meta[@charset]/@content')[0] + "<br><br>"
		if len(tree.xpath('//html/@lang/@content'))>0:
			txt += "Language: <br>" + tree.xpath('//html/@lang/@content')[0] + "<br><br>"
		if len(tree.xpath("//meta[@name='theme-color']/@content"))>0:
			txt += "Theme Color: <br>" + tree.xpath("//meta[@name='theme-color']/@content")[0] + "<br><br>"
		return txt

if __name__ == '__main__':
	app = QApplication(sys.argv)
	window = DevToolWidget("https://techcrunch.com/")
	app.exec_()
