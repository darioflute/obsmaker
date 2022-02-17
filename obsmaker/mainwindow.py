from PyQt5.QtWidgets import (QMainWindow, QApplication, QFileDialog, QWidget,
                             QHBoxLayout)
#from PyQt5.QtCore import Qt
from obsmaker.dialog import TableWidget
from obsmaker.io import readAOR, writeFAOR, replaceBadChar, readSct, readMap
import xml.etree.ElementTree as ET
import sys
import os

from obsmaker import __version__

class GUI(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title = 'Observation maker for FIFI-LS: version ' + __version__
        self.setWindowTitle(self.title)
        # Define main widget
        wid = QWidget()
        self.setCentralWidget(wid)
        mainLayout = QHBoxLayout(wid)
        # Add dialog to main layout
        self.TW = TableWidget(self)
        mainLayout.addWidget(self.TW)
        self.mapListPath = os.getcwd()
        self.sctpath = os.getcwd()
        #self.TWdictionary()
        self.defineActions()
        self.show()

    def defineActions(self):
        self.TW.translateAOR.clicked.connect(self.translateAOR)
        self.TW.loadTemplate.clicked.connect(self.loadTemplate)
        self.TW.loadMapPatternFile.clicked.connect(self.loadMapFile)
        self.TW.exit.clicked.connect(self.exitObsmaker)

    def translateAOR(self):
        """
        Read *aor created with USPOT, split it into multiple parts and save it in *.sct files.
        """
        from unidecode import unidecode
        fd = QFileDialog(None, "Load and translate AOR")
        fd.setLabelText(QFileDialog.Accept, "Import")
        fd.setNameFilters(["AOR Files (*.aor)", "All Files (*)"])
        fd.setOptions(QFileDialog.DontUseNativeDialog)
        fd.setViewMode(QFileDialog.List)
        fd.setFileMode(QFileDialog.ExistingFile)
        if fd.exec():
            fileName= fd.selectedFiles()
            aorfile = fileName[0]
            print('Reading file ', aorfile)
            self.TW.update_status("translateAOR: Reading file " + aorfile + "\n")
            errmsg = ''
            # Save the file path for future reference
            self.pathFile, file = os.path.split(aorfile)
            # Define path of AOR file in the TW class
            self.TW.pathFile = self.pathFile
            tree = ET.ElementTree(file=aorfile)  # or tree = ET.parse(aorfile)
            vector = tree.find('list/vector')
            # Extract Target and Instrument from each AOR
            targets = [item.text for item in vector.findall('Request/target/name')]
            instruments = [item.text for item in vector.findall('Request/instrument/data/InstrumentName')]
            print('targets ', targets)
            print('instruments ', instruments)
            # Unique combinations of target and instrument
            target_inst=list(set(zip(targets,instruments)))
            # get Proposal ID
            PropID = tree.find('list/ProposalInfo/ProposalID').text
            PI = tree.find('list/ProposalInfo/Investigator')
            #PIname = PI.attrib['Honorific'] + ' ' + PI.attrib['FirstName'] + ' ' + PI.attrib['LastName']
            # Get rid of non-ASCII characters
            PIname = unidecode(PI.attrib['FirstName'] + ' ' + PI.attrib['LastName'])
            print('Proposal ID ', PropID)
            print('Proposer ', PIname)
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
                        errmsg += writeFAOR(obs, PropID, PIname,
                            os.path.dirname(os.path.abspath(aorfile)))
                else: errmsg += 'Skipping a non-FIFI-LS aor.\n'
            self.TW.update_status(errmsg)

    def loadTemplate(self):
        """Load a sct file."""
        fd = QFileDialog(None, "Load Scan Template")
        fd.setLabelText(QFileDialog.Accept, "Import")
        fd.setDirectory(self.sctpath)
        fd.setNameFilters(["Scan Template (*.sct)", "All Files (*)"])
        fd.setOptions(QFileDialog.DontUseNativeDialog)
        fd.setViewMode(QFileDialog.List)
        fd.setFileMode(QFileDialog.ExistingFile)
        if fd.exec():
            fileName= fd.selectedFiles()
            sctfile = fileName[0]
            self.title = 'Observation maker for FIFI-LS ['+sctfile+']'
            self.setWindowTitle(self.title)
            # Default settings
            self.TW.setDefaults()
            # Load template and update table widget
            self.TW.update_status('Loading ' + sctfile + "\n")
            self.TW.sctfile = sctfile
            self.aorParameters = readSct(sctfile)
            # self.TW.update_status(errmsg)
            self.TW.update_gui(self.aorParameters)
            self.sctpath = os.path.dirname(os.path.abspath(sctfile))
            # self.TW.sctdir.setText(sctpath) Initiliaze with path of read file
            mapfile = os.path.basename(self.TW.mapListPath)
            self.TW.pathFile = self.sctpath
            self.TW.mapListPath = os.path.join(self.sctpath, mapfile)
            mapfile = self.TW.mapListPath
            print('mapfile ', mapfile)
            self.TW.update_status("mapfile: " + mapfile + "\n")
            if len(mapfile) > 0:
                try:
                    noMapPoints, mapListPath = readMap(mapfile)
                    print('map path ', mapListPath)
                    self.TW.mapListPath = mapListPath
                    self.TW.noMapPoints.setText(str(noMapPoints))
                    print('map loaded')
                    # self.TW.update_status("Map loaded. \n")
                except:
                    print('Invalid map file.')
            # First build
            print('First build ')
            self.TW.buildObs()

    def loadMapFile(self):
        """Load a map file."""
        #fd = QFileDialog()
        #fd.setLabelText(QFileDialog.Accept, "Import")
        #fd.setNameFilters(["Fits Files (*.txt)", "All Files (*)"])
        #fd.setOptions(QFileDialog.DontUseNativeDialog)
        #fd.setViewMode(QFileDialog.List)
        #fd.setFileMode(QFileDialog.ExistingFile)
        #if (fd.exec()):
        #    fileName= fd.selectedFiles()
        #    mapfile = fileName[0]
        #    try:
        #        noMapPoints, mapListPath = readMap(mapfile)
        #        self.TW.mapListPath = mapListPath
        #        self.TW.noMapPoints.setText(str(noMapPoints))
        #    except:
        #        print('Invalid map file.')
        try:
            noMapPoints, mapListPath = readMap()
            self.TW.mapListPath = mapListPath
            self.TW.noMapPoints.setText(str(noMapPoints))
        except:
            print('Invalid map file.')

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
    height = screen_resolution.height()
    gui.setGeometry(width*0.01, 0, width*0.96, height*0.92)  # X, Y, W, H

    sys.exit(app.exec_())
