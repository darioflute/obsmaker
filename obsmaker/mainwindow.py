from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QWidget, QHBoxLayout
from obsmaker.dialog import TableWidget
import sys
import os

class GUI(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title = 'Obs maker'
        self.left = 0
        self.top = 0
        self.width = 300
        self.height = 200
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        # Define main widget
        wid = QWidget()
        self.setCentralWidget(wid)
        mainLayout = QHBoxLayout(wid)
        
        # Add dialog to main layout
        self.TW = TableWidget(self)
        mainLayout.addWidget(self.TW)
        self.defineActions()
        self.show()
        
    def defineActions(self):
        self.TW.loadTemplate.clicked.connect(self.loadTemplate)
        self.TW.exit.clicked.connect(self.exitObsmaker)
        
    def loadTemplate(self):
        fd = QFileDialog()
        fd.setLabelText(QFileDialog.Accept, "Import")
        fd.setNameFilters(["Fits Files (*.aor)", "All Files (*)"])
        fd.setOptions(QFileDialog.DontUseNativeDialog)
        fd.setViewMode(QFileDialog.List)
        fd.setFileMode(QFileDialog.ExistingFile)
        if (fd.exec()):
            fileName= fd.selectedFiles()
            print('Reading file ', fileName[0])
            # Save the file path for future reference
            self.pathFile, file = os.path.split(fileName[0])
            self.loadFile(fileName[0])
            # ... other actions here
    
    def exitObsmaker(self):
        self.close()
    
    def loadFile(self, filename):
        print('Here the file is read')
        
        
def main():
    from obsmaker import __version__
    print('Obsmaker version ', __version__)
    app = QApplication(sys.argv)
    app.setApplicationName('OBSMAKER')
    app.setApplicationVersion(__version__)
    gui = GUI()
    # Adjust geometry to size of the screen
    screen_resolution = app.desktop().screenGeometry()
    width = screen_resolution.width()
    gui.setGeometry(width*0.1, 0, width*0.5, width*0.2)

    sys.exit(app.exec_())