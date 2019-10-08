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
        
        # Default
        self.mapListPath = ''
        
        # Col 1
        c1 = self.col1.layout
        self.translateAOR = self.createButton('Load and translate AOR')
        c1.addRow(self.translateAOR,None)
        self.loadTemplate = self.createButton('Load template')
        self.exit = self.createButton('Exit ')
        c1.addRow(self.loadTemplate, self.exit)
       
        self.buildObservation = self.createButton('Build observation')
        self.writeObservation = self.createButton('Write observation')
        c1.addRow(self.buildObservation, self.writeObservation)

        self.observationID = self.createEditableBox("None", 40, "Observation ID: ", c1)
        self.observationType = self.addComboBox('Observation type: ', self.obstypes, c1)
       
        self.filegpIDred = self.createEditableBox('None', 40, 'File Group ID Red: ', c1)
        self.filegpIDblue = self.createEditableBox('None', 40, 'File Group ID Blue: ', c1)        
        self.sourceType = self.addComboBox('Source type: ', self.sourcetypes, c1 )
        self.aorID = self.createEditableBox('None', 40, 'AOR ID: ', c1)
        self.targetName = self.createEditableBox('None', 40, 'Target name: ', c1)
        self.targetRA = self.createEditableBox('00 00 00.0', 40, 'Target RA: ', c1)
        self.targetDec = self.createEditableBox('+00 00 00.0', 40, 'Target Dec: ', c1)
        self.redshift = self.createEditableBox('0', 40, 'Redshift [z]: ', c1)
        self.detectorAngle = self.createEditableBox('0', 40, 'Detector angle (E of N): ', c1)
        observingmodes = ["Symmetric", "Asymmetric"]
        #observingmodes = ["Beam switching", "Unmatched nodding"]
        self.observingMode = self.addComboBox('Observing mode: ', observingmodes, c1)
        self.instrumentalMode = self.addComboBox('Instrumental mode: ', self.instmodes, c1)
        self.primaryArray = self.addComboBox('Primary array: ', ["Red", "Blue", "Setpoint"], c1)
        self.setpoint = self.createEditableBox('n/a', 40, 'Setpoint: ', c1)
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
        self.scanFilesPerSplit = self.createEditableBox('n/a', 40, 'Scan files per split: ', c2)
        self.rewindMode = self.addComboBox('LOS rewind mode: ', ['Auto', 'Manual'], c2)

        c2.addRow(QLabel('Off position'),None)
        items = ['Matched', 'Absolute', 'Relative to target', 'Relative to active map pos']
        self.offPosition = self.addComboBox('Off position: ', items, c2)
        self.lambdaOffPos = self.createEditableBox('', 40, 'Off Position Lambda [arcsec]: ',c2)
        self.betaOffPos = self.createEditableBox('', 40, 'Off Position Beta [arcsec]: ', c2)
        self.mapOffPos = self.createEditableBox('', 40, 'Off Position map reduction: ', c2)
        c2.addRow(QLabel('Mapping pattern'),None)
        c2.addRow(QLabel('Map center offset from target'),None)
        self.coordSysMap = self.addComboBox('Coordinate system: ', self.mapcoordsys, c2)        
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
        self.chopPhaseMode.addItems(["Default", "Manual"])
        self.chopPhaseMode.currentIndexChanged.connect(self.chopPhaseChange)
        self.add2widgets('Chopper Phase: ', self.chopPhaseMode, self.chopPhase, c3)
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
        self.gratpatterns = ['Centre', 'Dither', 'Inward dither', 'Start']
        c4.addRow(QLabel('Red Array [100-210 um]'),None)
        self.setDichroic = self.addComboBox('Dichroic: ', ['105', '130'], c4)
        c4.addRow(QLabel(''),None)
        self.redLine = self.addComboBox('Line: ', self.redlines, c4)
        self.redWave = self.createEditableBox('', 50, 'Wavelength [um]', c4)
        self.redLine.currentIndexChanged.connect(self.redLineChange)
        self.redOffsetUnits = QComboBox()
        self.redOffsetUnits.addItems(["kms", "um", "units"])
        self.redOffset = QLineEdit('0')
        self.add2widgets('Line offset: ', self.redOffset, self.redOffsetUnits, c4)
        self.redGratPosMicron = self.createEditableBox('', 50, 'Grating position [um]: ', c4)
        c4.addRow(QLabel('Spectral mode'),None)
        self.redGratPattern = self.addComboBox('Grating movement pattern: ', self.gratpatterns, c4)
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
        self.blueLine.currentIndexChanged.connect(self.blueLineChange)
        self.blueWave = self.createEditableBox('', 50, 'Wavelength [um]', c5)
        self.blueOffsetUnits = QComboBox()
        self.blueOffsetUnits.addItems(["kms", "um", "units"])
        self.blueOffset = QLineEdit('0')
        self.add2widgets('Line offset: ', self.blueOffset, self.blueOffsetUnits, c5)
        self.blueGratPosMicron = self.createEditableBox('', 50, 'Grating position [um]: ', c5)
        c5.addRow(QLabel('Spectral mode'),None)
        self.blueGratPattern = self.addComboBox('Grating movement pattern: ', self.gratpatterns, c5)
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
        
        # Define conversion
        self.defineConversion()
        
        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        
    def blueLineChange(self, index):
        """If new line selected, populate the wavelength."""
        self.blueWave.setText(self.bluewaves[index])
        
    def redLineChange(self, index):
        """If new line selected, populate the wavelength."""
        self.redWave.setText(self.redwaves[index])

    def chopPhaseChange(self, index):
        """Put default phase value is default is selected."""
        if index == 0:
            self.chopPhase.setText('356')

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
        
    def add2widgets(self, text, widget1, widget2, layout):
        box = QWidget()
        box.layout = QHBoxLayout(box)
        box.layout.setContentsMargins(0, 0, 0, 0)
        box.layout.addWidget(widget1)
        box.layout.addWidget(widget2)
        layout.addRow(QLabel(text), box)
        
    def addComboBox(self, text, items, layout=None):
        a = QComboBox()
        a.addItems(items)
        if layout is not None:
            layout.addRow(QLabel(text), a)
        return a
        
    def createEditableBox(self, text, size, label='None', layout=None):
        box = QLineEdit(text)
        #box.setText(text)
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
    
    def defineConversion(self):
        self.k2tw = {
                'OBSMODE'          :self.observingMode,
                'PRIMARYARRAY'	   :self.primaryArray,
                'NODPATTERN'	   :self.nodPattern,
                'REWIND'	       :self.rewindMode,
                'OFFPOS'	       :self.offPosition,
                'CHOPPHASE'	       :self.chopPhaseMode,
                'DICHROIC'	       :self.setDichroic,
                'ORDER'		       :self.setOrder,
                'RED_LAMBDA'       :self.redGratPattern,
                'BLUE_LAMBDA'	   :self.blueGratPattern,
                'TRACKING'	       :self.trackingInB,
                'SCANDIST'	       :self.gratingDirection,
                'RED_LINE'	       :self.redLine,
                'RED_OFFSET_TYPE'  :self.redOffsetUnits, 
                'BLUE_LINE'	       :self.blueLine,
                'BLUE_OFFSET_TYPE' :self.blueOffsetUnits,
                'BLUE_FILTER'	   :self.setFilter,
                'PATTERN'	       :self.mapPattern,
                'RED_CAPACITOR'	   :self.redCapacitor,
                'BLUE_CAPACITOR'   :self.blueCapacitor,
                'CHOPCOORD_SYSTEM' :self.coordSysChop,
                'MAPCOORD_SYSTEM'  :self.coordSysMap,
                'OBSTYPE'	       :self.observationType,
                'SRCTYPE'	       :self.sourceType,
                'INSTMODE'	       :self.instrumentalMode,
                'OBSID'		       :self.observationID,
                'AORID'		       :self.aorID,
                'FILEGP_R'	       :self.filegpIDred,
                'FILEGP_B'	       :self.filegpIDblue,
                'REDSHIFT'	       :self.redshift,
                'TARGET_NAME'	   :self.targetName,
                'TARGET_LAMBDA'	   :self.targetRA,
                'TARGET_BETA'	   :self.targetDec,
                'SETPOINT'	       :self.setpoint,
                'NODCYCLES'	       :self.nodCycles,
                'SPLITS'	       :self.scanFilesPerSplit,
                'OFFPOS_LAMBDA'	   :self.lambdaOffPos,
                'OFFPOS_BETA'	   :self.betaOffPos,
                'OFFPOS_REDUC'	   :self.mapOffPos,
                'DITHMAP_LAMBDA'   :self.lambdaMapCenter,
                'DITHMAP_BETA'	   :self.betaMapCenter,
                'DETANGLE'	       :self.detectorAngle,
                'MAPLISTPATH'	   :self.mapListPath,
                'DITHMAP_NUMPOINTS':self.noMapPoints,
                'DITHMAP_STEPSIZE' :self.mapStepSize,
                'CHOP_AMP'	       :self.chopAmp,
                'CHOP_POSANG'	   :self.chopPosAngle,
                'CHOP_MANUALPHASE' :self.chopPhase,
                'CHOP_LENGTH'	   :self.chopLengthSamples,
                'RED_MICRON'	   :self.redWave,
                'RED_OFFSET'	   :self.redOffset,
                'RED_SIZEUP'	   :self.redStepSizeUp,
                'RED_POSUP'	       :self.redGratPosUp,
                'RED_SIZEDOWN'	   :self.redStepSizeDown,
                'RED_POSDOWN'	   :self.redGratPosDown,
                'RED_RAMPLEN'	   :self.redRampLengthSamples,
                'RED_CHOPCYC'	   :self.redCC4ChopPos,
                'RED_GRTCYC'	   :self.redGratCycles,
                'RED_ZBIAS'	       :self.redZeroBias,
                'RED_BIASR'	       :self.redBiasR,
                'BLUE_MICRON'	   :self.blueWave,
                'BLUE_OFFSET'	   :self.blueOffset,
                'BLUE_SIZEUP'	   :self.blueStepSizeUp,
                'BLUE_POSUP'	   :self.blueGratPosUp,
                'BLUE_SIZEDOWN'	   :self.blueStepSizeDown,
                'BLUE_POSDOWN'	   :self.blueGratPosDown,
                'BLUE_RAMPLEN'	   :self.blueRampLengthSamples,
                'BLUE_CHOPCYC'	   :self.blueCC4ChopPos,
                'BLUE_GRTCYC'	   :self.blueGratCycles,
                'BLUE_ZBIAS'	   :self.blueZeroBias,
                'BLUE_BIASR'       :self.blueBiasR
            }
        
    def update(self, dictionary):
        """Update with values from *.sct file."""
        
        for key in dictionary.keys():
            label = self.k2tw[key]
            if isinstance(label, QLineEdit):
                try:
                    label.setText(dictionary[key])
                except:
                    print(key + 'is unkown.')
            elif isinstance(label, QComboBox):
                try:
                    index = label.findText(dictionary[key], Qt.MatchFixedString)
                    label.setCurrentIndex(index)
                except:
                    print(key + 'is unkown.')
            else:  # No widget, just variable
                self.k2tw[key] = dictionary[key]
                # I should maybe read this file and update the gui immediately

        # Check if chopper phase mode is default and put default value
        if dictionary['CHOPPHASE'] == 'Default' :
            self.chopPhase.setText('356')

