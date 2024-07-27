import sys
import os
import toml

from PyQt5.QtWidgets import *

class OnboardingWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Setup Glacier")
        self.setFixedSize(540, 220)
        # Create a top-level layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        # Create the tab widget with two tabs
        self.tabWidget = QTabWidget()
        self.tabWidget.setStyleSheet("QTabBar::tab { height: 0px; width: 0px; }")
        self.tabWidget.addTab(self.page0UI(), "welcome")
        self.tabWidget.addTab(self.page1UI(), "Default Search Engine")
        self.tabWidget.addTab(self.page2UI(), "Favourites")
        self.tabWidget.addTab(self.page3UI(), "New Tab Page")
        self.tabWidget.addTab(self.page4UI(), "Finish")
        layout.addWidget(self.tabWidget)

    def finish(self):
        self.close()

        search_engine = ""
        search_engine_name = self.searchenginecombobox.currentText()
        if search_engine_name == "DuckDuckGo":
            search_engine = "https://duckduckgo.com/?t=ffab&q=%s"
        elif search_engine_name == 'Google':
            search_engine = "https://www.google.ca/search?q=%s"
        elif search_engine_name == 'Mojeek':
            search_engine = "https://www.mojeek.com/search?q=%s"
        elif search_engine_name == 'Brave Search':
            search_engine = "https://search.brave.com/search?q=%s"
        elif search_engine_name == 'Yahoo':
            search_engine = "https://ca.search.yahoo.com/search?p=%s"
        elif search_engine_name == 'Bing':
            search_engine = "https://www.bing.com/search?q=%s"
        
        newtabpage = ""
        newtabpagetext = self.newtabpagecombobox.currentText()
        if newtabpagetext == 'Default':
            newtabpage = "default"
        if newtabpagetext == 'DuckDuckGo':
            newtabpage = "https://start.duckduckgo.com/"
        if newtabpagetext == 'Google':
            newtabpage = "https://www.google.ca/"

        options = {
            "search_engine_url": search_engine,
            "homepage": newtabpage
        }

        with open(os.path.expanduser('~/.glaciercnfg/config.toml'), 'w') as f:
            f.write(toml.dumps(options))

    def next_tab(self):
        cur_index = self.tabWidget.currentIndex()
        if cur_index < len(self.tabWidget)-1:
            self.tabWidget.setCurrentIndex(cur_index+1)

    def prev_tab(self):
        cur_index = self.tabWidget.currentIndex()
        if cur_index > 0:
            self.tabWidget.setCurrentIndex(cur_index-1)

    def next_prev_btns(self, layout):
        self.widget = QWidget()

        layout_h = QHBoxLayout(self.widget)

        self.prevbtn = QPushButton("Previous")
        self.prevbtn.clicked.connect(self.prev_tab)
        layout_h.addWidget(self.prevbtn)

        self.nextbtn = QPushButton("Next")
        self.nextbtn.clicked.connect(self.next_tab)
        self.nextbtn.setStyleSheet("""
        QPushButton {
            width: 260%;
        }
        """)
        layout_h.addWidget(self.nextbtn)

        layout.addWidget(self.widget)

    def page0UI(self):
        generalTab = QWidget()
        layout = QVBoxLayout()
        hlabel = QLabel("Welcome to Glacier!")
        hlabel.setStyleSheet("QLabel{font-size: 18pt;}")
        layout.addWidget(hlabel)
        label = QLabel("There's lots to explore in the endless sea of Glacier!")
        label.setStyleSheet("QLabel{font-size: 10pt;}")
        layout.addWidget(label)

        self.startsetupbtn = QPushButton("Start setup >")
        self.startsetupbtn.clicked.connect(self.next_tab)
        layout.addWidget(self.startsetupbtn)

        generalTab.setLayout(layout)
        return generalTab

    def page1UI(self):
        generalTab = QWidget()
        layout = QVBoxLayout()
        hlabel = QLabel("Default Search Engine")
        hlabel.setStyleSheet("QLabel{font-size: 18pt;}")
        layout.addWidget(hlabel)

        self.searchenginecombobox = QComboBox()
        self.searchenginecombobox.addItems(['DuckDuckGo', 'Google', 'Mojeek', 'Brave Search', 'Yahoo', 'Bing'])
        layout.addWidget(self.searchenginecombobox)

        self.next_prev_btns(layout)

        generalTab.setLayout(layout)
        return generalTab

    def page2UI(self):
        networkTab = QWidget()
        layout = QVBoxLayout()
        hlabel = QLabel("Select some favourites")
        hlabel.setStyleSheet("QLabel{font-size: 18pt;}")
        layout.addWidget(hlabel)

        self.widget = QWidget()

        layout_h = QHBoxLayout(self.widget)

        favsites = ["Youtube", "Gmail", "Wikipedia", "Netflix", "Twitter", "Reddit"]

        for site in favsites:
            CkBox = QCheckBox(text=site)
            layout_h.addWidget(CkBox)

        layout.addWidget(self.widget)

        self.next_prev_btns(layout)

        networkTab.setLayout(layout)
        return networkTab

    def page3UI(self):
        networkTab = QWidget()
        layout = QVBoxLayout()
        hlabel = QLabel("New Tab Page")
        hlabel.setStyleSheet("QLabel{font-size: 18pt;}")
        layout.addWidget(hlabel)

        self.newtabpagecombobox = QComboBox()
        self.newtabpagecombobox.addItems(['Default', 'DuckDuckGo', 'Google']) # TODO: Add custom new tab option
        layout.addWidget(self.newtabpagecombobox)

        self.next_prev_btns(layout)

        networkTab.setLayout(layout)
        return networkTab

    def page4UI(self):
        finishTab = QWidget()
        layout = QVBoxLayout()
        lbl = QLabel("Welcome to Glacier!")
        lbl.setStyleSheet("QLabel{font-size: 18pt;}")
        layout.addWidget(lbl)
        lbl = QLabel("It's time to start browsing!")
        lbl.setStyleSheet("QLabel{font-size: 13pt;}")
        layout.addWidget(lbl)

        layout.addStretch()

        self.finishbtn = QPushButton("Go Explore the Web!")
        self.finishbtn.setStyleSheet("QPushButton{ font-size: 15pt; }")
        self.finishbtn.clicked.connect(self.finish)
        layout.addWidget(self.finishbtn)

        hlabel = QLabel("Note: You must restart Glacier after finishing onboarding.")
        hlabel.setStyleSheet("QLabel{font-size: 9pt; margin: 0px; }")
        layout.addWidget(hlabel)

        layout.addStretch()

        finishTab.setLayout(layout)
        return finishTab

def start():
    app = QApplication(sys.argv)
    window = OnboardingWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    start()