from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtPrintSupport import *
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlSchemeHandler, QWebEngineUrlScheme
from PyQt5 import QtCore, QtWidgets, QtWebEngineCore, QtWebEngineWidgets

import urllib.parse
import os
import sys
import json
import validators
import feedparser
import random
from functools import partial
import webbrowser
import toml
import pathlib
import re
import tkinter as tk
from tkinter import ttk
from tkinter import *
import requests

# Imports from files
from components import adblock, devtools

version = "0.01"
is_64bits = sys.maxsize > 2**32


def show_settings():
    with open(os.path.expanduser('~/.glaciercnfg/config.toml').replace("\\", "/")) as f:
        configfile = f.read()

    root = tk.Tk()
    root.title('Settings')

    window_width = 1000
    window_height = 800

    # get the screen dimension
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # find the center point
    center_x = int(screen_width/2 - window_width / 2)
    center_y = int(screen_height/2 - window_height / 2)

    # set the position of the window to the center of the screen
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

    label = ttk.Label(text="Settings").pack(side="top")

    def saveInput():
        inp = inputtxt.get(1.0, "end-1c")
        with open(os.path.expanduser('~/.glaciercnfg/config.toml').replace("\\", "/"), "w") as f:
            f.write(inp)

    # TextBox Creation
    inputtxt = tk.Text(root, height=45, width=window_width)

    inputtxt.pack()

    inputtxt.insert(END, configfile)

    # Button Creation
    printButton = tk.Button(root, text="Save Settings", command=saveInput)
    printButton.pack()

    label = ttk.Label(
        text="You will have to restart Glacier for the changes to take effect.").pack(side="top")

    root.mainloop()


class AboutDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super(AboutDialog, self).__init__(*args, **kwargs)

        QBtn = QDialogButtonBox.Ok  # No cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()

        title = QLabel("Glacier")
        font = title.font()
        font.setPointSize(20)
        title.setFont(font)

        layout.addWidget(title)

        logo = QLabel()
        logo.setPixmap(QPixmap(os.path.join(
            glacier_path, 'images', 'icon.png')))
        layout.addWidget(logo)

        layout.addWidget(QLabel("Version " + version))

        for i in range(0, layout.count()):
            layout.itemAt(i).setAlignment(Qt.AlignHCenter)

        layout.addWidget(self.buttonBox)

        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBarDoubleClicked.connect(self.tab_open_doubleclick)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)

        self.tabs.setStyleSheet("""
                        QTabWidget {
                            background: #ffffff;
                        }
                        QTabBar {
                            background: #e7eaed;
                        }
                        QTabBar::tab {
                            background: #e7eaed;
                            padding: 7px;
                            color: #000000;
                            margin-top: -1px;
                            margin-bottom: -1px;
                            margin-left: 1pt solid black;
                            margin-right: 1pt solid black;
                            border: 1px solid #000000;
                            border-radius: 4px;
                            width: 200px;
                        }
                        QTabBar::tab:hover {
                            background: #f0f0f0;
                        }
                        QTabBar::tab:selected {
                            background: #ffffff;
                            color: #000000;
                        }
                        """)

        self.setCentralWidget(self.tabs)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self.cmd_prompt = QLineEdit()
        self.cmd_prompt.returnPressed.connect(self.do_cmd)
        self.statusBar().addWidget(self.cmd_prompt)
        self.cmd_prompt.hide()

        names = ["/quit", "/newtab", "/reload", "/close_current_tab",
                 "/new_window", "/o", "/add_bookmark", "/show_license", "/help", "/open_internet_archive"]
        self.cmd_prompt.setCompleter(QCompleter(names))

        navtb = QToolBar("Navigation")
        navtb.setIconSize(QSize(16, 16))
        self.addToolBar(navtb)

        back_btn = QAction(
            QIcon(os.path.join(glacier_path, 'images', 'arrow-180.png')), "Back", self)
        back_btn.setStatusTip("Back to previous page")
        back_btn.triggered.connect(lambda: self.tabs.currentWidget().back())
        navtb.addAction(back_btn)

        next_btn = QAction(
            QIcon(os.path.join(glacier_path, 'images', 'arrow-000.png')), "Forward", self)
        next_btn.setStatusTip("Forward to next page")
        next_btn.triggered.connect(lambda: self.tabs.currentWidget().forward())
        navtb.addAction(next_btn)

        reload_btn = QAction(QIcon(os.path.join(
            glacier_path, 'images', 'arrow-circle-315.png')), "Reload", self)
        reload_btn.setStatusTip("Reload page")
        reload_btn.triggered.connect(
            lambda: self.tabs.currentWidget().reload())
        navtb.addAction(reload_btn)

        home_btn = QAction(
            QIcon(os.path.join(glacier_path, 'images', 'home.png')), "Home", self)
        home_btn.setStatusTip("Go home")
        home_btn.triggered.connect(self.navigate_home)
        navtb.addAction(home_btn)

        navtb.addSeparator()

        self.httpsicon = QLabel()  # Yes, really!
        self.httpsicon.setPixmap(QPixmap(os.path.join(
            glacier_path, 'images', 'lock-nossl.png')))
        navtb.addWidget(self.httpsicon)

        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        self.urlbar.setFont(QFont("Arial", 10))
        self.urlbar.setStyleSheet("""""")
        self.urlbar.setStyleSheet("""
        QLineEdit {
            border-radius: 10px;
            padding: 4px;
        }
        QLineEdit:hover {
            border-radius: 10px;
            padding: 4px;
            border-width: 1px;
            border-style: solid;
            border-color: qlineargradient(spread:pad, x1:0.5, y1:1, x2:0.5, y2:0, stop:0 rgba(0, 113, 255, 255), stop:1 rgba(91, 171, 252, 255));
        }
        """)
        navtb.addWidget(self.urlbar)

        add_bookmark_btn = QAction(QIcon(os.path.join(
            glacier_path, 'images', 'star.png')), "Add a new bookmark", self)
        add_bookmark_btn.setStatusTip("Add a new bookmark")
        add_bookmark_btn.triggered.connect(self.add_bookmark)
        navtb.addAction(add_bookmark_btn)

        stop_btn = QAction(
            QIcon(os.path.join(glacier_path, 'images', 'cross-circle.png')), "Stop", self)
        stop_btn.setStatusTip("Stop loading current page")
        stop_btn.triggered.connect(lambda: self.tabs.currentWidget().stop())
        navtb.addAction(stop_btn)

        if config["show_experimental_buttons"] == "yes":
            rss_btn = QAction(
                QIcon(os.path.join(glacier_path, 'images', 'rss-solid.png')), "Rss", self)
            rss_btn.setStatusTip("RSS")
            rss_btn.triggered.connect(lambda: self.display_rss_feeds())
            navtb.addAction(rss_btn)

        menu = QMenu(self)

        new_tab_action = QAction(
            QIcon(os.path.join('images', 'ui-tab--plus.png')), "New Tab", self)
        new_tab_action.triggered.connect(lambda _: self.add_new_tab())
        menu.addAction(new_tab_action)

        open_file_action = QAction(
            QIcon(os.path.join('images', 'disk--arrow.png')), "Open file...", self)
        open_file_action.triggered.connect(self.open_file)
        menu.addAction(open_file_action)

        webdev_tools_action = QAction(
            QIcon(os.path.join('images', 'wrench.png')), "Open Web Developer Tools", self)
        webdev_tools_action.triggered.connect(self.open_webdev_tools)
        menu.addAction(webdev_tools_action)

        devmode_action = QAction("Open page in Developer Mode", self)
        devmode_action.triggered.connect(self.devtools)
        menu.addAction(devmode_action)

        settings_action = QAction(
            QIcon(os.path.join('images', 'wrench.png')), "Settings", self)
        settings_action.triggered.connect(show_settings)
        menu.addAction(settings_action)

        history_action = QAction("History", self)
        history_action.triggered.connect(self.history)
        menu.addAction(history_action)

        toggle_js_action = QAction("Toggle Javascript", self)
        toggle_js_action.triggered.connect(self.toggle_javascript)
        menu.addAction(toggle_js_action)

        bookmarks_action = QAction("Bookmarks", self)
        bookmarks_action.triggered.connect(
            lambda _: self.add_new_tab(QUrl("glacier://bookmarks")))
        menu.addAction(bookmarks_action)

        wayback_action = QAction("Go Back with the Internet Archive", self)
        wayback_action.triggered.connect(self.open_internet_archive)
        menu.addAction(wayback_action)

        about_action = QAction(
            QIcon(os.path.join('images', 'question.png')), "About Glacier", self)
        about_action.triggered.connect(self.about)
        menu.addAction(about_action)

        option_btn = QAction(
            QIcon(os.path.join(glacier_path, 'images', 'blank.png')), "Option", self)
        option_btn.setMenu(menu)
        navtb.addAction(option_btn)

        self.menuBar().setNativeMenuBar(False)

        file_menu = self.menuBar().addMenu("&File")

        new_tab_action = QAction(QIcon(os.path.join(
            glacier_path, 'images', 'ui-tab--plus.png')), "New Tab", self)
        new_tab_action.setStatusTip("Open a new tab")
        new_tab_action.triggered.connect(lambda _: self.add_new_tab())
        file_menu.addAction(new_tab_action)

        open_file_action = QAction(QIcon(os.path.join(
            glacier_path, 'images', 'disk--arrow.png')), "Open file...", self)
        open_file_action.setStatusTip("Open from file")
        open_file_action.triggered.connect(self.open_file)
        file_menu.addAction(open_file_action)

        save_file_action = QAction(QIcon(os.path.join(
            glacier_path, 'images', 'disk--pencil.png')), "Save Page As...", self)
        save_file_action.setStatusTip("Save current page to file")
        save_file_action.triggered.connect(self.save_file)
        file_menu.addAction(save_file_action)

        email_page_action = QAction("Email Page To...", self)
        email_page_action.setStatusTip("Email current page")
        email_page_action.triggered.connect(self.mailpageto)
        file_menu.addAction(email_page_action)

        print_action = QAction(
            QIcon(os.path.join(glacier_path, 'images', 'printer.png')), "Print...", self)
        print_action.setStatusTip("Print current page")
        print_action.triggered.connect(self.print_page)
        file_menu.addAction(print_action)

        quit_action = QAction("Quit", self)
        quit_action.setStatusTip("Quit glacier")
        quit_action.triggered.connect(quit)
        file_menu.addAction(quit_action)

        bookmarks_menu = self.menuBar().addMenu("&Bookmarks")

        bookmarks_file = open(glacier_path + 'bookmarks.txt', 'r')
        bookmarks = bookmarks_file.readlines()

        for bookmark in range(0, len(bookmarks)):
            locals()["bookmark_action_" + bookmarks[bookmark]
                     ] = QAction(bookmarks[bookmark], self)
            locals()["bookmark_action_" + bookmarks[bookmark]
                     ].setStatusTip("Open " + bookmarks[bookmark])
            locals()["bookmark_action_" + bookmarks[bookmark]
                     ].triggered.connect(partial(self.open_bookmark, bookmarks[bookmark]))
            bookmarks_menu.addAction(
                locals()["bookmark_action_" + bookmarks[bookmark]])

        bookmarks_file.close()

        help_menu = self.menuBar().addMenu("&Help")

        about_action = QAction(QIcon(os.path.join(
            glacier_path, 'images', 'question.png')), "About Glacier", self)
        about_action.setStatusTip("Find out more about Glacier")
        about_action.triggered.connect(self.about)
        help_menu.addAction(about_action)

        self.printer = QPrinter()

        try:
            if validators.url(sys.argv[1]):
                self.add_new_tab(QUrl(sys.argv[1]), '')
            else:
                self.add_new_tab(QUrl(homepage), 'Homepage')
        except:
            self.add_new_tab(QUrl(homepage), 'Homepage')

        self.shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        self.shortcut.activated.connect(self.add_new_tab)

        self.shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        self.shortcut.activated.connect(
            lambda: self.tabs.currentWidget().reload())

        self.shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        self.shortcut.activated.connect(
            lambda: self.close_current_tab(self.tabs.currentIndex()))

        self.shortcut = QShortcut(QKeySequence("Ctrl+/"), self)
        self.shortcut.activated.connect(self.toggle_cmd_prompt)

        self.shortcut = QShortcut(QKeySequence("Ctrl+U"), self)
        self.shortcut.activated.connect(self.view_source)

        # opening window in maximized size
        self.showMaximized()

        self.show()

        self.setWindowTitle("Glacier")

        self.setWindowIcon(
            QIcon(os.path.join(glacier_path, 'images', 'icon.png')))

        global jsEnabled
        jsEnabled = True
        self.tabs.currentWidget().page().settings().setAttribute(
            QWebEngineSettings.JavascriptEnabled, jsEnabled)
        self.tabs.currentWidget().page().profile().setHttpUserAgent(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )

        leftToolBar = QToolBar("Quickbar", self)
        leftToolBar.setMovable(False)
        self.addToolBar(Qt.LeftToolBarArea, leftToolBar)

        self.addToQuickSidebar(leftToolBar, "https://static.vecteezy.com/system/resources/previews/002/557/425/original/google-mail-icon-logo-isolated-on-transparent-background-free-vector.jpg", "https://gmail.com/", "Gmail")
        self.addToQuickSidebar(leftToolBar, "https://www.youtube.com/favicon.ico", "https://www.youtube.com/", "Youtube")
        self.addToQuickSidebar(leftToolBar, "https://en.wikipedia.org/favicon.ico", "https://en.wikipedia.org", "Wikipedia")
        self.addToQuickSidebar(leftToolBar, "https://www.netflix.com/favicon.ico", "https://www.netflix.com/", "Netflix")

    def addToQuickSidebar(self, leftToolBar, icon, url, name):
        response = requests.get(icon)
        pixmap = QPixmap()
        pixmap.loadFromData(response.content)
        myicon = QIcon(pixmap)
        yt_btn = QAction(myicon, name, self)
        yt_btn.setStatusTip(name)
        yt_btn.triggered.connect(lambda: self.add_new_tab(QUrl(url)))
        leftToolBar.addAction(yt_btn)

    def getBookmarks(self):
        bookmarks_file = open(glacier_path + 'bookmarks.txt', 'r')
        bookmarks = bookmarks_file.readlines()

        bookmarks_file.close()

        return bookmarks

    def mailpageto(self):
        text, ok = QInputDialog.getText(
            self, 'Email Page To...', 'Please enter the recipient\'s email address')
        if ok:
            webbrowser.open("mailto:" + text + "?subject=!LINK!&body=!LINK!")

    def open_webdev_tools(self):
        with open("devConsole.js") as my_file:
            self.tabs.currentWidget().page().runJavaScript(my_file.read())

    def add_bookmark(self):
        currentTabUrl = self.tabs.currentWidget().url().toString()

        bookmarksFile = open(glacier_path + 'bookmarks.txt', 'r')
        bookmarksFileLines = bookmarksFile.readlines()

        containsBookmark = False
        for bookmarksFileLine in bookmarksFileLines:
            if bookmarksFileLine.strip() == currentTabUrl.strip():
                containsBookmark = True
                break

        bookmarksFile.close()

        if not containsBookmark:
            with open(glacier_path + 'bookmarks.txt', 'a') as file:
                file.write('\n' + currentTabUrl)

    def view_source(self):
        url = self.urlbar.text()
        if not url.startswith('view-source:'):
            self.add_new_tab(QUrl("view-source:" + url))

    def open_bookmark(self, bookmark):
        self.add_new_tab(QUrl(bookmark.strip()))

    def do_cmd(self):
        cmd = self.cmd_prompt.text()
        if cmd.startswith("/"):
            cmd = cmd[1:]
        else:
            self.status.showMessage("Command must start with a slash.", 2000)
            self.cmd_prompt.setText("")
            self.cmd_prompt.hide()
            return

        if cmd == "quit":
            sys.exit()
        elif cmd == "newtab":
            self.add_new_tab()
        elif cmd == "reload":
            self.tabs.currentWidget().reload()
        elif cmd == "close_current_tab":
            self.close_current_tab(self.tabs.currentIndex())
        elif cmd == "new_window":
            self.show_new_window()
        elif cmd.startswith("o "):
            self.navigate_to_url(cmd.replace("o ", ""))
        elif cmd == "add_bookmark":
            self.add_bookmark()
        elif cmd == "show_license":
            window.add_new_tab(QUrl("file:///LICENSE"))
        elif cmd == "help":
            window.add_new_tab(QUrl("file:///html/help.html"))
        elif cmd == "open_internet_archive":
            self.open_internet_archive()
        elif cmd == "":
            self.status.showMessage("No command given", 2000)
        else:
            self.status.showMessage(cmd + ": no such command", 2000)

        self.cmd_prompt.setText("")
        self.cmd_prompt.hide()

    def toggle_cmd_prompt(self):
        self.cmd_prompt.show()
        self.cmd_prompt.setText("/")
        self.cmd_prompt.setFocus()

    @pyqtSlot("QWebEngineDownloadItem*")
    def on_downloadRequested(self, download):
        old_path = download.url().path()  # download.path()
        suffix = QFileInfo(old_path).suffix()
        path, _ = QFileDialog.getSaveFileName(
            self, "Save File", old_path, "*." + suffix
        )
        if path:
            download.setPath(path)
            download.accept()

    def add_new_tab(self, qurl=None, label="New Tab"):

        try:
            sysargv1 = sys.argv[1]
        except:
            sysargv1 = homepage

        if qurl is None:
            qurl = QUrl(homepage)

        browser = QWebEngineView()
        profile = QWebEngineProfile("default", browser)
        interceptor = WebEngineUrlRequestInterceptor()
        profile.setUrlRequestInterceptor(interceptor)
        webpage = WebPage(browser)
        browser.setPage(webpage)
        QWebEngineProfile.defaultProfile().downloadRequested.connect(
            self.on_downloadRequested)
        browser.settings().setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        browser.page().fullScreenRequested.connect(lambda request: request.accept())
        browser.loadFinished.connect(self.onLoadFinished)
        browser.setUrl(qurl)
        newtabI = self.tabs.addTab(browser, label)
        newtab = self.tabs.widget(newtabI)

        self.tabs.setTabIcon(newtabI, browser.page().icon())

        url = qurl.toString()
        if qurl.scheme() == "glacier":
            html = ""
            print(url)
            print(url.split("/")[2])
            if url.split("/")[2] == "about":
                with open(glacier_path + "html/about.html", 'r') as f:
                    html = f.read()
            elif url.split("/")[2] == "newtab":
                with open(glacier_path + "html/newtab.html", 'r') as f:
                    html = f.read()
            elif url.split("/")[2] == "welcome":
                with open(glacier_path + "html/welcome.html", 'r') as f:
                    html = f.read()
            elif url.split("/")[2] == "history":
                html += "<title>History</title>"
                for j in self.tabs.currentWidget().page().history().backItems(100):
                    html = "<br>" + html
                    html = "<p><strong>" + j.title() + "</strong>" + "    <span style='color: grey;'>" + \
                        j.url().toString() + "</span></p>" + html
                html = "<br>" + html
                html = "<p><strong>" + self.tabs.currentWidget().page().title() + "</strong>" + "    <span style='color: grey;'>" + \
                    self.tabs.currentWidget().page().url().toString() + "</span></p>" + html
            elif url.split("/")[2] == "bookmarks":
                html += "<title>Bookmarks</title>"
                for j in self.getBookmarks():
                    html += "<a href='" + j + "'>" + j + "</a><br>"
            elif url.split("/")[2].split("?")[0] == "dev":
                print(url.split("?")[1])
                t = self.tabs.currentWidget().page().title()
                self.tabs.addTab(devtools.DevToolWidget(url.split("?")[1]), t + " - Developer Mode")
                self.tabs.removeTab(newtabI)

            newtab.setHtml(html)
        else:
            # More difficult! We only want to update the url when it's from the
            # correct tab
            browser.urlChanged.connect(lambda qurl, browser=browser:
                                       self.update_urlbar(qurl, browser))

        if type(self.tabs.widget(newtabI)) == QtWebEngineWidgets.QWebEngineView and not url.startswith("glacier:"):
            browser.loadFinished.connect(lambda _, i=newtabI, browser=browser:
                                        self.setWindowTitle(self.tabs.currentWidget().page().title() + " - Glacier"))

            browser.loadFinished.connect(lambda _, i=newtabI, browser=browser:
                                        self.tabs.setTabText(newtabI, self.tabs.currentWidget().page().title()[:30]))

            global jsEnabled
            browser.loadFinished.connect(lambda _, i=newtabI, browser=browser:
                                        self.tabs.currentWidget().page().settings().setAttribute(QWebEngineSettings.JavascriptEnabled, jsEnabled))

            browser.iconChanged.connect(lambda _, i=newtabI, browser=browser:
                                        self.tabs.setTabIcon(newtabI, browser.icon()))

        self.tabs.setCurrentIndex(newtabI)

    def onLoadFinished(self, ok):
        if type(self.tabs.currentWidget()) == QtWebEngineWidgets.QWebEngineView:
            if is_64bits:
                bits = "64-bit"
            else:
                bits = "32-bit"
            if ok:
                if self.tabs.currentWidget().page().url().toString() == "file:///html/about.html":
                    self.tabs.currentWidget().page().runJavaScript(
                        "document.getElementById('glacier_version').innerHTML = 'Version " + version + " (" + bits + ")';")

                if self.tabs.currentWidget().page().url().toString() == "file:///html/newtab.html":
                    self.tabs.currentWidget().page().runJavaScript(
                        "document.getElementById('searchform').action = '" + search_engine_url.split("?")[0] + "';")

                if not self.tabs.currentWidget().page().url().toString().startswith("file:///"):
                    self.tabs.currentWidget().page().runJavaScript("""
                    var r = document.getElementsByTagName('script');

                    for (var i = (r.length-1); i >= 0; i--) {
                        if(r[i].src.includes("pagead") || r[i].src.includes("ad")){
                            r[i].parentNode.removeChild(r[i]);
                        }
                    }
                    """)

    def tab_open_doubleclick(self, i):
        if i == -1:  # No tab under the click
            self.add_new_tab()

    def current_tab_changed(self, i):
        if type(self.tabs.currentWidget()) == QtWebEngineWidgets.QWebEngineView:
            qurl = self.tabs.currentWidget().url()
            self.update_urlbar(qurl, self.tabs.currentWidget())
            self.update_title(self.tabs.currentWidget())

    def close_current_tab(self, i):
        if self.tabs.count() < 2:
            return

        self.tabs.removeTab(i)

    def update_title(self, browser):
        if browser != self.tabs.currentWidget():
            # If this signal is not from the current tab, ignore
            return

        title = self.tabs.currentWidget().page().title()
        self.setWindowTitle("%s - Glacier" % title)

    def about(self):
        self.add_new_tab(QUrl("file:///html/about.html"), "About Glacier")

    def history(self):
        self.add_new_tab(QUrl("glacier://history"), "History")

    def devtools(self):
        self.add_new_tab(QUrl("glacier://dev?" + self.tabs.currentWidget().url().toString()), "Dev Tools")

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open file", "",
                                                  "Hypertext Markup Language (*.htm *.html);;"
                                                  "All files (*.*)")

        if filename:
            with open(filename, 'r') as f:
                html = f.read()

            self.tabs.currentWidget().setHtml(html)
            self.urlbar.setText(filename)

    def save_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Page As", "",
                                                  "Hypertext Markup Language (*.htm *html);;"
                                                  "All files (*.*)")

        if filename:
            html = self.tabs.currentWidget().page().mainFrame().toHtml()
            with open(filename, 'w') as f:
                f.write(html.encode('utf8'))

    def open_internet_archive(self):
        self.add_new_tab(QUrl("https://web.archive.org/web/20230000000000*/" +
                         self.tabs.currentWidget().url().toString()))

    def print_page(self):
        dlg = QPrintDialog(self.printer)
        if dlg.exec_():
            self.browser.page().print(self.printer, self.print_completed)

    def print_completed(self, success):
        self.status.showMessage(success, 2000)

    def navigate_home(self):
        self.tabs.currentWidget().setUrl(QUrl(homepage))

    def navigate_to_url(self, url=None):
        if url is None:
            url = self.urlbar.text()

        if url.startswith(":yt "):
            url = url.replace(":yt ", "https://www.youtube.com/results?search_query=")

        q = QUrl(url)
        if q.scheme() == "":
            if validators.url("http://" + url):
                q = QUrl("http://" + url)
            else:
                q = QUrl(search_engine_url.replace("%s", url))

        self.tabs.currentWidget().setUrl(q)

    def update_urlbar(self, q, browser=None):

        if browser != self.tabs.currentWidget():
            # If this signal is not from the current tab, ignore
            return

        if q.scheme() == 'https':
            # Secure padlock icon
            self.httpsicon.setPixmap(
                QPixmap(os.path.join(glacier_path, 'images', 'lock-ssl.png')))

        else:
            # Insecure padlock icon
            self.httpsicon.setPixmap(QPixmap(os.path.join(
                glacier_path, 'images', 'lock-nossl.png')))

        self.urlbar.setText(q.toString())
        self.urlbar.setCursorPosition(0)

    def display_rss_feeds(self):
        self.should_show_rss_msg = True
        rss_msg_box = QMessageBox()
        rss_msg_box.setIcon(QMessageBox.Information)
        rss_msg_box.buttonClicked.connect(self.rss_feed_button_pressed)
        rss_msg_box.addButton(QPushButton('Next'), QMessageBox.YesRole)
        rss_msg_box.addButton(QPushButton('Cancel'), QMessageBox.RejectRole)

        rssFeeds = open(glacier_path + 'rssFeeds.txt', 'r')
        rssFeedLines = rssFeeds.readlines()

        for line in rssFeedLines:
            NewsFeed = feedparser.parse(line)

            for entry in NewsFeed.entries:
                try:
                    if self.should_show_rss_msg == False:
                        break
                    rss_msg_box.setText(entry.published + "\n" + "------Summary------" +
                                        "\n" + entry.summary + "\n" + "------Link------" + "\n" + entry.link)
                    retval = rss_msg_box.exec_()
                except:
                    pass

    def rss_feed_button_pressed(self, i):
        if i.text() == "Cancel":
            self.should_show_rss_msg = False

    def toggle_javascript(self):
        global jsEnabled
        jsEnabled = not jsEnabled
        self.tabs.currentWidget().page().settings().setAttribute(
            QWebEngineSettings.JavascriptEnabled, jsEnabled)


class WebEngineUrlRequestInterceptor(QtWebEngineCore.QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        url = info.requestUrl().toString()


class WebPage(QWebEnginePage):
    _windows = {}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.featurePermissionRequested.connect(
            self.handleFeaturePermissionRequested)
        self.geometryChangeRequested.connect(self.handleGeometryChange)

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        print("javaScriptConsoleMessage: ", message, "   ", sourceID)

    @pyqtSlot(QUrl, QWebEnginePage.Feature)
    def handleFeaturePermissionRequested(self, securityOrigin, feature):
        title = "Permission Request"
        questionForFeature = {
            QWebEnginePage.Geolocation: "Allow {feature} to access your location information?",
            QWebEnginePage.MediaAudioCapture: "Allow {feature} to access your microphone?",
            QWebEnginePage.MediaVideoCapture: "Allow {feature} to access your webcam?",
            QWebEnginePage.MediaAudioVideoCapture: "Allow {feature} to access your webcam and microphone?",
            QWebEnginePage.DesktopVideoCapture: "Allow {feature} to capture video of your desktop?",
            QWebEnginePage.DesktopAudioVideoCapture: "Allow {feature} to capture audio and video of your desktop?"
        }
        question = questionForFeature.get(feature)
        if question:
            question = question.format(feature=securityOrigin.host())
            if QMessageBox.question(self.view().window(), title, question) == QMessageBox.Yes:
                self.setFeaturePermission(
                    securityOrigin, feature, QWebEnginePage.PermissionGrantedByUser)
            else:
                self.setFeaturePermission(
                    securityOrigin, feature, QWebEnginePage.PermissionDeniedByUser)

    def acceptNavigationRequest(self, url,  _type, isMainFrame):
        urlString = url.toString()
        redirecting = False

        #if "google.com" in urlString:
        #    urlString = urlString.replace(
        #        "google.com", "duckduckgo.com")
        #    redirecting = True
        if redirecting:
            window.navigate_to_url(urlString)

        path = glacier_path + 'userscripts'
        list_of_files = []

        for root, dirs, files in os.walk(path):
            for file in files:
                list_of_files.append(os.path.join(root, file))
        for name in list_of_files:
            with open(name.replace("\\", "/")) as my_file:
                lines = my_file.readlines()

                runUserscript = True

                for line in lines:
                    if "@match" in line.strip():
                        match = line.strip()
                        match = match.replace(" ", "")
                        match = match.replace("//@match", "")
                        runUserscript = False
                        if match in urlString:
                            runUserscript = True
                            print("Running userscript: " + name.replace("\\", "/"))

                js = ""
                for line in lines:
                    if not line.strip().startswith("//"):
                        js += line.strip() + "\n"

                if runUserscript:
                    self.runJavaScript(js)

        return True

    @classmethod
    def newWindow(cls):
        window = QWebEngineView()
        window.setObjectName(f'window-{id(window)}')
        window.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        window.destroyed.connect(
            lambda window: cls._windows.pop(window.objectName(), None))
        window.setPage(cls(window))
        cls._windows[window.objectName()] = window
        return window

    def handleGeometryChange(self, rect):
        view = self.view()
        window = QtGui.QWindow.fromWinId(view.winId())
        if window is not None:
            rect = rect.marginsRemoved(window.frameMargins())
        view.resize(rect.size())
        view.show()

    def createWindow(self, mode):
        window = self.newWindow()
        if mode != QtWebEngineWidgets.QWebEnginePage.WebDialog:
            window.resize(800, 600)
            window.show()
        return window.page()


app = QApplication(sys.argv)
app.setApplicationName("Glacier")
app.setOrganizationName("glacier")

glacier_path = str(pathlib.Path(__file__).parent.resolve()) + "/"

# Think forward not backwards
glacier_path = glacier_path.replace("\\", "/")

try:
    with open(os.path.expanduser('~/.glaciercnfg/config.toml').replace("\\", "/"), 'r') as f:
        config = toml.loads(f.read())
except FileNotFoundError:
    print("Config file not found.")
    print("Config file should be located in: " + os.path.expanduser('~/.glaciercnfg/config.toml').replace("\\", "/"))
    print("Aborting program.")
    exit()
except Exception as e:
    print("error with opening config file" + e.message)

with open(glacier_path + "themes/" + config['theme'] + ".qss", 'r') as f:
    style = f.read()
    # Set the stylesheet of the application
    app.setStyleSheet(style)

if 'homepage' in config:
    if config['homepage'] == "default":
        homepage = "file:///html/newtab.html"
    else:
        homepage = config['homepage']
else:
    homepage = "file:///html/newtab.html"

if 'search_engine_url' in config:
    if config['search_engine_url'] == "default":
        search_engine_url = "https://duckduckgo.com/?t=ffab&q=%s"
    else:
        search_engine_url = config['search_engine_url']
else:
    search_engine_url = "https://duckduckgo.com/?t=ffab&q=%s"

window = MainWindow()
app.exec_()
