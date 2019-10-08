from PyQt5.QtWidgets import (QMainWindow, QApplication, QFileDialog, QWidget, 
                             QHBoxLayout)
#from PyQt5.QtCore import Qt
from obsmaker.dialog import TableWidget
from obsmaker.io import readAOR, writeFAOR, replaceBadChar, readSct
import xml.etree.ElementTree as ET
import sys
import os

class GUI(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title = 'Observation maker for FIFI-LS'
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
        self.mapListPath = ''
        #self.TWdictionary()
        self.defineActions()
        self.show()
        
    def defineActions(self):
        self.TW.translateAOR.clicked.connect(self.translateAOR)
        self.TW.loadTemplate.clicked.connect(self.loadTemplate)
        self.TW.exit.clicked.connect(self.exitObsmaker)
        
    def translateAOR(self):
        """
        Read *aor created with USPOT, split it into multiple parts and save it in *.sct files.
        """
        fd = QFileDialog()
        fd.setLabelText(QFileDialog.Accept, "Import")
        fd.setNameFilters(["Fits Files (*.aor)", "All Files (*)"])
        fd.setOptions(QFileDialog.DontUseNativeDialog)
        fd.setViewMode(QFileDialog.List)
        fd.setFileMode(QFileDialog.ExistingFile)
        if (fd.exec()):
            fileName= fd.selectedFiles()
            aorfile = fileName[0]
            print('Reading file ', aorfile)
            errmsg = ''
            # Save the file path for future reference
            self.pathFile, file = os.path.split(aorfile)
            tree = ET.ElementTree(file=aorfile)  # or tree = ET.parse(aorfile)
            vector = tree.find('list/vector')
            # Extract Target and Instrument from each AOR
            targets = [(item.text) for item in vector.findall(
                    'Request/target/name')]
            instruments = [(item.text) for item in vector.findall(
                           'Request/instrument/data/InstrumentName')]
            # Unique combinations of target and instrument
            target_inst=list(set(zip(targets,instruments)))
            # get Proposal ID
            PropID = tree.find('list/ProposalInfo/ProposalID').text
            if PropID == None:
                PropID = "00_0000"    # indicates no PropID
            for combo in target_inst:  # Loop over Target-Instrument combo
                tree = ET.ElementTree(file=aorfile)
                vector = tree.find('list/vector')
                # remove non-relevant AORs
                for elem in vector.findall('Request'):
                    name = elem.find('target/name').text
                    inst = elem.find('instrument/data/InstrumentName').text
                    if (name, inst) != combo:
                        vector.remove(elem)
                # create root, PropID_Target_Inst
                root = PropID + '_' + combo[0] + '_' + combo[1]
                # replace some reserved characters with '_'
                root = replaceBadChar(root)
                inst = combo[1]
                if inst == 'FIFI-LS':
                    requests = vector.findall('Request')
                    for aor in requests:
                        obs = readAOR(aor)
                        # FIFI-LS wants sct and map files to be in the same directory
                        # as the input aorfile, so set that as outdir
                        print('write translated AOR')
                        errmsg += writeFAOR(obs, PropID, os.path.dirname(os.path.abspath(aorfile)))
            return errmsg
        
    def loadTemplate(self):
        """Load a sct file."""
        fd = QFileDialog()
        fd.setLabelText(QFileDialog.Accept, "Import")
        fd.setNameFilters(["Fits Files (*.sct)", "All Files (*)"])
        fd.setOptions(QFileDialog.DontUseNativeDialog)
        fd.setViewMode(QFileDialog.List)
        fd.setFileMode(QFileDialog.ExistingFile)
        if (fd.exec()):
            fileName= fd.selectedFiles()
            sctfile = fileName[0]
            # Load template and update table widget
            self.aorParameters = readSct(sctfile)
            self.TW.update(self.aorParameters)
            

    def exitObsmaker(self):
        self.close()
            
        
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