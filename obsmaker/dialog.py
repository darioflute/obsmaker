from PyQt5.QtWidgets import (QPushButton, QWidget, QTabWidget,QVBoxLayout, QHBoxLayout, QComboBox,
                             QLabel, QLineEdit, QFormLayout)
from PyQt5.QtCore import Qt

class TableWidget(QWidget):
    
    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Read defaults
        self.readDefaults()
        
        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = self.createWidget('H')
        self.tab2 = self.createWidget('H')
        
        # Add tabs
        self.tabs.addTab(self.tab1, "Telescope")
        self.tabs.addTab(self.tab2, "Arrays")
        
        # Telescope tab
        self.col1 = self.createWidget('F', self.tab1.layout)
        self.col2 = self.createWidget('F', self.tab1.layout)
        self.col3 = self.createWidget('F', self.tab1.layout)
        
        # Col 1
        c1 = self.col1.layout
        self.loadTemplate = self.createButton('Load AOR template')
        self.exit = self.createButton('Exit ')
        c1.addRow(self.loadTemplate, self.exit)
       
        self.buildObservation = self.createButton('Build observation')
        self.writeObservation = self.createButton('Write observation')
        c1.addRow(self.buildObservation, self.writeObservation)

        self.observationID = self.createEditableBox("None", 40, "Observation ID: ", c1)
        self.objectType = self.addComboBox('Object type: ', self.obstypes, c1)
       
        self.filegpIDred = self.createEditableBox('None', 40, 'File Group ID Red: ', c1)
        self.filegpIDblue = self.createEditableBox('None', 40, 'File Group ID Blue: ', c1)        
        self.sourceType = self.addComboBox('Source type: ', self.sourcetypes, c1 )
        self.aorID = self.createEditableBox('None', 40, 'AOR ID: ', c1)
        self.targetName = self.createEditableBox('None', 40, 'Target name: ', c1)
        self.targetRA = self.createEditableBox('00 00 00.0', 40, 'Target RA: ', c1)
        self.targetDec = self.createEditableBox('+00 00 00.0', 40, 'Target Dec: ', c1)
        self.redshift = self.createEditableBox('0', 40)
        self.redshiftUnits = QComboBox()
        self.redshiftUnits.addItems(["Target vel (cz) [km/s]", "Target redshift (z)"])
        c1.addRow(self.redshiftUnits, self.redshift)
        self.detectorAngle = self.createEditableBox('0', 40, 'Detector angle (E of N): ', c1)
        observingmodes = ["Symmetric chop", "Asymmetric chop"]
        self.observingMode = self.addComboBox('Observing mode: ', observingmodes, c1)
        self.primaryArray = self.addComboBox('Primary array: ', ["Red", "Blue", "Setpoint"], c1)
        self.setpoint = self.createEditableBox('N/A', 40, 'Setpoint: ', c1)
        self.col1.layout.addRow(QLabel('Observing stats'),None)
        self.rawIntTime = self.createEditableBox('', 40, 'Raw integration time (s): ', c1)
        self.onsourceIntTime = self.createEditableBox('', 40, 'On source integration time (s): ', c1)
        self.estObsTime = self.createEditableBox('', 40, 'Estimated observation time (s): ', c1)
        # Col 2
        c2 = self.col2.layout
        c2.addRow(QLabel('Nod Pattern'),None)
        nodpatterns = ['ABBA','AB','A','ABA','AABAA']
        self.nodPattern = self.addComboBox('Nod pattern: ', nodpatterns, c2)
        self.nodcyclesPerMapPosition = self.createEditableBox('1', 20, 'Nod cycles per map position: ', c2)
        self.gratingDirection = self.addComboBox('Grating direction: ', ['Up','Down','None','Split'], c2)
        self.scanFilesPerSplit = self.createEditableBox('N/A', 40, 'Scan files per split: ', c2)
        self.rewindMode = self.addComboBox('LOS rewind mode: ', ['Auto', 'Manual'], c2)

        c2.addRow(QLabel('Off position'),None)
        items = ['Matched', 'Absolute', 'Relative to target', 'Relative to active map pos']
        self.offPosition = self.addComboBox('Off position: ', items, c2)
        self.lambdaOffPos = self.createEditableBox('', 40, 'Off Position Lambda [arcsec]: ',c2)
        self.betaOffPos = self.createEditableBox('', 40, 'Off Position Beta [arcsec]: ', c2)
        self.mapOffPos = self.createEditableBox('', 40, 'Off Position map reduction: ', c2)
        c2.addRow(QLabel('Mapping pattern'),None)
        c2.addRow(QLabel('Map center offset from target'),None)
        self.coordSysMapCenter = self.addComboBox('Coordinate system: ', self.mapcoordsys, c2)        
        self.lambdaMapCenter = self.createEditableBox('', 40, 'Lambda [arcsec]: ', c2)
        self.betaMapCenter = self.createEditableBox('', 40, 'Beta [arcsec]: ', c2)
        self.mapPattern = self.addComboBox('Mapping pattern: ', ['File', 'Manual'], c2)        
        self.noMapPoints = self.createEditableBox('', 40,'No of map points: ',c2)
        self.mapStepSize = self.createEditableBox('', 40, 'Step size [arcsec]: ', c2)
        self.loadMapPatternFile= self.createButton('Load file')
        c2.addRow(QLabel('Mapping pattern: '), self.loadMapPatternFile)
        
        # Col 3
        c3 = self.col3.layout
        c3.addRow(QLabel('Chopper setup'),None)
        self.chopScheme = self.addComboBox('Chop scheme: ', self.chopschemes, c3)
        self.coordSysChop = self.addComboBox('Coordinate system: ', self.chopcoordsys, c3)        
        self.chopAmp = self.createEditableBox('', 40,'Chop amplitude (1/2 throw): ', c3)        
        self.chopPosAngle = self.createEditableBox('', 40,'Chop pos angle (S of E): ', c3)  
        self.chopPhase = self.createEditableBox('356', 40)
        self.chopPhaseMode = QComboBox()
        self.chopPhaseMode.addItems(["Chopper phase default", "Chopper phase manual"])
        c3.addRow(self.chopPhaseMode, self.chopPhase)
        #self.chopPhaseDefault = self.createEditableBox('356', 40,'Chopper phase default: ', c3)
        #self.chopPhaseManual = self.createEditableBox('N/A', 40,'Chopper phase manual: ', c3)
        self.chopLengthFrequency = self.createEditableBox('', 40, 'Chop frequency [Hz] ', c3)
        self.chopLengthSamples = self.createEditableBox('64', 40, 'Chop samples per position ', c3)
        self.trackingInB = self.addComboBox('Tracking in B (asymmetric): ', ['On', 'Off'], c3) 
        c3.addRow(QLabel('Input params per mapping position'),None)
        self.onSourceTimeChop = self.createEditableBox('', 40, 'On-source time: ', c3)
        self.noGratPosChop = self.createEditableBox('', 40, 'No of grating positions:  ', c3)
        self.totGratPositions = self.createEditableBox('1', 40, 'Total no of mapping positions: ', c3)
        self.chopCompute = self.createButton('Compute')
        c3.addRow(self.chopCompute, None)
        self.nodCycles = self.createEditableBox('', 40, 'No of nod cycles: ', c3)
        self.ccPerGratPos = self.createEditableBox('', 40, 'No of CC per grating pos: ', c3)
        self.loadScanDescriptionFile= self.createButton('Load file')
        self.noGratPos4Nod = self.createEditableBox('', 40, 'No of grating pos per nod: ', c3)
        self.gratCycle4Nod = self.createEditableBox('', 40, 'Grating cycle per nod (30.0): ', c3)
        self.timeCompleteMap = self.createEditableBox('', 40, 'Time to complete map [min]: ', c3)
        c3.addRow(QLabel('Scan description file: '), self.loadScanDescriptionFile)
        
        # Arrays tab
        self.col4 = self.createWidget('F', self.tab2.layout)
        self.col5 = self.createWidget('F', self.tab2.layout)
        
        # Column 4 (Red array)
        c4 = self.col4.layout
        c4.addRow(QLabel('Red Array [100-210 um]'),None)
        self.setDichroic = self.addComboBox('Dichroic: ', ['105 um', '130 um'], c4)
        c4.addRow(QLabel(''),None)
        self.redLine = self.addComboBox('Line: ', self.redlines, c4)  
        self.redWave = self.addComboBox('Wavelength [um]: ', self.redwaves, c4)
        
        self.redOffset = self.createEditableBox('0', 40)
        self.redOffsetUnits = QComboBox()
        self.redOffsetUnits.addItems(["Line offset [um]:", "Line offset [units]:"])
        c4.addRow(self.redOffsetUnits, self.redOffset)
        self.redGratPosMicron = self.createEditableBox('', 50, 'Grating position [um]: ', c4)
        c4.addRow(QLabel('Spectral mode'),None)
        items = ['Center', 'Dither', 'Inward', 'Start']
        self.redGratPattern = self.addComboBox('Grating movement pattern: ', items, c4)
        self.redStepSizeUp = self.createEditableBox('0', 40, 'Step size up [pixels]: ', c4)
        self.redGratPosUp = self.createEditableBox('1', 40, 'Grating position up: ', c4)
        self.redStepSizeDown = self.createEditableBox('0', 40, 'Step size down [pixels]: ', c4)
        self.redGratPosDown = self.createEditableBox('0', 40, 'Grating position down: ', c4)
        c4.addRow(QLabel('Timing and sensitivity'),None)
        self.redRampLengthSamples = self.createEditableBox('32', 40, 'Ramp length [samples]: ', c4)
        self.redRampLengthMs = self.createEditableBox('32', 40, 'Ramp length [ms]: ', c4)
        self.redRamp4ChopPos = self.createEditableBox('', 40, 'Ramps per chop pos: ', c4)
        self.redCC4ChopPos = self.createEditableBox('1', 40, 'CC per chop pos: ', c4)
        self.redGratCycles = self.createEditableBox('1', 40, 'Number of grating cycles: ', c4)
        self.redZeroBias = self.createEditableBox('60', 40, 'Zero bias [mV]: ', c4)
        self.redBiasR = self.createEditableBox('0', 40, 'BiasR [mV]: ', c4)
        self.redCapacitor = self.addComboBox('Capacitor [uF]: ', self.capacitors, c4)
        self.redScanFileLength = self.createEditableBox('', 40, 'Scan file length [s]: ', c4)
        
        # Column 5 (Blue array)
        c5 = self.col5.layout
        c5.addRow(QLabel('Blue Array [48-130 um]'),None)
        items = ['First (70-130 um)', 'Second (48-72 um)']
        self.setOrder = self.addComboBox('Order: ', items, c5)
        self.setFilter = self.addComboBox('Filter: ', ['1', '2'], c5)
        self.blueLine = self.addComboBox('Line: ', self.bluelines, c5)  
        self.blueWave = self.addComboBox('Wavelength [um]: ', self.bluewaves, c5)        
        self.blueOffset = self.createEditableBox('0', 40)
        self.blueOffsetUnits = QComboBox()
        self.blueOffsetUnits.addItems(["Line offset [um]:", "Line offset [units]:"])
        c5.addRow(self.blueOffsetUnits, self.blueOffset)
        self.blueGratPosMicron = self.createEditableBox('', 50, 'Grating position [um]: ', c5)
        c5.addRow(QLabel('Spectral mode'),None)
        items = ['Center', 'Dither', 'Inward', 'Start']
        self.blueGratPattern = self.addComboBox('Grating movement pattern: ', items, c5)
        self.blueStepSizeUp = self.createEditableBox('0', 40, 'Step size up [pixels]: ', c5)
        self.blueGratPosUp = self.createEditableBox('1', 40, 'Grating position up: ', c5)
        self.blueStepSizeDown = self.createEditableBox('0', 40, 'Step size down [pixels]: ', c5)
        self.blueGratPosDown = self.createEditableBox('0', 40, 'Grating position down: ', c5)
        c5.addRow(QLabel('Timing and sensitivity'),None)
        self.blueRampLengthSamples = self.createEditableBox('32', 40, 'Ramp length [samples]: ', c5)
        self.blueRampLengthMs = self.createEditableBox('32', 40, 'Ramp length [ms]: ', c5)
        self.blueRamp4ChopPos = self.createEditableBox('', 40, 'Ramps per chop pos: ', c5)
        self.blueCC4ChopPos = self.createEditableBox('1', 40, 'CC per chop pos: ', c5)
        self.blueGratCycles = self.createEditableBox('1', 40, 'Number of grating cycles: ', c5)
        self.blueZeroBias = self.createEditableBox('60', 40, 'Zero bias [mV]: ', c5)
        self.blueBiasR = self.createEditableBox('0', 40, 'BiasR [mV]: ', c5)
        self.blueCapacitor = self.addComboBox('Capacitor [uF]: ', self.capacitors, c5)
        self.blueScanFileLength = self.createEditableBox('', 40, 'Scan file length [s]: ', c5)
        
        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        
    def readDefaults(self):  
        """Read input file with defaults."""
        import json
        import os
        this_dir = os.path.dirname(os.path.realpath(__file__))
        file = os.path.join(this_dir, "data", "defaults.json")
        with open(file) as f:
            config = json.load(f)
        self.refTargetSystems = config["obs_ref_target_systems"]
        self.redlines = config["obs_ref_red_lines"]
        self.redwaves = config["obs_ref_red_lambdas"]
        self.bluelines = config["obs_ref_blue_lines"]
        self.bluewaves = config["obs_ref_blue_lambdas"]
        self.refpatterns = config["obs_ref_patterns"]
        self.obstypes = config["obs_ref_obstypes"]
        self.chopschemes = config["obs_ref_chop_schemes"]
        self.chopcoordsys = config["obs_ref_chopcoord_systems"]
        self.mapcoordsys = config["obs_ref_mapcoord_systems"]
        self.sourcetypes = config["obs_ref_srctypes"]
        self.instmodes = config["obs_ref_instmodes"]
        self.capacitors = config["obs_ref_red_capacitors"]
        
        
    def addComboBox(self, text, items, layout=None):
        a = QComboBox()
        a.addItems(items)
        if layout is not None:
            layout.addRow(QLabel(text), a)
        return a
        
    def createEditableBox(self, text, size, label='None', layout=None):
        box = QLineEdit()
        box.setText(text)
        box.resize(size,40)
        if layout is not None:
            layout.addRow(QLabel(label), box)
        return box
        
    def createWidget(self, direction, layout=None):
        a = QWidget()
        if direction == 'H':
            a.layout = QHBoxLayout(a)
        elif direction == 'V':
            a.layout = QVBoxLayout(a)
        elif direction == 'F':
            a.layout = QFormLayout(a)
            a.layout.setLabelAlignment(Qt.AlignLeft)
            a.layout.setAlignment(Qt.AlignLeft)
        if layout is not None:
            layout.addWidget(a)
        return a
    
    def createButton(self, action, layout=None):
        a = QPushButton(action)
        if layout is not None:
            layout.addWidget(a)
        return a
    
    def addLabel(self, text, layout=None):
        label = QLabel()
        label.setText(text)
        label.setAlignment(Qt.AlignCenter)
        if layout is not None:
            layout.addWidget(label)
        return label