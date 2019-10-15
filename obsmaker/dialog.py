from PyQt5.QtWidgets import (QWidget, QTabWidget,QVBoxLayout, QComboBox, 
                             QLabel, QLineEdit, QMessageBox)
from PyQt5.QtCore import Qt, QObject
import os
import math
import numpy as np
from obsmaker.grating import inductosyn2wavelength, wavelength2inductosyn
from obsmaker.io import (velocity2z, writeSct, readMap, add2widgets, addComboBox,
                         createEditableBox, createWidget, createButton)

def mround(number, multiple):
    """
    MS Excel's MROUND function.  Rounds up number to the closest integer
    multiple of multiple if number % multiple is greater than
    multiple / 2.
    """
    num = int(number / multiple)
    rem = number % multiple
    if rem > multiple / 2.:
        return multiple * (num + 1)
    else:
        return multiple * num


class TableWidget(QWidget):
    
    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Read defaults
        self.readDefaults()
        self.pathFile = ''
        
        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = createWidget('H')
        self.tab2 = createWidget('H')
        
        # Add tabs
        self.tabs.addTab(self.tab1, "Telescope")
        self.tabs.addTab(self.tab2, "Arrays")
        
        # Telescope tab
        self.col1 = createWidget('F', self.tab1.layout)
        self.col2 = createWidget('F', self.tab1.layout)
        self.col3 = createWidget('F', self.tab1.layout)
        
        # Default
        self.mapListPath = ''
        
        # Col 1
        c1 = self.col1.layout
        self.translateAOR = createButton('Load and translate AOR')
        c1.addRow(self.translateAOR,None)
        self.loadTemplate = createButton('Load template')
        self.exit = createButton('Exit ')
        c1.addRow(self.loadTemplate, self.exit)
       
        self.buildObservation = createButton('Build observation')
        self.buildObservation.clicked.connect(self.buildObs)
        self.writeObservation = createButton('Write observation')
        self.writeObservation.clicked.connect(self.writeObs)
        self.writeObservation.setEnabled(False)
        c1.addRow(self.buildObservation, self.writeObservation)

        self.observationID = createEditableBox("None", 40, "Observation ID: ", c1)
        self.observationType = addComboBox('Observation type: ', self.obstypes, c1)
       
        self.filegpIDred = createEditableBox('None', 40, 'File Group ID Red: ', c1)
        self.filegpIDblue = createEditableBox('None', 40, 'File Group ID Blue: ', c1)        
        self.sourceType = addComboBox('Source type: ', self.sourcetypes, c1 )
        self.aorID = createEditableBox('None', 40, 'AOR ID: ', c1)
        self.targetName = createEditableBox('None', 40, 'Target name: ', c1)
        self.targetRA = createEditableBox('00 00 00.0', 40, 'Target RA: ', c1)
        self.targetDec = createEditableBox('+00 00 00.0', 40, 'Target Dec: ', c1)
        self.redshift = createEditableBox('0', 40, 'Redshift [z]: ', c1, 'double')
        self.detectorAngle = createEditableBox('0', 40, 'Detector angle (E of N): ', c1, 'double')
        self.observingmodes = ["Symmetric", "Asymmetric"]
        #observingmodes = ["Beam switching", "Unmatched nodding"]
        self.observingMode = addComboBox('Observing mode: ', self.observingmodes, c1)
        self.observingMode.currentIndexChanged.connect(self.obsModeChange)
        self.instrumentalMode = addComboBox('Instrumental mode: ', self.instmodes, c1)
        self.primaryArrays = ["RED", "BLUE", "cmd"]
        self.primaryArray = addComboBox('Primary array: ', self.primaryArrays, c1)
        self.primaryArray.currentIndexChanged.connect(self.primaryArrayChange)
        self.setpoint = createEditableBox('', 40, 'Set setpoint: ', c1)
        self.col1.layout.addRow(QLabel('Observing stats'),None)
        self.rawIntTime = createEditableBox('', 40, 'Raw integration time (s): ', c1, 'double')
        self.onsourceIntTime = createEditableBox('', 40, 'On source integration time (s): ', c1)
        self.estObsTime = createEditableBox('', 40, 'Estimated observation time (s): ', c1)
        # Col 2
        c2 = self.col2.layout
        c2.addRow(QLabel('Nod Pattern'),None)
        self.nodpatterns = ['ABBA','AB','A','ABA','AABAA']
        self.nodPattern = addComboBox('Nod pattern: ', self.nodpatterns, c2)
        self.nodPattern.currentIndexChanged.connect(self.nodPatternChange)
        self.nodcyclesPerMapPosition = createEditableBox('1', 40, 'Nod cycles per map position: ', c2, 'int')
        self.gratingDirections = ['Up','Down','None','Split']
        self.gratingDirection = addComboBox('Grating direction: ', self.gratingDirections, c2)
        self.gratingDirection.currentIndexChanged.connect(self.gratingDirectionChange)
        self.scanFilesPerSplit = createEditableBox('n/a', 40, 'Scan files per split: ', c2)
        self.rewindMode = addComboBox('LOS rewind mode: ', ['Auto', 'Manual'], c2)

        c2.addRow(QLabel('Off position'),None)
        self.offpositions = ['Matched', 'Absolute', 'Relative to target', 'Relative to active map pos']
        self.offPosition = addComboBox('Off position: ', self.offpositions, c2)
        self.offPosition.currentIndexChanged.connect(self.offPosChange)
        self.lambdaOffPos = createEditableBox('', 40, 'Lambda [arcsec]:', c2, 'double')
        self.betaOffPos = createEditableBox('', 40, 'Beta [arcsec]:', c2, 'double')
        self.mapOffPos = createEditableBox('', 40, 'Offpos map reduction: ', c2)
        c2.addRow(QLabel('Mapping pattern'),None)
        c2.addRow(QLabel('Map center offset from target'),None)
        self.coordSysMap = addComboBox('Coordinate system: ', self.mapcoordsys, c2)        
        self.lambdaMapCenter = createEditableBox('0', 40, 'Lambda [arcsec]: ', c2, 'double')
        self.betaMapCenter = createEditableBox('0', 40, 'Beta [arcsec]: ', c2, 'double')
        self.mapPattern = addComboBox('Mapping pattern: ', self.refpatterns, c2)
        self.mapPattern.currentIndexChanged.connect(self.mapPatternChange)
        self.noMapPoints = createEditableBox('1', 40,'No of map points: ',c2, 'int')
        self.mapStepSize = createEditableBox('n/a', 40, 'Step size [arcsec]: ', c2)
        self.loadMapPatternFile = createButton('Load file')
        c2.addRow(QLabel('Mapping pattern: '), self.loadMapPatternFile)
        
        # Col 3
        c3 = self.col3.layout
        c3.addRow(QLabel('Chopper setup'),None)
        self.chopScheme = addComboBox('Chop scheme: ', self.chopschemes, c3)
        self.coordSysChop = addComboBox('Coordinate system: ', self.chopcoordsys, c3)        
        self.chopAmp = createEditableBox('', 40,'Chop amplitude (1/2 throw): ', c3, 'double')
        self.chopPosAngle = createEditableBox('', 40,'Chop pos angle (S of E): ', c3, 'double')
        self.chopPhase = createEditableBox(str(self.chop_phase_default), 40)
        self.chopPhaseMode = QComboBox()
        self.chopPhaseMode.addItems(["Default", "Manual"])
        self.chopPhaseMode.currentIndexChanged.connect(self.chopPhaseChange)
        add2widgets('Chopper Phase: ', self.chopPhaseMode, self.chopPhase, c3)
        self.chopLengthFrequency = createEditableBox('', 40, 'Chop frequency [Hz] ', c3, 'double')
        self.chopLengthSamples = createEditableBox('64', 40, 'Chop samples per position ', c3, 'double')
        self.trackingInB = addComboBox('Tracking in pos B: ', ['On', 'Off'], c3) 
        c3.addRow(QLabel('Input params per mapping position'),None)
        self.onSourceTimeChop = createEditableBox('', 40, 'On-source time: ', c3, 'double')
        self.noGratPosChop = createEditableBox('', 40, 'No of grating positions:  ', c3, 'int')
        self.totMapPositions = createEditableBox('1', 40, 'Total no of mapping positions: ', c3, 'int')
        self.chopCompute = createButton('Compute')
        self.chopCompute.setEnabled(False)
        self.chopCompute.clicked.connect(self.grating_xls)
        c3.addRow(self.chopCompute, None)
        self.nodCycles = createEditableBox('', 40, 'No of nod cycles: ', c3)
        self.ccPerGratPos = createEditableBox('', 40, 'No of CC per grating pos: ', c3)
        self.loadScanDescriptionFile= createButton('Load file')
        self.noGratPos4Nod = createEditableBox('', 40, 'No of grating pos per nod: ', c3)
        self.gratCycle4Nod = createEditableBox('', 40, 'Grating cycle per nod (30.0): ', c3)
        self.timeCompleteMap = createEditableBox('', 40, 'Time to complete map [min]: ', c3)
        #c3.addRow(QLabel('Scan description file: '), self.loadScanDescriptionFile)
        
        # Arrays tab
        self.col4 = createWidget('F', self.tab2.layout)
        self.col5 = createWidget('F', self.tab2.layout)
        
        # Column 4 (Red array)
        c4 = self.col4.layout
        self.gratpatterns = ['Centre', 'Dither', 'Inward dither', 'Start']
        c4.addRow(QLabel('Red Array.  [100-210 um]'),None)
        self.setDichroic = addComboBox('Dichroic: ', ['105', '130'], c4)
        c4.addRow(QLabel(''),None)
        self.redLine = addComboBox('Line: ', self.redlines, c4)
        self.redWave = createEditableBox('', 50, 'Wavelength [um]', c4, 'double')
        self.redLine.currentIndexChanged.connect(self.redLineChange)
        self.redOffsetUnits = QComboBox()
        self.redOffsetUnits.addItems(["kms", "um", "units"])
        self.redOffset = QLineEdit('0')
        add2widgets('Line offset: ', self.redOffset, self.redOffsetUnits, c4)
        self.redGratPosMicron = createEditableBox('', 50, 'Grating position [um]: ', c4)
        self.redGratPosUnits = createEditableBox('', 50, 'Grating position [unit]: ', c4)
        c4.addRow(QLabel('Spectral mode'),None)
        self.redGratPattern = addComboBox('Grating movement pattern: ', self.gratpatterns, c4)
        self.redStepSizeUp = createEditableBox('0', 40, 'Step size up [pixels]: ', c4, 'double')
        self.redGratPosUp = createEditableBox('1', 40, 'Grating position up: ', c4, 'int')
        self.redStepSizeDown = createEditableBox('0', 40, 'Step size down [pixels]: ', c4, 'double')
        self.redGratPosDown = createEditableBox('0', 40, 'Grating position down: ', c4, 'int')
        c4.addRow(QLabel('Timing and sensitivity'),None)
        self.redRampLengthSamples = createEditableBox('32', 40, 'Ramp length [samples]: ', c4)
        self.redRampLengthMs = createEditableBox('32', 40, 'Ramp length [ms]: ', c4)
        self.redRamp4ChopPos = createEditableBox('', 40, 'Ramps per chop pos: ', c4)
        self.redCC4ChopPos = createEditableBox('1', 40, 'CC per chop pos: ', c4)
        self.redGratCycles = createEditableBox('1', 40, 'Number of grating cycles: ', c4)
        self.redZeroBias = createEditableBox('60', 40, 'Zero bias [mV]: ', c4)
        self.redBiasR = createEditableBox('0', 40, 'BiasR [mV]: ', c4)
        self.redCapacitor = addComboBox('Capacitor [uF]: ', self.capacitors, c4)
        self.redScanFileLength = createEditableBox('', 40, 'Scan file length [s]: ', c4)
        
        # Column 5 (Blue array)
        c5 = self.col5.layout
        c5.addRow(QLabel('Blue Array.  Order 2: [48-72um]   Order 1:  [70-130 um]'),None)
        items = ['1', '2']
        self.setOrder = addComboBox('Order: ', items, c5)
        self.setFilter = addComboBox('Filter: ', ['1', '2'], c5)
        self.blueLine = addComboBox('Line: ', self.bluelines, c5) 
        self.blueLine.currentIndexChanged.connect(self.blueLineChange)
        self.blueWave = createEditableBox('', 50, 'Wavelength [um]', c5)
        self.blueOffsetUnits = QComboBox()
        self.blueOffsetUnits.addItems(["kms", "um", "units"])
        self.blueOffset = QLineEdit('0')
        add2widgets('Line offset: ', self.blueOffset, self.blueOffsetUnits, c5)
        self.blueGratPosMicron = createEditableBox('', 50, 'Grating position [um]: ', c5)
        self.blueGratPosUnits = createEditableBox('', 50, 'Grating position [unit]: ', c5)
        c5.addRow(QLabel('Spectral mode'),None)
        self.blueGratPattern = addComboBox('Grating movement pattern: ', self.gratpatterns, c5)
        self.blueStepSizeUp = createEditableBox('0', 40, 'Step size up [pixels]: ', c5)
        self.blueGratPosUp = createEditableBox('1', 40, 'Grating position up: ', c5)
        self.blueStepSizeDown = createEditableBox('0', 40, 'Step size down [pixels]: ', c5)
        self.blueGratPosDown = createEditableBox('0', 40, 'Grating position down: ', c5)
        c5.addRow(QLabel('Timing and sensitivity'),None)
        self.blueRampLengthSamples = createEditableBox('32', 40, 'Ramp length [samples]: ', c5)
        self.blueRampLengthMs = createEditableBox('32', 40, 'Ramp length [ms]: ', c5)
        self.blueRamp4ChopPos = createEditableBox('', 40, 'Ramps per chop pos: ', c5)
        self.blueCC4ChopPos = createEditableBox('1', 40, 'CC per chop pos: ', c5)
        self.blueGratCycles = createEditableBox('1', 40, 'Number of grating cycles: ', c5)
        self.blueZeroBias = createEditableBox('60', 40, 'Zero bias [mV]: ', c5)
        self.blueBiasR = createEditableBox('0', 40, 'BiasR [mV]: ', c5)
        self.blueCapacitor = addComboBox('Capacitor [uF]: ', self.capacitors, c5)
        self.blueScanFileLength = createEditableBox('', 40, 'Scan file length [s]: ', c5)
        
        # Define conversion
        self.defineConversion()
        
        # First conversion
        self.gui2vars()
        
        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        
        # Defaults
        self.setDefaults()
        
    def setDefaults(self):
        self.chopPhaseChange(0)
        self.obsModeChange(0)
        self.primaryArrayChange(0)
        self.nodPatternChange(0)
        self.gratingDirectionChange(0)
        self.offPosChange(0)
        self.mapPatternChange(0, readFile=False)
        
    def blueLineChange(self, index):
        """If new line selected, populate the wavelength."""
        if self.blueLine.currentText()  == 'Custom':
            return
        self.blueWave.setText(str(self.bluewaves[index]))
        # Select best order
        print('current order ',self.setOrder.currentText())
        wave = float(self.blueWave.text())
        print('wave is ', wave)
        if wave < 71.:
            order = '2'
            bfilter = '2'
        else:
            order = '1'
            bfilter = '1'
        print('order ', order)
        index = self.setOrder.findText(order, Qt.MatchFixedString)
        self.setOrder.setCurrentIndex(index)
        index = self.setFilter.findText(bfilter, Qt.MatchFixedString)
        self.setFilter.setCurrentIndex(index)
        print('updated order ',self.setOrder.currentText())
        
    def redLineChange(self, index):
        """If new line selected, populate the wavelength."""
        self.redWave.setText(str(self.redwaves[index]))

    def chopPhaseChange(self, index):
        """Put default phase value is default is selected."""
        if index == 0:
            self.chopPhase.setText(str(self.chop_phase_default))
            
    def obsModeChange(self, index):
        """Reaction to change of obsMode."""
        obsmode = self.observingmodes[index]
        if obsmode == 'Symmetric':
            self.var['offpos'] = 'Matched'
            self.var['symmetry'] = 'Symmetric'
            index = self.instrumentalMode.findText('SYMMETRIC_CHOP', Qt.MatchFixedString)
            self.instrumentalMode.setCurrentIndex(index)
            index = self.offPosition.findText('Matched', Qt.MatchFixedString)
            self.offPosition.setCurrentIndex(index)
            # disable labels and entryboxes beneath
            self.lambdaOffPos.setReadOnly(True)
            self.betaOffPos.setReadOnly(True)
            self.mapOffPos.setReadOnly(True)
            self.lambdaOffPos.setEnabled(False)
            self.betaOffPos.setEnabled(False)
            self.mapOffPos.setEnabled(False)
            # disable Tracking in B buttons
            index = self.trackingInB.findText('On', Qt.MatchFixedString)
            self.trackingInB.setCurrentIndex(index)
            self.trackingInB.hide()
            self.trackingInB.label.hide()
            #self.trackingInB.setEnabled(False)
        else:
            self.var['offpos'] = 'Relative to target'
            self.var['symmetry'] = 'Asymmetric'
            index = self.instrumentalMode.findText('ASYMMETRIC_CHOP', Qt.MatchFixedString)
            self.instrumentalMode.setCurrentIndex(index)
            index = self.offPosition.findText('Relative to target', Qt.MatchFixedString)
            self.offPosition.setCurrentIndex(index)
            # enable labels and entryboxes beneath
            self.lambdaOffPos.setReadOnly(False)
            self.betaOffPos.setReadOnly(False)
            self.mapOffPos.setReadOnly(False)
            self.lambdaOffPos.setEnabled(True)
            self.betaOffPos.setEnabled(True)
            self.mapOffPos.setEnabled(True)
            # enable Tracking in B buttons
            index = self.trackingInB.findText('Off', Qt.MatchFixedString)
            self.trackingInB.setCurrentIndex(index)
            self.trackingInB.show()
            self.trackingInB.label.show()
            #self.trackingInB.setEnabled(True)
            
    def primaryArrayChange(self, index):
        """Changes with switch of primary array."""
        self.var['primaryarray'] =  self.primaryArrays[index]
        print('new array is ', self.var['primaryarray'])
        if self.var['primaryarray'] == 'RED':
            self.var['commandline_option'] = '0'
            self.setpoint.setText('n/a')
            #self.setpoint.setReadOnly(True)
            #self.setpoint.setEnabled(False)
            self.setpoint.hide()
            self.setpoint.label.hide()
        elif self.var['primaryarray'] == 'BLUE':
            self.var['commandline_option'] = '0'
            self.setpoint.setText('n/a')
            #self.setpoint.setReadOnly(True)
            #self.setpoint.setEnabled(False)
            self.setpoint.hide()
            self.setpoint.label.hide()
        elif self.var['primaryarray'] == 'cmd':
            self.var['commandline_option'] = '1'
            #self.setpoint.setReadOnly(False)
            self.setpoint.setText('')
            #self.setpoint.setEnabled(False)
            self.setpoint.show()
            self.setpoint.label.show()

        
    def nodPatternChange(self, index):
        """When changing nod pattern."""    
        self.var['nodpattern'] = self.nodpatterns[index]
        if self.var['nodpattern'] in ['AB', 'ABBA', 'A']:
            self.nodcyclesPerMapPosition.label.setText('Nod cycles per map position (n): ')
            self.nodcyclesPerMapPosition.setReadOnly(False)
        elif self.var['nodpattern'] in ['ABA', 'AABAA']:
            self.nodcyclesPerMapPosition.label.setText('Number of A positions per B (n): ')
            if self.var['nodpattern'] == 'ABA':
                self.nodcyclesPerMapPosition.setText('2')
            else:
                self.nodcyclesPerMapPosition.setText('4')
                self.nodcyclesPerMapPosition.setReadOnly(False)
        if self.var['nodpattern'] == 'A':
            self.chopAmp.setText('0')
            obstype = 'SKY'
        else:
            self.chopAmp.setText('60')
            obstype = 'OBJECT'
        index = self.setOrder.findText(obstype, Qt.MatchFixedString)
        self.observationType.setCurrentIndex(index)
    
    def gratingDirectionChange(self, index):
        """When changing grating scan direction."""
        self.var['scandist'] = self.gratingDirections[index]
        if self.var['scandist'] in ['Up', 'Down']:
            self.scanFilesPerSplit.setText('')
            self.scanFilesPerSplit.setReadOnly(True)
            index = self.redGratPattern.findText('Inward dither', Qt.MatchFixedString)
            self.redGratPattern.setCurrentIndex(index)
            self.blueGratPattern.setCurrentIndex(index)
            if self.var['scandist'] == 'Up':
                self.redStepSizeUp.setText('0')
                self.redGratPosUp.setText('1')
                self.redStepSizeDown.setText('0')
                self.redGratPosDown.setText('0')
                self.blueStepSizeUp.setText('0')
                self.blueGratPosUp.setText('1')
                self.blueStepSizeDown.setText('0')
                self.blueGratPosDown.setText('0')
                self.redStepSizeUp.setReadOnly(False)            
                self.redGratPosUp.setReadOnly(False)    
                self.redStepSizeDown.setReadOnly(True)
                self.redGratPosDown.setReadOnly(True)
                self.blueStepSizeUp.setReadOnly(False)                   
                self.blueGratPosUp.setReadOnly(False)
                self.blueStepSizeDown.setReadOnly(True)
                self.blueGratPosDown.setReadOnly(True)
            elif self.var['scandist'] == 'Down':
                self.redStepSizeUp.setText('0')
                self.redGratPosUp.setText('0')
                self.redStepSizeDown.setText('0')
                self.redGratPosDown.setText('1')
                self.blueStepSizeUp.setText('0')
                self.blueGratPosUp.setText('0')
                self.blueStepSizeDown.setText('0')
                self.blueGratPosDown.setText('1')
                self.redStepSizeUp.setReadOnly(True)               
                self.redGratPosUp.setReadOnly(True)
                self.redStepSizeDown.setReadOnly(False)
                self.redGratPosDown.setReadOnly(False) 
                self.blueStepSizeUp.setReadOnly(True)           
                self.blueGratPosUp.setReadOnly(True)
                self.blueStepSizeDown.setReadOnly(False)
                self.blueGratPosDown.setReadOnly(False)
        elif self.var['scandist'] in ['None', 'Split']:
            if self.var['scandist'] == 'None':
                self.scanFilesPerSplit.setText('')
                self.scanFilesPerSplit.setReadOnly(True)       
            else:
                self.scanFilesPerSplit.setReadOnly(False)
            # if grating movement pattern is not Centre or Start, set it to Centre
            if self.redGratPattern.currentText() not in ['Centre', 'Start']:
                index = self.redGratPattern.findText('Centre', Qt.MatchFixedString)
                self.redGratPattern.setCurrentIndex(index)
            if self.blueGratPattern.currentText() not in ['Centre', 'Start']:
                index = self.blueGratPattern.findText('Centre', Qt.MatchFixedString)
                self.blueGratPattern.setCurrentIndex(index)
            self.redStepSizeUp.setText('0')
            self.redGratPosUp.setText('1')
            self.redStepSizeDown.setText('0')
            self.redGratPosDown.setText('0')
            self.blueStepSizeUp.setText('0')
            self.blueGratPosUp.setText('1')
            self.blueStepSizeDown.setText('0')
            self.blueGratPosDown.setText('0')
            self.redStepSizeUp.setReadOnly(False)             
            self.redGratPosUp.setReadOnly(False)
            self.redStepSizeDown.setReadOnly(False)
            self.redGratPosDown.setReadOnly(False)
            self.blueStepSizeUp.setReadOnly(False)             
            self.blueGratPosUp.setReadOnly(False)
            self.blueStepSizeDown.setReadOnly(False)
            self.blueGratPosDown.setReadOnly(False)
        
    def offPosChange(self, index):
        """Offset position changed."""
        self.var['offpos'] = self.offpositions[index]
        if self.var['offpos'] == 'Matched':
            self.lambdaOffPos.label.setText('Lambda [arcsec]: ')
            self.betaOffPos.label.setText('Beta [arcsec]: ')
            self.mapOffPos.setText('1')
            self.mapOffPos.setReadOnly(True)
        elif self.var['offpos'] == 'Absolute':
            print('label text is ', self.lambdaOffPos.label.text())
            self.lambdaOffPos.label.setText('Lambda [RA decimal degs]:')
            self.betaOffPos.label.setText('Beta [Dec decimal degs]:')
            self.mapOffPos.setReadOnly(True)
        elif self.var['offpos'] == 'Relative to target':
            self.lambdaOffPos.label.setText('Lambda [arcsec]: ')
            self.betaOffPos.label.setText('Beta [arcsec]: ')
            self.mapOffPos.setReadOnly(True)
        elif self.var['offpos'] == 'Relative to active map pos':
            self.lambdaOffPos.label.setText('Lambda [arcsec]: ')
            self.betaOffPos.label.setText('Beta [arcsec]: ')
            self.mapOffPos.setText('1')
            self.mapOffPos.setReadOnly(False)

    def loadMapFile(self):
        """Load a map file."""
        try:
            noMapPoints, mapListPath = readMap()
            self.mapListPath = mapListPath
            self.noMapPoints.setText(str(noMapPoints))
        except:
            print('Invalid map file.')  

    def mapPatternChange(self, index, readFile=True):
        """Mapping pattern changed."""
        self.var['pattern'] = self.refpatterns[index]
        if self.var['pattern'] == 'File':
            self.noMapPoints.setText('1')
            self.mapStepSize.setText('n/a')
            self.noMapPoints.setEnabled(False)
            self.mapStepSize.setEnabled(False)
            self.loadMapPatternFile.setEnabled(True)
            # Lunch load button
            if readFile:
                self.loadMapFile()
        elif self.var['pattern'] == 'Stare':
            self.loadMapPatternFile.setEnabled(False)
            self.noMapPoints.setEnabled(True)
            self.mapStepSize.setEnabled(True)
            self.noMapPoints.setText('1')
            self.mapStepSize.setText('n/a')
        elif self.var['pattern'] == 'N-point cross':
            self.loadMapPatternFile.setEnabled(False)
            self.noMapPoints.setEnabled(True)
            self.mapStepSize.setEnabled(True)
            self.noMapPoints.setText('multiple of 4 + 1')
            self.mapStepSize.setText('n/a')
        elif self.var['pattern'] in ['Spiral', 'Inward spiral']:
            self.loadMapPatternFile.setEnabled(False)
            self.noMapPoints.setEnabled(True)
            self.mapStepSize.setEnabled(True)
            self.noMapPoints.setText('Odd square number')
            self.mapStepSize.setText('1')
        else:
            print(self.var['pattern'], ' is not yet supported.')

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
        self.obs_eff = config["obs_eff"]
        self.t_ta_move = config["t_ta_move"]
        self.t_grating_move = config["t_grating_move"]
        self.f_chop = config["f_chop"]
        self.chop_phase_default = config["chop_phase_default"]
        self.obs_con_samplesize = config["obs_con_samplesize"]
            
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
        
    def update(self, aorPars):
        """Update with values from *.sct file."""
        
        for key in aorPars.keys():
            label = self.k2tw[key]
            if isinstance(label, QLineEdit):
                try:
                    if key == 'REDSHIFT':
                        label.setText("{0:.10f}".format(float(aorPars[key])))
                    else:
                        label.setText(aorPars[key])
                except:
                    print(key + 'is unkown.')
            elif isinstance(label, QComboBox):
                try:
                    index = label.findText(aorPars[key], Qt.MatchFixedString)
                    label.setCurrentIndex(index)
                    if key == 'ORDER':
                        print('Order ', aorPars[key], index, label.currentText())
                except:
                    print(key + 'is unkown.')
            else:  # No widget, just variable
                if key == 'MAPLISTPATH':
                    # self.k2tw[key] = maplistpath # does not work ...
                    self.mapListPath = aorPars[key]
                    #print('Map file is in: ', maplistpath)
                else:
                    print('Unknown key ',key)

        # Check if chopper phase mode is default and put default value
        if aorPars['CHOPPHASE'] == 'Default' :
            self.chopPhase.setText(str(self.chop_phase_default))            
        # Update number of points in map
        self.totMapPositions.setText(aorPars['DITHMAP_NUMPOINTS'])
        self.totMapPositions.setEnabled(False)

    def buildObs(self):
        """
        Save GUI parameters and calculate observation.
        """
        try:
            if self.pathFile == '':
                message = 'Upload a template before building the observation.'
                QMessageBox.about(self, "Build", message)
                return                
            self.writeObservation.setEnabled(False)
            self.gui2vars()
            self.calculate()
            self.var['ind_scanindex'] = 0
            self.var['commandline_option'] = '0' # No command line option for the moment
            print('Observation built')
            self.writeObservation.setEnabled(True) 
            self.chopCompute.setEnabled(True)
        except:
            message = 'Upload a template before building the observation.'
            QMessageBox.about(self, "Build", message)
            print(message)
            
    def gui2vars(self):
        """
        Save selected GUI variables to local variables.
        """        
        self.var = {}
        for key in self.k2tw:
            label = self.k2tw[key]
            if isinstance(label, QLineEdit):
                self.var[key.lower()] = label.text()
            elif isinstance(label, QComboBox):
                self.var[key.lower()] = label.currentText()
            else:
                if key.lower() == 'maplistpath':
                    self.var[key.lower()] = self.mapListPath
        
        # convert values that need to be int and float for calculations
        ints = [
            'nodcycles',
            'splits',
            'dithmap_numpoints',
            'chop_length',
            'dichroic',
            'order',
            'blue_filter',
            'red_posup',
            'red_posdown',
            'red_ramplen',
            'red_chopcyc',
            'red_grtcyc',
            'red_capacitor',
            'red_zbias',
            'red_biasr',
            'blue_posup',
            'blue_posdown',
            'blue_ramplen',
            'blue_chopcyc',
            'blue_grtcyc',
            'blue_capacitor',
            'blue_zbias',
            'blue_biasr']
        flts = [
            'detangle',
            'chop_amp',
            'offpos_lambda',
            'offpos_beta',
            'offpos_reduc',
            'dithmap_lambda',
            'dithmap_beta',
            'red_micron',
            'redshift',
            'red_offset',
            'red_sizeup',
            'red_sizedown',
            'blue_micron',
            'blue_offset',
            'blue_sizeup',
            'blue_sizedown'
            ]
        
        for item in ints:
            # in case any are float, convert str -> float -> int
            try:
                self.var[item] = int(float(self.var[item]))
            except:
                self.var[item] = 0
        for item in flts:
            try:
                self.var[item] = float(self.var[item])
            except:
                self.var[item] = 0.0
            
        # get any other values from the GUI
        self.var['ch_scheme'] = self.chopScheme.currentText()
        self.var['symmetry'] = self.observingMode.currentText()
        self.var['scandesdir'] = self.pathFile  # Same directory where the AOR files are read
        
        # calculate any "support" variables needed
        self.var['target_lambda_hms'] = self.var['target_lambda']
        # target RA in decimal Hours
        rah, ram, ras = self.var['target_lambda'].split()
        target_ra_decim = float(rah) + float(ram) / 60.0 + float(ras)/ 3600.
        # target RA in decimal degrees
        self.var['target_lambda_deg'] = (target_ra_decim / 24.0) * 360.
        # target Beta
        self.var['target_beta_dms'] = self.var['target_beta']
        dd, dm, ds = self.var['target_beta'].split()
        target_dec_decim = np.abs(float(dd)) + float(dm) / 60. + float(ds) / 3600.
        sign = np.sign(float(dd))
        # target DEC in decimal degrees
        self.var['target_beta_deg'] = sign * target_dec_decim
        # calculate grating step sizes in inductosyn units (isu)
        redPixelsize = 730.0
        bluePixelsize = 800.0
        self.var['red_sizeup_isu'] = int(float(self.var['red_sizeup']) * redPixelsize)
        self.var['red_sizedown_isu'] = int(float(self.var['red_sizedown']) * redPixelsize)
        self.var['blue_sizeup_isu'] = int(float(self.var['blue_sizeup']) * bluePixelsize)
        self.var['blue_sizedown_isu'] = int(float(self.var['blue_sizedown']) * bluePixelsize)
        self.var['target_coordsys'] = 'J2000'
        self.var['map_centlambda'] = float(self.lambdaMapCenter.text())
        self.var['map_centbeta'] = float(self.betaMapCenter.text())
        # TOTAL_POWER mode if chop throw is 0
        if self.var['chop_amp'] == 0.0:
            self.var['instmode'] = 'TOTAL_POWER'
        # SKY mode if instmode is A
        if self.var['nodpattern'] == 'A':
            self.var['instmode'] = 'SKY'
            
    def calculate(self):
        """
        Make calculations and update GUI.
        """
        result = self.calcTiming()  # calculate timing, update GUI
        if result == False:
            print("ERROR in calc_timing")
            return
        result = self.calcInductosynPos()  # calculate inductosyn position, update GUI
        if result == False:
            print('ERROR in calc_lookup')
            return
        result = self.calcGrtpos()  # calculate grating positions and movements
        if result == False:
            print('ERROR in calc_grtpos')
            return

    def calcTiming(self):        
        """
        Calculate time estimates, set chopper values.
        """
        #obs_con_samplesize = 250.0  #250.0 SOFIA clock, 256.0 lab clock
        obs_con_samplesize = self.obs_con_samplesize
        if self.var['chop_amp'] == 0.0:
            obs_con_chopeff = 1.0
        else:
            obs_con_chopeff = 0.5

        # ramp length in ms, red and blue
        red_ramplen_ms = (1000.0 / obs_con_samplesize) * self.var['red_ramplen']
        blue_ramplen_ms = (1000.0 / obs_con_samplesize) * self.var['blue_ramplen']
        # for 2POINT chop scheme - time in samples
        chopcyctime_sam = 2. * self.var['chop_length']
        
        # time per grating position in samples, red and blue_ramplen_ms
        red_grtpostime_sam = self.var['red_chopcyc'] * chopcyctime_sam
        blue_grtpostime_sam = self.var['blue_chopcyc'] * chopcyctime_sam
        print('red chop cycle ',self.var['red_chopcyc'])
        # number of total grating positions = up + down, red and blue
        self.var['red_numgrtpos'] = self.var['red_posup'] + self.var['red_posdown']
        self.var['blue_numgrtpos'] = self.var['blue_posup'] + self.var['blue_posdown']
        # time per grading cycle in samples
        print('red number of grat pos ', self.var['red_numgrtpos'])
        red_grtcyctime_sam = self.var['red_numgrtpos'] * red_grtpostime_sam
        blue_grtcyctime_sam = self.var['blue_numgrtpos'] * blue_grtpostime_sam

        # override timepergrtcyc if distributing steps
        if self.var['nodcycles'] >= 2:
            if self.var['scandist'] == 'Up':
                if self.var['red_posup'] <= 1:
                    red_grtcyctime_sam = self.var['red_numgrtpos'] * red_grtpostime_sam
                else:
                    red_grtcyctime_sam = \
                    (self.var['red_posup'] / self.var['nodcycles']) * red_grtpostime_sam
                if self.var['blue_posup'] <= 1:
                    blue_grtcyctime_sam = self.var['blue_numgrtpos'] * blue_grtpostime_sam
                else:
                    blue_grtcyctime_sam = \
                    (self.var['blue_posup'] / self.var['nodcycles']) * blue_grtpostime_sam                    
            elif self.var['scandist'] == 'Down':
                if self.var['red_posdown'] <= 1:
                    red_grtcyctime_sam = self.var['red_numgrtpos'] * red_grtpostime_sam
                else:
                    red_grtcyctime_sam = \
                    (self.var['red_posdown'] / self.var['nodcycles']) * red_grtpostime_sam
                if self.var['blue_posdown'] <= 1:
                    blue_grtcyctime_sam = self.var['blue_numgrtpos'] * blue_grtpostime_sam
                else:
                    blue_grtcyctime_sam = \
                    (self.var['blue_posdown'] / self.var['nodcycles']) * blue_grtpostime_sam

        # time per scan in ms, red and blue
        print('red_grtcyctime_sam ', red_grtcyctime_sam)
        red_scantime_ms = (1000 / obs_con_samplesize) * self.var['red_grtcyc'] * red_grtcyctime_sam
        blue_scantime_ms = (1000 / obs_con_samplesize) * self.var['blue_grtcyc'] * blue_grtcyctime_sam
        
        # ramps per chop pos
        red_rampsperchoppos = self.var['chop_length'] / self.var['red_ramplen']
        blue_rampsperchoppos = self.var['chop_length'] / self.var['blue_ramplen']

        # On-source chop cycle length in samples, account for chopper eff.
        chopcyctime_src_sam = float(chopcyctime_sam) * obs_con_chopeff
        red_grtpostime_src_sam = chopcyctime_src_sam * self.var['red_chopcyc']
        # time spent by grating settling after a move in samps
        red_grtsettime_sam = (self.var['red_posup'] - 1 + self.var['red_posdown'] - 1) * (0.25 / obs_con_samplesize)
        # actual time per grating cycle on source
        red_grtcyctime_src_sam =  (red_grtpostime_src_sam * self.var['red_numgrtpos']) - red_grtsettime_sam
        red_scantime_src_sam = red_grtcyctime_src_sam * self.var['red_grtcyc']
        blue_grtpostime_src_sam =  chopcyctime_src_sam * self.var['blue_chopcyc']
        # time spent by grating settling after a move in samps
        blue_grtsettime_sam = \
            (self.var['blue_posup'] - 1 + self.var['blue_posdown'] - 1) *  (0.25 / obs_con_samplesize)
        # actual time per grating cycle on source
        blue_grtcyctime_src_sam =  \
            (blue_grtpostime_src_sam * self.var['blue_numgrtpos']) - blue_grtsettime_sam
        blue_scantime_src_sam =  blue_grtcyctime_src_sam * self.var['blue_grtcyc']
        
        # Loops to sort out special cases where we are distributing steps over nod nycles; 
        # also special case where only one channel does this if distributing scans, use the steps per nod cycle
        if self.var['nodcycles'] >= 2:
            obs4sample = 0.25 / obs_con_samplesize
            nodCycles = self.var['nodcycles']
            if self.var['scandist'] == 'Up':
                rUp = self.var['red_posup']
                bUp = self.var['blue_posup']
                if rUp <= 1:
                    red_grtsettime_sam = rUp * obs4sample
                else:
                    red_grtsettime_sam = rUp / nodCycles * obs4sample
                if bUp <= 1:
                    blue_grtsettime_sam = bUp * obs4sample
                else:
                    blue_grtsettime_sam = bUp / nodCycles * obs4sample
                red_grtcyctime_src_sam = red_grtpostime_src_sam *  rUp / nodCycles - red_grtsettime_sam
                red_scantime_src_sam =  red_grtcyctime_src_sam * self.var['red_grtcyc']
                blue_grtcyctime_src_sam = blue_grtpostime_src_sam * bUp / nodCycles -  blue_grtsettime_sam
                blue_scantime_src_sam =  blue_grtcyctime_src_sam * self.var['blue_grtcyc']
            elif self.var['scandist'] == 'Down':
                rDo = self.var['red_posdown']
                bDo = self.var['blue_posdown']
                blue_grtsettime_sam = bDo / nodCycles * obs4sample
                if rDo <= 1:
                    red_grtsettime_sam = rDo * obs4sample
                else:
                    red_grtsettime_sam = rDo / nodCycles * obs4sample
                if bDo <= 1:
                    blue_grtsettime_sam = bDo * obs4sample
                else:
                    blue_grtsettime_sam = bDo / nodCycles * obs4sample
                red_grtcyctime_src_sam = red_grtpostime_src_sam * rDo / nodCycles - red_grtsettime_sam
                red_scantime_src_sam =  red_grtcyctime_src_sam * self.var['red_grtcyc']
                blue_grtcyctime_src_sam = blue_grtpostime_src_sam * bDo / nodCycles -  blue_grtsettime_sam
                blue_scantime_src_sam = blue_grtcyctime_src_sam * self.var['blue_grtcyc']

        #chop_freq = float(1.0 / (self.var['chop_length'] / obs_con_samplesize)) / 2.
        chop_freq = obs_con_samplesize / self.var['chop_length'] * 0.5
        
        # Update GUI
        # Ramp length in ms
        self.redRampLengthMs.setText('{0:.2f}'.format(round(red_ramplen_ms, 2)))
        self.blueRampLengthMs.setText('{0:.2f}'.format(round(blue_ramplen_ms, 2)))
        # Fill Scan file length (s), red and blue
        self.redScanFileLength.setText('{0:.2f}'.format(round(red_scantime_ms / 1000., 2)))
        self.blueScanFileLength.setText('{0:.2f}'.format(round(blue_scantime_ms / 1000., 2)))
        # Fill Ramps per chop pos, red and blue_rampsperchoppos
        self.redRamp4ChopPos.setText(str(red_rampsperchoppos))
        self.blueRamp4ChopPos.setText(str(blue_rampsperchoppos))
        # Chop frequency
        self.chopLengthFrequency.setText(str(chop_freq))
        
        # Compute nod multipliers for integration time calculation
        if self.var['pattern'] == 'File':
            if self.var['maplistpath']:
                result = self.calcFile()
                if result == False:
                    return
            else:
                print('Map file not found')
                return False
        else:
            self.var['numlistpoints'] = self.var['dithmap_numpoints']
            if self.var['pattern'] == 'N-point cross':
                result = self.calcNpoint()
                if result == False:
                    return
            elif self.var['pattern'] in ['Spiral', 'Inward spiral']:
                result = self.calcSpiral()
                if result == False:
                    return
            elif self.var['pattern'] == 'Stare':
                result = self.calcStare()
                if result == False:
                    return
                
        print('num list points is: ', self.var['numlistpoints'])

        if self.var['nodpattern'] in ['ABA','AABAA']:
            nodmultiplier = math.ceil(self.var['numlistpoints'] / self.var['nodcycles'])
        elif self.var['nodpattern'] == 'A':
            nodmultiplier = self.var['nodcycles']
        else:  # 'AB' and 'ABBA'
            nodmultiplier = 2 * self.var['nodcycles']
        if int(self.var['nodcycles']) == 0:
            nodmultiplier = 1

        # Determine C_TIP based on Chopper Symmetry
        if self.var['symmetry'] == 'Symmetric':
            self.var['chop_tip'] = 0.0
        else:
            self.var['chop_tip'] = 1.0

        # Compute raw integration time - use the longest scan time between both channels
        if red_scantime_ms >= blue_scantime_ms:
            scantime_ms = red_scantime_ms
        else:
            scantime_ms = blue_scantime_ms
        print('scantime in ms: ', scantime_ms)
        npts = self.var['numlistpoints'] 
        if self.var['nodpattern'] in ['ABA', 'AABAA']:
            rawtime_ms = (npts +  nodmultiplier) * scantime_ms
        else:  # 'AB', 'ABBA', and 'A'
            rawtime_ms = npts * scantime_ms * nodmultiplier
        rawtime_sec = rawtime_ms / 1000.
        # update GUI
        print('numlistpts ', npts, ' nodmult ', nodmultiplier)
        print('integration time ', rawtime_sec)
        self.rawIntTime.setText(str("%.1f" % rawtime_sec))

        # Compute on source integration time
        if self.var['nodpattern'] in ['ABA','AABAA']:
            sourcetime_sam = self.var['numlistpoints'] * red_scantime_src_sam
        else:
            if self.var['symmetry'] == 'Symmetric':
                symfactor = 1.
            else:
                symfactor = 2.
            sourcetime_sam = npts * nodmultiplier / symfactor * red_scantime_src_sam
        sourcetime_sec = float(sourcetime_sam / obs_con_samplesize)
        print('time on source [s]: ', sourcetime_sec)
        self.onsourceIntTime.setText(str("%.1f" % sourcetime_sec))

        # Compute observation time including overheads
        if self.var['nodpattern'] == 'A':
            nodcycmovetime_sec = 0.
            nodcycmovetime_total_sec = 0.
            obstime_sec = rawtime_sec + nodcycmovetime_total_sec
        elif self.var['nodpattern'] == 'AB':
            nodcycmovetime_sec = 10.0 * 2.0 * self.var['nodcycles']
            nodcycmovetime_total_sec = nodcycmovetime_sec * self.var['numlistpoints']
            obstime_sec = rawtime_sec + nodcycmovetime_total_sec
        elif self.var['nodpattern'] == 'ABBA':
            nodcycmovetime_sec = 10.0 * self.var['nodcycles']
            nodcycmovetime_total_sec = nodcycmovetime_sec * self.var['numlistpoints']
            obstime_sec = rawtime_sec + nodcycmovetime_total_sec
        elif self.var['nodpattern'] in ['ABA', 'AABAA']:
            nodcycmovetime_sec = 10. * (self.var['nodcycles'] + 1)
            nodcycscantime_sec = nodcycmovetime_sec + \
                (red_scantime_ms / 1000. * (self.var['nodcycles'] + 1))
            nodcycmovetime_total_sec = nodcycmovetime_sec *   \
                (math.ceil(self.var['numlistpoints'] / self.var['nodcycles']))
            nodcycscantime_total_sec = nodcycscantime_sec *  \
                (math.ceil(self.var['numlistpoints'] / self.var['nodcycles']))
            obstime_sec = nodcycscantime_total_sec
        self.estObsTime.setText(str("%.1f" % obstime_sec))
        
    def calcFile(self):
        """
        Read mapping file.
        """
        print('reading map file ...')
        try:
            print('File is ', self.mapListPath)  
            print('Variable ', self.var['maplistpath'])
            with open(self.var['maplistpath']) as file:
                map_lambda, map_beta = [], []
                nod_lambda, nod_beta = [], []
                map_centre_lambda, map_centre_beta = [], []
                map_offset_lambda, map_offset_beta = [], []
                for cnt, line in enumerate(file):
                    line = line.rstrip('\n')
                    print(line)
                    if cnt == 0:
                        rah, ram, ras, decd, decm, decs = line.split() 
                        map_ra = ' '.join((rah, ram, ras))
                        map_dec = ' '.join((decd, decm, decs))
                        if (self.var['target_lambda_hms'] != map_ra) or \
                            (self.var['target_beta_dms'] != map_dec):
                                print('Widget and map file coordinates do not match')
                                return False
                    else:
                        # read the mapping points
                        l, b = line.split()
                        map_lambda.append(float(l))
                        map_beta.append(float(b))
                        nod_lambda.append(float(l))
                        nod_beta.append(float(b))
                        map_centre_lambda.append(float(self.var['map_centlambda']))
                        map_centre_beta.append(float(self.var['map_centbeta']))
                        map_offset_lambda.append(float(self.var['offpos_lambda']))
                        map_offset_beta.append(float(self.var['offpos_beta']))
            map_lambda = np.array(map_lambda)
            map_beta = np.array(map_beta)
            nod_lambda = np.array(nod_lambda)
            nod_beta = np.array(nod_beta)
            map_centre_lambda = np.array(map_centre_lambda)
            map_centre_beta = np.array(map_centre_beta)
            map_offset_lambda = np.array(map_offset_lambda)
            map_offset_beta = np.array(map_offset_beta)
            map_lambda += map_centre_lambda
            map_beta += map_centre_beta
            nod_lambda = map_lambda / self.var['offpos_reduc'] + map_offset_lambda
            nod_beta = map_beta / self.var['offpos_reduc'] + map_offset_beta
            self.var['map_lambda'] = map_lambda
            self.var['map_beta'] = map_beta
            self.var['nod_lambda'] = nod_lambda
            self.var['nod_beta'] = nod_beta
            self.var['numlistpoints'] = cnt
        except:
            print('Problems to read map file ..')
            return False                                        

    def calcNpoint(self):
        self.var['map_lambda'] = [ None ] * self.var['numlistpoints']
        self.var['map_beta'] = [ None ] * self.var['numlistpoints']
        self.var['nod_lambda'] = [ None ] * self.var['numlistpoints']
        self.var['nod_beta'] = [ None ] * self.var['numlistpoints']

        self.var['map_lambda'][0] = self.var['map_centlambda']
        self.var['map_beta'][0] = self.var['map_centbeta']
        self.var['nod_lambda'][0] = self.var['map_centlambda']
        self.var['nod_beta'][0] = self.var['map_centbeta']

        if (self.var['numlistpoints'] % 2) == 0:  # Number is even
            print('calcNpoint: Odd number - 1 divisible by 4 required.')
            return False
        elif  (self.var['numlistpoints'] - 1) % 4 != 0:
            print('calcNpoint: Odd number - 1 divisible by 4 required.')
            return False
        try:
            self.var['dithmap_stepsize'] = float(self.var['dithmap_stepsize'])
        except:
            print('calcNpoint: mapping stepsize must be a number.')
            return False

        if self.var['numlistpoints'] > 1:
            mapclam = self.var['map_centlambda']
            mapcbet = self.var['map_centbeta']
            dithstep = self.var['dithmap_stepsize']
            for idx in range(1, ((self.var['numlistpoints'] - 1) // 4) + 1):
                i =  (idx - 1) * 4
                self.var['map_lambda'][1 + i] = mapclam + idx * dithstep
                self.var['map_beta'][1 + i] = mapcbet
                self.var['map_lambda'][2 + i] = mapclam
                self.var['map_beta'][2 + i] = mapcbet + idx * dithstep
                self.var['map_lambda'][3 + i] = mapclam - idx * dithstep
                self.var['map_beta'][3 + i] = mapcbet
                self.var['map_lambda'][4 + i] = mapclam
                self.var['map_beta'][4 + i] = mapcbet - idx * dithstep
                self.var['nod_lambda'][1 + i] = mapclam + idx * dithstep / self.var['offpos_reduc']
                self.var['nod_beta'][1 + i] = mapcbet
                self.var['nod_lambda'][2 + i] = mapclam
                self.var['nod_beta'][2 + i] = mapcbet + idx * dithstep / self.var['offpos_reduc']
                self.var['nod_lambda'][3 + i] = mapclam - idx * dithstep / self.var['offpos_reduc']
                self.var['nod_beta'][3 + i] = mapcbet
                self.var['nod_lambda'][4 + i] = mapclam
                self.var['nod_beta'][4 + i] = mapcbet - idx * dithstep / self.var['offpos_reduc']

    def calcStare(self):
        if self.var['numlistpoints'] == 0:
            self.var['numlistpoints'] = 1
        self.var['map_lambda'] = [self.var['map_centlambda']] * self.var['numlistpoints']
        self.var['map_beta'] = [self.var['map_centbeta']] * self.var['numlistpoints']
        self.var['nod_lambda'] = [self.var['map_centlambda']] * self.var['numlistpoints']
        self.var['nod_beta'] = [self.var['map_centbeta']] * self.var['numlistpoints']

    def upright(self, pointidx, corneridx):
        dithstep = float(self.var['dithmap_stepsize'])
        # go up
        for upidx in range(1, corneridx):
            self.var['map_lambda'][pointidx] = self.var['map_lambda'][pointidx - 1] + dithstep
            self.var['map_beta'][pointidx] = self.var['map_beta'][pointidx - 1]
            self.var['nod_lambda'][pointidx] = self.var['nod_lambda'][pointidx - 1] +  \
                dithstep / float(self.var['offpos_reduc'])
            self.var['nod_beta'][pointidx] = self.var['nod_beta'][pointidx - 1]
            pointidx += 1
        # go right
        for rightidx in range(1, corneridx):
            self.var['map_lambda'][pointidx] = self.var['map_lambda'][pointidx - 1]
            self.var['map_beta'][pointidx] =  self.var['map_beta'][pointidx - 1] + dithstep
            self.var['nod_lambda'][pointidx] =  self.var['nod_lambda'][pointidx - 1]
            self.var['nod_beta'][pointidx] =  self.var['nod_beta'][pointidx - 1] +  \
                dithstep / float(self.var['offpos_reduc'])
            pointidx += 1

    def downleft(self, pointidx, corneridx):
        dithstep = float(self.var['dithmap_stepsize'])
        # go down
        for downidx in range(1, corneridx):
            self.var['map_lambda'][pointidx] = self.var['map_lambda'][pointidx - 1] - dithstep
            self.var['map_beta'][pointidx] = self.var['map_beta'][pointidx - 1]
            self.var['nod_lambda'][pointidx] =  self.var['nod_lambda'][pointidx - 1] -  \
                dithstep / float(self.var['offpos_reduc'])
            self.var['nod_beta'][pointidx] = self.var['nod_beta'][pointidx - 1]
            pointidx += 1
        # go left
        for leftidx in range(1, corneridx):
            self.var['map_lambda'][pointidx] = self.var['map_lambda'][pointidx - 1]
            self.var['map_beta'][pointidx] = self.var['map_beta'][pointidx - 1] - dithstep
            self.var['nod_lambda'][pointidx] = self.var['nod_lambda'][pointidx - 1]
            self.var['nod_beta'][pointidx] = self.var['nod_beta'][pointidx - 1] -  \
                dithstep / float(self.var['offpos_reduc'])
            pointidx += 1

    def calcSpiral(self):
        numpoints = self.var['dithmap_numpoints']
        numcorners = int(math.sqrt(numpoints)) - 1
        self.var['map_lambda'] = [ None ] * self.var['dithmap_numpoints']
        self.var['map_beta'] = [ None ] * self.var['dithmap_numpoints']
        self.var['nod_lambda'] = [ None ] * self.var['dithmap_numpoints']
        self.var['nod_beta'] = [ None ] * self.var['dithmap_numpoints']
        self.var['map_lambda'][0] = self.var['map_centlambda']
        self.var['map_beta'][0] = self.var['map_centbeta']
        self.var['nod_lambda'][0] = self.var['map_centlambda']
        self.var['nod_beta'][0] = self.var['map_centbeta']
        pointidx = 1
        for corneridx in range(1, numcorners + 1):
            self.upright(pointidx, corneridx)
            corneridx += 1
            self.downleft(pointidx, corneridx)
        for upidx in range(numcorners):
            self.var['map_lambda'][pointidx] = self.var['map_lambda'][pointidx - 1] +  \
                float(self.var['dithmap_stepsize'])
            self.var['map_beta'][pointidx] = self.var['map_beta'][pointidx - 1]
            self.var['nod_lambda'][pointidx] = self.var['nod_lambda'][pointidx - 1] +  \
                float(self.var['dithmap_stepsize']) / float(self.var['offpos_reduc'])
            self.var['nod_beta'][pointidx] = self.var['nod_beta'][pointidx - 1]
            pointidx += 1

    def calcGrtpos(self):
        # Compute red grating start positions for different distribution modes
        #print('computing grating positions ...')
        #print('scandist ', self.var['scandist'], ' red_lambda ', self.var['red_lambda'])
        if self.var['scandist'] == 'None':
            self.var['red_grstart'] = []
            if self.var['red_lambda'] == 'Start':
                self.var['red_grstart'].append(int(self.var['red_grtpos']))
            if self.var['red_lambda'] == 'Centre':
                unitsup = int(self.var['red_sizeup_isu'] * (self.var['red_posup'] - 1) / 2)
                self.var['red_grstart'].append(int(self.var['red_grtpos']) - unitsup)
            if self.var['red_lambda'] == 'Dither':
                unitsup = int(self.var['red_sizeup_isu'] * (self.var['red_posup'] - 1) / 2)
                self.var['red_grstart'].append(int(self.var['red_grtpos']))
        elif self.var['scandist'] == 'Split':
            self.var['red_grstart'] = [ None ] * self.var['splits']
            if self.var['red_lambda'] == 'Start':
                self.var['red_grstart'][0] = int(self.var['red_grtpos'])
            if self.var['red_lambda'] == 'Centre':
                unitsup = int(self.var['red_sizeup_isu'] * (self.var['red_posup'] - 1) / 2)
                self.var['red_grstart'][0] = int(self.var['red_grtpos']) - unitsup
            # distance travelled by each split
            distsplit = int(self.var['red_sizeup_isu'] * self.var['red_posup'] / self.var['splits'])
            for idx in range(1, self.var['splits']):
                self.var['red_grstart'][idx] = self.var['red_grstart'][idx - 1] +  distsplit
        else:  # Up and Down
            #distfactor = int(float(self.var['red_numgrtpos']) / float(self.var['nodcycles']))
            self.var['numnodcyc'] = self.var['nodcycles']
            self.var['red_grstart'] = [ None ] * self.var['numnodcyc']
            if self.var['red_lambda'] == 'Start':
                self.var['red_grstart'][0] = int(self.var['red_grtpos'])
                if self.var['scandist'] == 'Up':
                    distnodcycle = int(self.var['red_posup'] / self.var['numnodcyc'] * self.var['red_sizeup_isu'])
                    for idx in range(1, self.var['numnodcyc']):
                        self.var['red_grstart'][idx] = self.var['red_grstart'][idx - 1] + distnodcycle
                if self.var['scandist'] == 'Down':
                    distnodcycle = int(self.var['red_posdown'] / self.var['numnodcyc'] * self.var['red_sizedown_isu'])
                    for idx in range(1, self.var['numnodcyc']):
                        self.var['red_grstart'][idx] = self.var['red_grstart'][idx - 1] - distnodcycle
            elif self.var['red_lambda'] == 'Centre':
                if self.var['scandist'] == 'Up':
                    unitsup = int(self.var['red_sizeup_isu'] * (self.var['red_posup'] - 1) / 2)
                    distnodcycle = int(self.var['red_posup'] / self.var['numnodcyc'] *  self.var['red_sizeup_isu'])
                    self.var['red_grstart'][0] = int(self.var['red_grtpos']) - unitsup
                    for idx in range(1, self.var['numnodcyc']):
                        self.var['red_grstart'][idx] = self.var['red_grstart'][idx - 1] + distnodcycle
                if self.var['scandist'] == 'Down':
                    unitsdown = int(self.var['red_sizedown_isu'] * (self.var['red_posdown'] - 1) / 2)
                    distnodcycle = int(self.var['red_posdown'] / self.var['numnodcyc'] * self.var['red_sizedown_isu'])
                    self.var['red_grstart'][0] = int(self.var['red_grtpos']) + unitsdown
                    for idx in range(1, self.var['numnodcyc']):
                        self.var['red_grstart'][idx] = self.var['red_grstart'][idx - 1] - distnodcycle
            else:  # Dither or Inward
                #print('Dither or inward')
                if self.var['numnodcyc'] == 1:
                    if self.var['scandist'] == 'Up':
                        unitsup = int(self.var['red_sizeup_isu'] * (self.var['red_posup'] - 1) / 2)
                        distnodcycle = int(self.var['red_posup'] / self.var['numnodcyc'] * self.var['red_sizeup_isu'])
                        self.var['red_grstart'][0] = int(self.var['red_grtpos']) - unitsup
                        for idx in range(1, self.var['numnodcyc']):
                            self.var['red_grstart'][idx] = self.var['red_grstart'][idx - 1] + distnodcycle
                    if self.var['scandist'] == 'Down':
                        unitsdown = int(self.var['red_sizedown_isu'] * (self.var['red_posdown'] - 1) / 2)
                        distnodcycle = int(self.var['red_posdown'] / self.var['numnodcyc'] * self.var['red_sizedown_isu'])
                        self.var['red_grstart'][0] = int(self.var['red_grtpos']) + unitsdown
                        for idx in range(1, self.var['numnodcyc']):
                            self.var['red_grstart'][idx] = self.var['red_grstart'][idx - 1] - distnodcycle
                elif self.var['numnodcyc'] > 1:  #else:
                    self.var['red_grstart'][0] = int(self.var['red_grtpos'])
                    if self.var['scandist'] == 'Up':
                        unitsup = int(self.var['red_sizeup_isu'] * (self.var['red_posup'] - 1) / 2)
                        pospernodcycle = self.var['red_posup'] / self.var['numnodcyc']
                        distnodcycle = int(pospernodcycle * self.var['red_sizeup_isu'])
                        #print('unitsup, pospenodcycle, distnodcycle ', unitsup, pospernodcycle, distnodcycle)
                        widthnodcycle = int((pospernodcycle - 1) * self.var['red_sizeup_isu'])
                        stepsizered = self.var['red_sizeup_isu']
                        #print('stepsizered ', stepsizered)
                    elif self.var['scandist'] == 'Down':
                        unitsdown = int(self.var['red_sizedown_isu'] * (self.var['red_posdown'] - 1) / 2)
                        pospernodcycle = self.var['red_posdown'] / self.var['numnodcyc']
                        distnodcycle = int(pospernodcycle * self.var['red_sizedown_isu'])
                        widthnodcycle = int((pospernodcycle - 1) * self.var['red_sizedown_isu'])
                        stepsizered = self.var['red_sizedown_isu']
                    if self.var['scandist'] in ['Split', 'None']:
                        stepsizered = self.var['red_sizeup_isu']
                    if pospernodcycle <= 1.0: #
                        # self.update_text(self.e_status_text,
                        #     'RED: 1 grating position per nod cycle\n')
                        if (self.var['numnodcyc'] % 2) != 0:
                            self.var['red_grstart'][0] = int(self.var['red_grtpos'])
                        else:
                            self.var['red_grstart'][0] =  int(self.var['red_grtpos']) - distnodcycle // 2
                    else:
                        if (self.var['numnodcyc'] % 2) != 0:
                            self.var['red_grstart'][0] = int(self.var['red_grtpos']) - widthnodcycle // 2
                        else:
                            self.var['red_grstart'][0] = int(self.var['red_grtpos']) -  \
                                int(math.floor(widthnodcycle)) - int(stepsizered) // 2  ## CHECK
                                
                    #print('start ', self.var['red_grstart'])
                    revs = 1
                    #  begin spectral dithering routine
                    dith = 1
                    for i in range(1, self.var['numnodcyc'] - 1):
                        if (dith % 2) == 0:
                            #print('dith even ', dith, revs)
                            self.var['red_grstart'][dith] =  self.var['red_grstart'][0] -  \
                                int(math.floor(distnodcycle * revs))
                            revs += 1
                        else:
                            #print('dith odd ', dith, revs)
                            self.var['red_grstart'][dith] = self.var['red_grstart'][0] +  \
                                int(math.floor(distnodcycle * revs))
                        dith += 1
                    dith = dith - 1
                    if (self.var['numnodcyc'] % 2) != 0:
                        #print('numnodcy odd ', dith)
                        self.var['red_grstart'][dith + 1] =  self.var['red_grstart'][0] -  \
                            int(math.floor(distnodcycle * revs))
                    else:
                        #print('numnodcy even', dith)
                        self.var['red_grstart'][dith + 1] =  self.var['red_grstart'][0] +  \
                            int(math.floor(distnodcycle * revs))
                    #print('grstart ', self.var['red_grstart'])
                    # with inward dither simply reverse the starting positions
                    # to start at the edge
                    if self.var['red_lambda'] == 'Inward dither':
                        self.var['red_grstart'].reverse()

        # Compute blue grating start positions for different distribution modes
        if self.var['scandist'] == 'None':
            self.var['blue_grstart'] = []
            if self.var['blue_lambda'] == 'Start':
                self.var['blue_grstart'].append(int(self.var['blue_grtpos']))
            if self.var['blue_lambda'] == 'Centre':
                unitsup = int(self.var['blue_sizeup_isu'] * (self.var['blue_posup'] - 1) / 2)
                self.var['blue_grstart'].append(int(self.var['blue_grtpos']) - unitsup)
            if self.var['blue_lambda'] == 'Dither':
                unitsup = int(self.var['blue_sizeup_isu'] * (self.var['blue_posup'] - 1) / 2)
                self.var['blue_grstart'].append(int(self.var['blue_grtpos']))
        elif self.var['scandist'] == 'Split':
            self.var['blue_grstart'] = [ None ] * self.var['splits']
            if self.var['blue_lambda'] == 'Start':
                self.var['blue_grstart'][0] = int(self.var['blue_grtpos'])
            elif self.var['blue_lambda'] == 'Centre':
                unitsup = int(self.var['blue_sizeup_isu'] * (self.var['blue_posup'] - 1) / 2)
                self.var['blue_grstart'][0] = int(self.var['blue_grtpos']) - unitsup
            # distance travelled by each split
            distsplit = int(self.var['blue_sizeup_isu'] * self.var['blue_posup'] / self.var['splits'])
            for idx in range(1, self.var['splits']):
                self.var['blue_grstart'][idx] = self.var['blue_grstart'][idx - 1] + distsplit
        else:  # Up and Down
            #distfactor = int(float(self.var['blue_numgrtpos']) / float(self.var['nodcycles']))
            self.var['numnodcyc'] = self.var['nodcycles']
            self.var['blue_grstart'] = [ None ] * self.var['numnodcyc']
            if self.var['blue_lambda'] == 'Start':
                self.var['blue_grstart'][0] = int(self.var['blue_grtpos'])
                if self.var['scandist'] == 'Up':
                    distnodcycle = int(self.var['blue_posup'] / self.var['numnodcyc'] * self.var['blue_sizeup_isu'])
                    for idx in range(1, self.var['numnodcyc']):
                        self.var['blue_grstart'][idx] = self.var['blue_grstart'][idx - 1] + distnodcycle
                if self.var['scandist'] == 'Down':
                    distnodcycle = int(self.var['blue_posdown'] / self.var['numnodcyc'] * self.var['blue_sizedown_isu'])
                    for idx in range(1, self.var['numnodcyc']):
                        self.var['blue_grstart'][idx] = self.var['blue_grstart'][idx - 1] - distnodcycle
            elif self.var['blue_lambda'] == 'Centre':
                if self.var['scandist'] == 'Up':
                    unitsup = int(self.var['blue_sizeup_isu'] * (self.var['blue_posup'] - 1) / 2)
                    distnodcycle = int(self.var['blue_posup'] / self.var['numnodcyc'] *  self.var['blue_sizeup_isu'])
                    self.var['blue_grstart'][0] = int(self.var['blue_grtpos']) - unitsup
                    for idx in range(1, self.var['numnodcyc']):
                        self.var['blue_grstart'][idx] = self.var['blue_grstart'][idx - 1] + distnodcycle
                if self.var['scandist'] == 'Down':
                    unitsdown = int(self.var['blue_sizedown_isu'] * (self.var['blue_posdown'] - 1) / 2)
                    distnodcycle = int(self.var['blue_posdown'] / self.var['numnodcyc'] * self.var['blue_sizedown_isu'])
                    self.var['blue_grstart'][0] = int(self.var['blue_grtpos']) + unitsdown
                    for idx in range(1, self.var['numnodcyc']):
                        self.var['blue_grstart'][idx] = self.var['blue_grstart'][idx - 1] - distnodcycle
            else:  # Dither or Inward
                if self.var['numnodcyc'] == 1:
                    if self.var['scandist'] == 'Up':
                        unitsup = int(self.var['blue_sizeup_isu'] * (self.var['blue_posup'] - 1) / 2)
                        distnodcycle = int(self.var['blue_posup'] / self.var['numnodcyc'] * self.var['blue_sizeup_isu'])
                        self.var['blue_grstart'][0] = int(self.var['blue_grtpos']) - unitsup
                        for idx in range(1, self.var['numnodcyc']):
                            self.var['blue_grstart'][idx] = self.var['blue_grstart'][idx - 1] + distnodcycle
                    if self.var['scandist'] == 'Down':
                        unitsdown = int(self.var['blue_sizedown_isu'] * (self.var['blue_posdown'] - 1) / 2)
                        distnodcycle = int(self.var['blue_posdown'] / self.var['numnodcyc'] * self.var['blue_sizedown_isu'])
                        self.var['blue_grstart'][0] = int(self.var['blue_grtpos']) + unitsdown
                        for idx in range(1, self.var['numnodcyc']):
                            self.var['blue_grstart'][idx] = self.var['blue_grstart'][idx - 1] - distnodcycle
                if self.var['numnodcyc'] != 1:  #else:
                    self.var['blue_grstart'][0] = int(self.var['blue_grtpos'])
                    if self.var['scandist'] == 'Up':
                        unitsup = int(self.var['blue_sizeup_isu'] * (self.var['blue_posup'] - 1) / 2)
                        pospernodcycle = self.var['blue_posup'] / self.var['numnodcyc']
                        distnodcycle = int(pospernodcycle * self.var['blue_sizeup_isu'])
                        widthnodcycle = int((pospernodcycle - 1) * self.var['blue_sizeup_isu'])
                        stepsizeblue = self.var['blue_sizeup_isu']
                    if self.var['scandist'] == 'Down':
                        unitsdown = int(self.var['blue_sizedown_isu'] * (self.var['blue_posdown'] - 1) / 2)
                        pospernodcycle = self.var['blue_posdown'] / self.var['numnodcyc']
                        distnodcycle = int(pospernodcycle * self.var['blue_sizedown_isu'])
                        widthnodcycle = int((pospernodcycle - 1) * self.var['blue_sizedown_isu'])
                        stepsizeblue = self.var['blue_sizedown_isu']
                    if self.var['scandist'] in ['Split', 'None']:
                        stepsizeblue = self.var['blue_sizeup_isu']
                    if pospernodcycle <= 1.0: #
                        # self.update_text(self.e_status_text,
                        #     'BLUE: 1 grating positiion per nod cycle\n')
                        if (self.var['numnodcyc'] % 2) != 0:
                            self.var['blue_grstart'][0] = int(self.var['blue_grtpos'])
                        else:
                            self.var['blue_grstart'][0] = int(self.var['blue_grtpos']) - distnodcycle // 2
                    else:
                        if (self.var['numnodcyc'] % 2) != 0:
                            self.var['blue_grstart'][0] = int(self.var['blue_grtpos']) - widthnodcycle // 2
                        else:
                            self.var['blue_grstart'][0] = int(self.var['blue_grtpos']) -  \
                                int(math.floor(widthnodcycle)) - int(stepsizeblue) // 2  ## CHECK
                    revs = 1
                    #  begin spectral dithering routine
                    dith = 1
                    for i in range(1, self.var['numnodcyc'] - 1):
                        if (dith % 2) == 0:
                            self.var['blue_grstart'][dith] = self.var['blue_grstart'][0] -  \
                                int(math.floor(distnodcycle * revs))
                            revs += 1
                        else:
                            self.var['blue_grstart'][dith] = self.var['blue_grstart'][0] +  \
                                int(math.floor(distnodcycle * revs))
                        dith += 1
                    dith = dith - 1
                    if (self.var['numnodcyc'] % 2) != 0:
                        self.var['blue_grstart'][dith + 1] = self.var['blue_grstart'][0] -  \
                            int(math.floor(distnodcycle * revs))
                    else:
                        self.var['blue_grstart'][dith + 1] = self.var['blue_grstart'][0] +  \
                            int(math.floor(distnodcycle * revs))
                    # with inward dither simply reverse the starting positions
                    # to start at the edge
                    if self.var['blue_lambda'] == 'Inward dither':
                        self.var['blue_grstart'].reverse()

        # Compute values
        gratpos = np.array(self.var['red_grstart'])
        l, w = inductosyn2wavelength(gratpos, self.var['dichroic'], 'RED', 1)
        self.var['red_lambdastart'] = np.mean(l, axis=(1,2))
        gratpos = np.array(self.var['blue_grstart'])
        l, w = inductosyn2wavelength(gratpos, self.var['dichroic'], 'BLUE', self.var['order'])
        self.var['blue_lambdastart'] = np.mean(l, axis=(1,2))

    def calcInductosynPos(self):
        """ Convert input wavelength to inductosyn units and update GUI."""
        
        # Red
        xt = self.var['red_micron']
        if self.var['red_offset_type'] == 'um':
            if self.var['redshift'] == '-99.0':
                self.var['redshift'] = self.var['red_offset'] / xt
            xt += self.var['red_offset']
        if self.var['red_offset_type'] == 'kms':
            if self.var['redshift'] == '-99.0':
                self.var['redshift'] = velocity2z(self.var['red_offset'])
            xt = xt * (1.0 + self.var['redshift'])
        #print('Requested red wavelength: ' + str(xt))
        self.redGratPosMicron.setText('{0:.4f}'.format(round(xt,4)))
        grtpos = wavelength2inductosyn(xt, self.var['dichroic'], 'RED', 1, obsdate='')
        self.var['red_grtpos'] = int(grtpos)
        if self.var['red_offset_type'] == 'units' and self.var['red_offset'] != 0:
            self.var['red_grtpos'] = int(self.var['red_grtpos'] + self.var['red_offset'])
            l, lw = inductosyn2wavelength(
                                gratpos = int(self.var['red_grtpos']),
                                dichroic = self.var['dichroic'], array = 'RED',
                                order = 1,  # RED channel only operates in 1st order
                                obsdate = '')
            #red_micron_actual = l[0,8,12]
            red_micron_actual = np.mean(l[0,:,:])
            self.redGratPosMicron.setText(str(red_micron_actual).strip())
        self.redGratPosUnits.setText(str(self.var['red_grtpos']))
        
        # Blue
        xt = self.var['blue_micron']
        if self.var['blue_offset_type'] == 'um':
            if self.var['redshift'] == '-99.0':
                self.var['redshift'] = self.var['blue_offset'] / xt
            xt += self.var['blue_offset']
        if self.var['blue_offset_type'] == 'kms':
            if self.var['redshift'] == '-99.0':
                self.var['redshift'] = velocity2z(self.var['blue_offset'])
            xt = xt * (1.0 + self.var['redshift'])
        #print('Requested blue wavelength: ' + str(xt))
        self.blueGratPosMicron.setText('{0:.4f}'.format(round(xt,4)))
        grtpos = wavelength2inductosyn(xt, self.var['dichroic'], 'BLUE', self.var['order'], obsdate='')
        self.var['blue_grtpos'] = int(grtpos)
        if self.var['blue_offset_type'] == 'units' and self.var['blue_offset'] != 0:
            self.var['blue_grtpos'] = int(self.var['blue_grtpos'] + self.var['blue_offset'])
            l, lw = inductosyn2wavelength(
                                gratpos = int(self.var['blue_grtpos']),
                                dichroic = self.var['dichroic'], array = 'BLUE',
                                order = self.var['order'],  # RED channel only operates in 1st order
                                obsdate = '')
            #blue_micron_actual = l[0,8,12]
            blue_micron_actual = np.mean(l[0,:,:])
            self.blueGratPosMicron.setText(str(blue_micron_actual).strip())
        self.blueGratPosUnits.setText(str(self.var['blue_grtpos']))

    def grating_xls(self):
        """
        Called by compute button.
        """

        # sanity check - if entry boxes are empty, return
        try:
            t_int_source = int(self.onSourceTimeChop.text())
            n_grating_pos = int(self.noGratPosChop.text())
            n_map_pts = int(self.totMapPositions.text())
            self.var['nodcycles'] = int(self.nodcyclesPerMapPosition.text())
        except ValueError:
            message = 'Please enter non-zero values for on-source time and number of grating positions.'
            QMessageBox.about(self, "Grating", message)
            return

        # check for zero values
        if float(t_int_source) == 0. or float(n_grating_pos) == 0.:
            print('ERROR: Please enter ' +
            'non-zero values for On-source time and # of gratin positions.\n')
            return
        
        # for Bright Object mode, check that n is even
        if self.var['nodpattern'] in ['ABA', 'AABAA']:
            if (self.var['nodcycles'] % 2) != 0:
                print('ERROR: Selected Nod Pattern is Bright Object mode. ' +
                ' Number of A positions per B (n) must be an even number.\n')
                return

        # exposure time needed due to attain t_int_source, seconds
        t_int_chopped = t_int_source / self.obs_eff
        # time spent in one grating position, seconds
        # for Asymmetric chops
        if self.var['symmetry'] == 'Asymmetric': #self.var['obsmode'] != 'Beam switching':
            t_grating_pos = (t_int_chopped / (n_grating_pos)) + self.t_grating_move
        # for Symmetric chops
        else:
            t_grating_pos = (t_int_chopped / (2 * n_grating_pos)) + self.t_grating_move

        # above time needs to be a rounded up to nearest integer, seconds
        t_grating_pos_use = t_grating_pos
        # time it takes to complete all grating steps
        t_grating_sweep = t_grating_pos_use * n_grating_pos
        # number of chop cycles during one grating position
        n_cc_per_grating_pos = t_grating_pos_use * self.f_chop

        # Bright Object mode
        # print self.var['nodpattern']
        if self.var['nodpattern'] in ['ABA','AABAA']:
            # nod interval, seconds
            t_nod_interval = t_int_source * 2
            # time spent in one grating position, seconds
            t_grating_pos = (t_int_chopped / (n_grating_pos)) + self.t_grating_move
            # total time to complete map, minutes
            t_map = (self.var['nodcycles'] + 1) *  \
                (t_int_source*2 + self.t_ta_move) * n_map_pts / self.var['nodcycles'] / 60.
            # update GUI
            self.nodCycles.setText('')
            self.noGratPos4Nod.setText('')
            self.gratCycle4Nod.setText('')
        else: # (AB)*n and (ABBA)*(n/2) modes
            t_nod_interval = 30.    # nod interval, seconds
            # number of nod cycles needed to complete all grating positions
            #n_nod_cycles = int( t_grating_sweep / t_nod_interval)   # CHECK is this the same ???
            n_nod_cycles = mround(math.ceil (t_grating_sweep * 2 / t_nod_interval), 2) / 2
            # number of grating positions on one nod
            n_grating_pos_per_nod = n_grating_pos / n_nod_cycles
            # time of one nod, based on the number of grating positions on the nod, seconds.
            t_nod_grating = t_grating_pos_use * n_grating_pos_per_nod # We want it to be 30
            # time interval of AB nod pair
            t_nod_ab = (t_nod_grating + self.t_ta_move) * 2  # should be 80
            # total time to step thru all grating positions
            t_total = t_nod_ab * n_nod_cycles
            # total time to complete map, minutes
            t_map = t_total * n_map_pts / 60.

            # update GUI
            self.nodCycles.setText("{0:.1f}".format(round(n_nod_cycles)))
            self.noGratPos4Nod.setText("{0:.1f}".format(n_grating_pos_per_nod))
            self.gratCycle4Nod.setText("{0:.1f}".format(t_nod_grating))
        # Common updates
        self.ccPerGratPos.setText("{0:.2f}".format(round(n_cc_per_grating_pos,2)))
        self.timeCompleteMap.setText("{0:.2f}".format(round(t_map,2)))
        self.redGratPosUp.setText("{0:.0f}".format(round(n_grating_pos,0)))
        self.blueGratPosUp.setText("{0:.0f}".format(round(n_grating_pos,0)))
        self.blueCC4ChopPos.setText("{0:.0f}".format(round(n_cc_per_grating_pos,0)))  # Missing in previous version
        self.redCC4ChopPos.setText("{0:.0f}".format(round(n_cc_per_grating_pos,0)))
        
        # Automatic build
        self.buildObs()
        
    def writeObs(self):
        """
        Write observation.
        """
        scan = ScanDescription()
        # make map
        print('Making ' + self.var['pattern'] + ' map.')
        if self.var['pattern'] == 'Inward spiral':
            self.var['map_lambda'].reverse()
            self.var['map_beta'].reverse()
            result = self.makemap(scan)
        else:  # 'File', 'N-point cross', 'Spiral', 'Stare'
            result = self.makemap(scan)

        # save template and update History box: insert text at beginning
        if result != False:
            self.exportSct()
            
    def makemap(self, s):
        """
        Create map.        
        """
        posidx = 0
        # Loop through scan writing process based on the length of map file
        if self.var['nodpattern'] in ['ABA', 'AABAA']:
            result = self.writenods(posidx, s)
            if result == False:
                print('ERROR writing nods.')
                return False
        else:
            for ml, mb in zip(self.var['map_lambda'], self.var['map_beta']):
                # These are overwritten by specific map position definitions in writeA and writeB
                s.scn['del_lam_map'] = ml  # self.var['map_lambda'][posidx]
                s.scn['del_bet_map'] = mb  # self.var['map_beta'][posidx]
                print('Writing scans for position ' + str(posidx + 1))
                result = self.writenods(posidx, s)
                if result == False:
                    print('ERROR writing nods.')
                    return False
                posidx += 1

        print('Wrote ' + str(self.var['ind_scanindex']) + ' scans.')
        
    def writenods(self, posidx, s):
        rewind = 0
        if self.var['nodcycles'] != 0:
            if self.var['nodpattern'] == 'AB':
                for idx in range(self.var['nodcycles']):
                    nodcyclenum = idx
                    if self.var['rewind'] == 'Auto':
                        if self.var['ind_scanindex'] == 0:
                            rewind = 2  # force for first scan description
                        elif self.var['ind_scanindex'] > 0:
                            rewind = 1  # allow for all A
                    # write A
                    for splitidx in range(self.var['splits']):
                        result = self.writeA(posidx, s, nodcyclenum, splitidx, rewind)
                        if result == False:
                            return False
                    rewind = 0  # block for all B
                    # write B
                    for splitidx in range(self.var['splits']):
                        result = self.writeB(posidx, s, nodcyclenum, splitidx, rewind)
            elif self.var['nodpattern'] == 'ABBA':
                idx = 0
                while idx < self.var['nodcycles']:
                    nodcyclenum = idx
                    if self.var['rewind'] == 'Auto':
                        if self.var['ind_scanindex'] == 0:
                            rewind = 2  # force for first scan description
                        elif self.var['ind_scanindex'] > 0:
                            rewind = 1  # allow for all A
                    # write A
                    for splitidx in range(self.var['splits']):
                        if splitidx > 0: rewind = 0
                        result = self.writeA(posidx, s, nodcyclenum, splitidx, rewind)
                        if result == False:
                            return False
                    rewind = 0  # block for all B
                    # write B
                    for splitidx in range(self.var['splits']):
                        self.writeB(posidx, s, nodcyclenum, splitidx, rewind)
                    idx += 1
                    nodcyclenum = idx
                    # continue if we have even number of nod cycles
                    if nodcyclenum < self.var['nodcycles']:
                        if self.var['rewind'] == 'Auto':
                            rewind = 1  # allow for first B
                        # write B
                        for splitidx in range(self.var['splits']):
                            if splitidx > 0: rewind = 0
                            self.writeB(posidx, s, nodcyclenum, splitidx, rewind)
                        rewind = 0  # block for all A
                        # write A
                        for splitidx in range(self.var['splits']):
                            self.writeA(posidx, s, nodcyclenum, splitidx, rewind)
                    idx += 1
            if self.var['nodpattern'] in ['ABA', 'AABAA']:
                while posidx < self.var['dithmap_numpoints']:
                    nodcyclenum = 0
                    print('Writing scans for position ' + str(posidx + 1))
                    # write first half of As (self.var['nodcycles'] / 2)
                    while nodcyclenum < (self.var['nodcycles'] / 2):
                        if posidx > self.var['dithmap_numpoints'] - 1:
                            print('INFO: No available next map position for next on (A) position.\n'+
                                  'Think about using a bigger map or increasing n. Going to off (B) position\n')
                            break
                        rewind = 0  # block rewind for all B
                        if self.var['rewind'] == 'Auto':
                            if self.var['ind_scanindex'] == 0:
                                rewind = 2  # force rewind for first scan
                            else:
                                if posidx % self.var['nodcycles'] == 0:
                                    rewind = 1  # allow for all A
                        for splitidx in range(self.var['splits']):
                            result = self.writeA(posidx, s, nodcyclenum, splitidx, rewind)
                            if result == False:
                                return False
                        nodcyclenum += 1
                        posidx += 1
                    # write middle B
                    posidx -= 1
                    rewind = 0  # block for all B
                    for splitidx in range(self.var['splits']):
                        self.writeB(posidx, s, nodcyclenum, splitidx, rewind)
                    posidx += 1

                    # write second half of As
                    while nodcyclenum <= self.var['nodcycles'] - 1:
                        if posidx > self.var['dithmap_numpoints'] - 1:
                            print('No available next map position for next on (A) position.\n ' +
                                  'Think about using a bigger map or decreasing n.')
                            break
                        for splitidx in range(self.var['splits']):
                            self.writeA(posidx, s, nodcyclenum, splitidx, rewind)
                        nodcyclenum += 1
                        posidx += 1
                    # posidx -= 1
            elif self.var['nodpattern'] == 'A':
                for idx in range(self.var['nodcycles']):
                    nodcyclenum = idx
                    if self.var['rewind'] == 'Auto' and  \
                        self.var['ind_scanindex'] == 0:
                        rewind = 2  # force for first scan description
                    if self.var['rewind'] == 'Auto' and  \
                        self.var['ind_scanindex'] > 0:
                        rewind = 1  # allow for all A
                    # write A
                    for splitidx in range(self.var['splits']):
                        result = self.writeA(posidx, s, nodcyclenum, splitidx, rewind)
                        if result == False:
                            return False
        else:  # case of no nod, just write the on position
            print('No nod: not implemented yet.')
    
    def writeA(self, posidx, s, nodcyclenum, splitidx, rewind):
        self.populate_scan(s, nodcyclenum, splitidx)
        s.scn['los_focus_update'] = rewind
        s.scn['offpos_lambda'] = 0
        s.scn['offpos_beta'] = 0
        s.scn['del_lam_map'] = self.var['map_lambda'][posidx]
        s.scn['del_bet_map'] = self.var['map_beta'][posidx]
        # pass the current map positions to the off position for matched nodding
        self.var['map_laston_lambda'] = s.scn['del_lam_map']
        self.var['map_laston_beta'] = s.scn['del_bet_map']
        s.scn['ch_beam'] = 1  # always on regardless of tracking

        scannum = self.var['ind_scanindex'] + 1
        scanfilename = '{0:05d}_{1:s}_'.format(scannum, self.var['obsid']) + \
                str(int(round(self.var['map_laston_lambda']))).strip() + '_' +  \
                str(int(round(self.var['map_laston_beta']))).strip() + '_A.scn'
        scanfilepath = os.path.join(self.var['scandesdir'], self.var['obsid'], scanfilename)        
        # print scanfilename
        check = s.check()
        if check[0] == 'NoErrors':
            print('Writing nod A.')
            self.var['ind_scanindex'] += 1
            s.write(scanfilepath)
        else:
            print(check[1])
            return False

    def writeB(self, posidx, s, nodcyclenum, splitidx, rewind):
        self.populate_scan(s, nodcyclenum, splitidx)
        s.scn['los_focus_update'] = rewind
        if self.var['offpos'] == 'Matched':
            s.scn['offpos_lambda'] = 0.
            s.scn['offpos_beta'] = 0.
            s.scn['del_lam_map'] = self.var['map_laston_lambda']
            s.scn['del_bet_map'] = self.var['map_laston_beta']
        elif self.var['offpos'] == 'Absolute':
            s.scn['offpos_lambda'] = 0.
            s.scn['offpos_beta'] = 0.
            s.scn['del_lam_map'] = 0.
            s.scn['del_bet_map'] = 0.
            s.scn['target_lambda'] = self.var['offpos_lambda']
            s.scn['target_beta'] = self.var['offpos_beta']
        elif self.var['offpos'] == 'Relative to target':
            s.scn['offpos_lambda'] = self.var['offpos_lambda']
            s.scn['offpos_beta'] = self.var['offpos_beta']
            s.scn['del_lam_map'] = 0.
            s.scn['del_bet_map'] = 0.
        elif self.var['offpos'] == 'Relative to active map pos':
            s.scn['offpos_lambda'] = self.var['offpos_lambda'] + self.var['nod_lambda'][posidx]
            s.scn['offpos_beta'] = self.var['offpos_beta'] + self.var['nod_beta'][posidx]
            if self.var['pattern'] == 'File':
                s.scn['offpos_lambda'] = self.var['nod_lambda'][posidx]
                s.scn['offpos_beta'] = self.var['nod_beta'][posidx]
            s.scn['del_lam_map'] = 0.
            s.scn['del_bet_map'] = 0.

        # Set beam variable to -1 (Asymmetric chop and tracking on) or
        # 0 (Asymmetric chop and tracking off) or -1 (Symmetric chop)
        if self.var['symmetry'] == 'Asymmetric':
            if self.var['tracking'] == 'On':
                s.scn['ch_beam'] = -1
            else:
                s.scn['ch_beam'] = 0
        else:
            s.scn['ch_beam'] = -1

        scannum = self.var['ind_scanindex'] + 1
        scanfilename = '{0:05d}_{1:s}_'.format(scannum, self.var['obsid']) + \
            str(int(round(self.var['map_laston_lambda']))).strip() + '_' +  \
            str(int(round(self.var['map_laston_beta']))).strip() + '_B.scn'
        scanfilepath = os.path.join(self.var['scandesdir'], self.var['obsid'], scanfilename)        

        check = s.check()
        if check[0] == 'NoErrors':
            print('Writing nod B.')
            self.var['ind_scanindex'] += 1
            s.write(scanfilepath)
        else:
            print(check[1])
            return False

        # Reset the target coord params because the absolute case changes them
        s.scn['target_lambda'] = self.var['target_lambda_deg']
        s.scn['target_beta'] = self.var['target_beta_deg']
        s.scn['obs_coord_sys'] = self.var['target_coordsys']

    def populate_scan(self, s, nodcyclenum, splitidx):
        """
        Update scan with variable values.
        """
        s.scn['target_name'] = self.var['target_name']
        s.scn['aorid'] = self.var['aorid']
        s.scn['filegp_r'] = self.var['filegp_r']
        s.scn['filegp_b'] = self.var['filegp_b']
        s.scn['obstype'] = self.var['obstype']
        # s.scn['focusoff'] = self.var['focusoff']
        s.scn['srctype'] = self.var['srctype']
        s.scn['instmode'] = self.var['instmode']  # 'nodtype'? 'obsmode'?
        s.scn['redshift'] = self.var['redshift']
        s.scn['obs_coord_sys'] = self.var['target_coordsys']
        s.scn['target_lambda'] = self.var['target_lambda_deg']
        s.scn['target_beta'] = self.var['target_beta_deg']
        s.scn['mapcoord_system'] = self.var['mapcoord_system']
        s.scn['off_coord_sys'] = 'J2000'
        s.scn['offpos_lambda'] = self.var['offpos_lambda']
        s.scn['offpos_beta'] = self.var['offpos_beta']
        s.scn['detangle'] = self.var['detangle']
        if self.var['commandline_option'] == '0':
            s.scn['primaryarray'] = self.var['primaryarray']
        elif self.var['commandline_option'] == '1':
            s.scn['primaryarray'] = self.var['setpoint']
        s.scn['los_focus_update'] = 0
        s.scn['nodpattern'] = self.var['nodpattern']
        s.scn['dichroic'] = self.var['dichroic']
        s.scn['order'] = self.var['order']
        s.scn['blue_filter'] = self.var['blue_filter']
        s.scn['blue_micron'] = self.var['blue_micron']
        s.scn['red_micron'] = self.var['red_micron']        
        s.scn['gr_cycles'] = [self.var['red_grtcyc'], self.var['blue_grtcyc']]
        s.scn['gr_stepsize_up'] = [
            int(self.var['red_sizeup_isu']),
            int(self.var['blue_sizeup_isu'])]
        s.scn['gr_stepsize_down'] = [
            int(self.var['red_sizedown_isu']),
            int(self.var['blue_sizedown_isu'])]
        gratingDirection = self.gratingDirection.currentText()
        if gratingDirection == "None":
            s.scn['gr_start'] = [int(self.var['red_grstart']), int(self.var['blue_grstart'])]
            s.scn['gr_lambda'] = [self.var['red_lambdastart'], self.var['blue_lambdastart']]
            s.scn['gr_steps_up'] = [   # minimum steps is 1
                max([self.var['red_posup'], 1]),
                max([self.var['blue_posup'], 1])]
            s.scn['gr_steps_down'] = [int(self.var['red_posdown']), int(self.var['blue_posdown'])]
        elif gratingDirection == "Up":
            s.scn['gr_start'] = [
                int(self.var['red_grstart'][nodcyclenum]),
                int(self.var['blue_grstart'][nodcyclenum])]
            s.scn['gr_lambda'] = [
                self.var['red_lambdastart'][nodcyclenum],
                self.var['blue_lambdastart'][nodcyclenum]]
            s.scn['gr_steps_up'] = [
                max([int(self.var['red_posup'] / self.var['nodcycles']), 1]),
                max([int(self.var['blue_posup'] / self.var['nodcycles']), 1])]
            s.scn['gr_steps_down'] = [int(self.var['red_posdown']), int(self.var['blue_posdown'])]
        elif gratingDirection == "Down":
            s.scn['gr_start'] = [
                int(self.var['red_grstart'][nodcyclenum]),
                int(self.var['blue_grstart'][nodcyclenum])]
            s.scn['gr_lambda'] = [
                self.var['red_lambdastart'][nodcyclenum],
                self.var['blue_lambdastart'][nodcyclenum]]
            s.scn['gr_steps_up'] = [max([self.var['red_posup'], 1]), max([self.var['blue_posup'], 1])]
            s.scn['gr_steps_down'] = [
                int(self.var['red_posdown'] / self.var['nodcycles']),
                int(self.var['blue_posdown'] / self.var['nodcycles'])]
        elif gratingDirection == "Split":
            s.scn['gr_start'] = [
                int(self.var['red_grstart'][splitidx]),
                int(self.var['blue_grstart'][splitidx])]
            s.scn['gr_lambda'] = [
                    self.var['red_lambdastart'][splitidx], 
                    self.var['blue_lambdastart'][splitidx]]
            s.scn['gr_steps_up'] = [
                max([int(self.var['red_posup'] / self.var['splits']), 1]),
                max([int(self.var['blue_posup'] / self.var['splits']), 1])]
            s.scn['gr_steps_down'] = [
                max([int(self.var['red_posdown'] / self.var['splits']), 1]),
                max([int(self.var['blue_posdown'] / self.var['splits']), 1])]

        if self.var['nodpattern'] in ['ABA', 'AABAA']:
            s.scn['gr_start'] = [int(self.var['red_grstart'][0]), int(self.var['blue_grstart'][0])]
            s.scn['gr_lambda'] = [self.var['red_lambdastart'][0], self.var['blue_lambdastart'][0]]
            s.scn['gr_steps_up'] = [int(self.var['red_posup']), int(self.var['blue_posup'])]
            s.scn['gr_steps_down'] = [int(self.var['red_posdown']), int(self.var['blue_posdown'])]

        # minimum steps is 1
        if s.scn['gr_steps_up'][0] < 1:
            s.scn['gr_steps_up'][0] = int(1)
        if s.scn['gr_steps_up'][1] < 1:
            s.scn['gr_steps_up'][1] = int(1)

        s.scn['ramplength'] = [self.var['red_ramplen'], self.var['blue_ramplen']]
        s.scn['ch_scheme'] = self.var['ch_scheme']
        s.scn['chopcoord_system'] = self.var['chopcoord_system']
        s.scn['chop_amp'] = self.var['chop_amp']
        s.scn['ch_tip'] = self.var['chop_tip']
        s.scn['ch_beam'] = 1
        s.scn['chop_posang'] = self.var['chop_posang']
        s.scn['ch_cycles'] = [self.var['red_chopcyc'], self.var['blue_chopcyc']]
        if self.var['chopphase'] == 'Default':
            s.scn['chop_manualphase'] = self.chop_phase_default
        elif  self.var['chopphase'] == 'Manual':
            s.scn['chop_manualphase'] = self.var['chop_manualphase']
        s.scn['chop_length'] = self.var['chop_length']
        s.scn['sel_cap'] = [self.var['red_capacitor'], self.var['blue_capacitor']]
        s.scn['zero_bias'] = [self.var['red_zbias'], self.var['blue_zbias']]
        #bluezerobiasold = s.scn['zero_bias'][1]
        if s.scn['zero_bias'][1] == 90:
            s.scn['zero_bias'][1] = 75
        if s.scn['zero_bias'][0] == 50 and s.scn['zero_bias'][1] == 90:
            s.scn['zero_bias'][0] = 60
        s.scn['biasr'] = [self.var['red_biasr'], self.var['blue_biasr']]
        s.scn['heater'] = [0, 0]
        s.scn['cal_src_temp'] = 0.

    def exportSct(self):
        """
        Write a scan template file *.sct to local disk.
        """
        # Create dictionary
        sctPars = {}
        for key in self.k2tw:
            label = self.k2tw[key]
            if isinstance(label, QLineEdit):
                try:
                    sctPars[key] = label.text()
                except:
                    print(key + 'is unkown.')
            elif isinstance(label, QComboBox):
                try:
                    sctPars[key] = label.currentText()
                except:
                    print(key + 'is unkown.')
            else:  # No widget, just variable
                if key == 'MAPLISTPATH':
                    # Save the file name only
                    sctPars[key] = os.path.basename(self.mapListPath)
                else:
                    print('Unknown key ',key)
        # Call writing routine
        writeSct(sctPars, self.sctfile)
        
class ScanDescription(QObject):
    """ Scan Description class """
    MAX_GR_STEP = int(10000) * int(1024)  # in grating units, 1024*inductosyn
    MIN_GR_POS = int(0)
    MAX_GR_POS = 0x200400
    MAX_RAMP_LENGTH = int(256)
    MAX_SUBRAMP_LENGTH = int(128)
    BLUEMIN, BLUEMAX = 29, 131
    REDMIN, REDMAX = 99, 221
    MAX_CH_AMP = 300
    RED_ZB_MAX  = 0.01   # mV
    RED_ZB_MIN  = 501.1   # mV
    RED_BR_MAX  = -70.21
    RED_BR_MIN  = 70.70
    BLUE_ZB_MAX = 0.0   # mV
    BLUE_ZB_MIN = 150.   # mV
    BLUE_BR_MAX = -150.
    BLUE_BR_MIN = 150.
    DICHROIC_VAL=[105, 130]  # um

    def __init__(self):
        """ initialize """
        self.scn = {
            'aorid': 'NONE',    # aor_id
            'filegp_r': 'NONE',
            'filegp_b': 'NONE',
            'obstype': 'NONE',
            # 'focusoff': 'NONE',  # 20170106: placeholder
            'srctype': 'NONE',
            'instmode': 'NONE',
            'target_name': 'NONE',   # object_name
            'redshift': -99.,
            'obs_coord_sys': 'NONE',
            'mapcoord_system': 'NONE',  # map_coord_sys
            'off_coord_sys': 'NONE',
            'target_lambda': 375., 'target_beta': -99.,  #  obslam, obsbet
            'del_lam_map': 0., 'del_bet_map': 0.,
            'offpos_lambda': 0., 'offpos_beta': 0., # del_lam_off, del_bet_off
            'detangle': 360.,   # det_angl y-axis of detector NofE in deg -180 to 180
            'primaryarray': 'NONE',  # prime_array
            'los_focus_update': 0,
            'nodpattern': 'NONE',
            'dichroic': 0,  # wavelength in um of dichroic
            'order': -1,  # gr_b_order
            'blue_filter': -1,  # filter used with Blue
            'gr_lambda': [-1., -1.],
            'gr_cycles': [int(-1), int(-1)],
            'gr_start': [0xFFFFFFFF, 0xFFFFFFFF],
            # ['FFFFFFFF'XUL,'FFFFFFFF'XUL], XUL = hexadecimal unsigned int
            'gr_steps_up': [int(-1), int(-1)],
            'gr_stepsize_up': [self.MAX_GR_STEP + 1, self.MAX_GR_STEP + 1],
            'gr_steps_down': [int(-1), int(-1)],
            'gr_stepsize_down': [self.MAX_GR_STEP + 1, self.MAX_GR_STEP + 1],
            'ramplength': [0, 0],
            'ch_scheme': 'NONE',
            'chopcoord_system': 'NONE',  # ch_coord_sys
            'chop_amp': -1.,  # ch_amp in arcsec
            'ch_tip': -1.,
            'ch_beam': -1,
            'chop_posang': -1.,  # ch_posangle in degrees
            'ch_cycles': [0, 0],   # in cycles as set by ch_scheme
            'chop_manualphase': -1.,   # ch_phase  in degrees
            'chop_length': 0,   # choplength  in readouts
            'sel_cap': [0, 0],   # which capacitor?
            'zero_bias': [2 * self.RED_ZB_MAX - self.RED_ZB_MIN,
                          2 * self.BLUE_ZB_MAX - self.BLUE_ZB_MIN],
            'biasr': [2 * self.RED_BR_MAX - self.RED_BR_MIN,
                      2 * self.BLUE_BR_MAX - self.BLUE_BR_MIN],
            'heater': [0., 0.],   # heater voltage
            'cal_src_temp': 0.,
            'subramp_length': [0, 0],
            'anz_frames': 0,   # number of frames in this scan
            'subramps_per_choppos': [0, 0],   # num of subramps per chop pos
            'subramps_per_ramp': [0, 0],   # num of chop pos per cycles
            'choppos_per_cycle': 0  # num of chop pos per cycle as defined by ch_scheme
            }

    def check(self):
        """ check Scan Description and return any error """
        errmsg = ''
        if self.scn['aorid'] == "NONE": errmsg += 'AORID not set\n'
        if self.scn['filegp_r'] == "NONE": errmsg += 'FILEGP_R not set\n'
        if self.scn['filegp_b'] == "NONE": errmsg += 'FILEGP_B not set\n'
        if self.scn['obstype'] == "NONE": errmsg += 'Obs Type not set\n'
        # if self.scn['focusoff'] == "NONE": errmsg += 'FOCUSOFF not set\n'
        if self.scn['srctype'] == "NONE": errmsg += 'Source Type not set\n'
        if self.scn['instmode'] == "NONE": errmsg += 'Inst. mode not set\n'
        if self.scn['redshift'] == -99.: errmsg += 'Redshift not set\n'
        if self.scn['target_name'] == "NONE": errmsg += 'Object name not set\n'
        if self.scn['target_lambda'] < 0. or self.scn['target_lambda'] >= 360.:
            errmsg += 'OBSLAM out of range\n '
        if self.scn['target_beta'] < -90.0 or self.scn['target_beta'] > 90:
            errmsg += 'OBSBET out of range\n '
        if self.scn['detangle'] < -180.0 or self.scn['detangle'] > 180:
            errmsg += 'DET_ANGL out of range\n '
        if self.scn['los_focus_update'] < 0 or self.scn['los_focus_update'] > 2:
            errmsg += 'LOSF_UPD out of range\n '
        if self.scn['nodpattern'] == "NONE": errmsg += 'NODPATT not set\n'
        if self.scn['dichroic'] != self.DICHROIC_VAL[0] and  \
            self.scn['dichroic'] != self.DICHROIC_VAL[1]:
            errmsg += 'unkown DICHROIC\n '
        if self.scn['order'] != 1 and self.scn['order'] != 2:
            errmsg += 'GR_b_order out of range\n'
        if self.scn['blue_filter'] != 1 and self.scn['blue_filter'] != 2:
            errmsg += 'G_FLT_B out of range\n'

        if self.scn['gr_lambda'][1] < self.BLUEMIN or  \
            self.scn['gr_lambda'][1] > self.BLUEMAX:
            errmsg += 'GR_LAMBDA_b out of range\n '
        if self.scn['gr_cycles'][1] < 0: errmsg += 'GR_CYCLES_b negative\n '
        if self.scn['gr_start'][1] < self.MIN_GR_POS or  \
            self.scn['gr_start'][1] > self.MAX_GR_POS:
            errmsg += 'GR_START_b out of range\n '
        if self.scn['gr_steps_up'][1] <= 0:
            errmsg += 'GR_STEPS_UP_b not positive\n '
        if abs(self.scn['gr_stepsize_up'][1]) > self.MAX_GR_STEP:
            errmsg += 'GR_STEPSIZE_UP_b too large\n '
        if self.scn['gr_steps_down'][1] < 0:
            errmsg += 'GR_STEPS_DOWN_b negative\n '
        if abs(self.scn['gr_stepsize_down'][1]) > self.MAX_GR_STEP:
            errmsg += 'GR_STEPSIZE_DOWN_b too large\n '

        if self.scn['gr_lambda'][0] < self.REDMIN or  \
            self.scn['gr_lambda'][0] > self.REDMAX:
            errmsg += 'GR_LAMBDA_r out of range\n '
        if self.scn['gr_cycles'][0] < 0: errmsg += 'GR_CYCLES_r negative\n '
        if self.scn['gr_start'][0] < self.MIN_GR_POS or  \
            self.scn['gr_start'][0] > self.MAX_GR_POS:
            errmsg += 'GR_START_r out of range\n '
        if self.scn['gr_steps_up'][0] <= 0:
            errmsg += 'GR_STEPS_UP_r not positive\n '
        if abs(self.scn['gr_stepsize_up'][0]) > self.MAX_GR_STEP:
            errmsg += 'GR_STEPSIZE_UP_r too large\n '
        if self.scn['gr_steps_down'][0] < 0:
            errmsg += 'GR_STEPS_DOWN_r negative\n '
        if abs(self.scn['gr_stepsize_down'][0]) > self.MAX_GR_STEP:
            errmsg += 'GR_STEPSIZE_DOWN_r too large\n '

        if self.scn['ramplength'][1] <= 0 or  \
            self.scn['ramplength'][1] > self.MAX_RAMP_LENGTH:
            errmsg += 'RAMPLENGTH_b out of range\n '
        if self.scn['ramplength'][0] <= 0 or  \
            self.scn['ramplength'][0] > self.MAX_RAMP_LENGTH:
            errmsg += 'RAMPLENGTH_r out of range\n '

        if self.scn['ch_scheme'] != '2POINT' and  \
            self.scn['ch_scheme'] != '4POINT':
            errmsg += 'CH_SCHEME unknown\n '
        if self.scn['chop_amp'] < 0 or self.scn['chop_amp'] > self.MAX_CH_AMP:
            errmsg += 'CH_THROW out of range\n '
        if float(self.scn['chop_posang']) < 0 or  \
            float(self.scn['chop_posang']) >= 360:
            errmsg += 'CH_POSANGLE out of range\n '
        if self.scn['ch_cycles'][1] <= 0: errmsg += 'CH_CYCLES_b negative\n '
        if self.scn['ch_cycles'][0] <= 0: errmsg += 'CH_CYCLES_r negative\n '
        if float(self.scn['chop_manualphase']) < 0 or  \
            float(self.scn['chop_manualphase']) >= 360:
            errmsg += 'CH_PHASE out of range\n '
        if self.scn['chop_length'] <= 0: errmsg += 'CHOPLENGTH out of range\n '
        capacitors = ["1330", "604", "351", "238"]
        if str(self.scn['sel_cap'][1]) not in capacitors:
            errmsg += 'SEL_CAP_b unknown value\n '
        if str(self.scn['sel_cap'][0]) not in capacitors:
            errmsg += 'SEL_CAP_r unknown value\n '

        if self.scn['zero_bias'][1] > self.BLUE_ZB_MIN or  \
            self.scn['zero_bias'][1] < self.BLUE_ZB_MAX:
            errmsg += 'Z_BIAS_B out of range\n '
        if self.scn['biasr'][1] > self.BLUE_BR_MIN or  \
            self.scn['biasr'][1] < self.BLUE_BR_MAX:
            errmsg += 'BIASR_B out of range\n '

        if self.scn['zero_bias'][0] > self.RED_ZB_MIN or  \
            self.scn['zero_bias'][0] < self.RED_ZB_MAX:
            errmsg += 'Z_BIAS_R out of range\n '
        if self.scn['biasr'][0] > self.RED_BR_MIN or  \
            self.scn['biasr'][0] < self.RED_BR_MAX:
            errmsg += 'BIASR_R out of range\n '

        if errmsg == '':
            if self.scn['ch_scheme'] == '2POINT':
                self.scn['choppos_per_cycle'] = 2
            if self.scn['ch_scheme'] == '4POINT':
                self.scn['choppos_per_cycle'] = 4

            # check BLUE
            gr_end = self.scn['gr_start'][1] +  \
                self.scn['gr_steps_up'][1] * self.scn['gr_stepsize_up'][1]
            if gr_end < self.MIN_GR_POS or gr_end > self.MAX_GR_POS:
                errmsg += 'Blue grating exceeds range on up\n '
            gr_end = gr_end -  \
                self.scn['gr_steps_down'][1] * self.scn['gr_stepsize_down'][1]
            if gr_end < self.MIN_GR_POS or gr_end > self.MAX_GR_POS:
                errmsg += 'Blue grating exceeds range on down\n '

            ramplength = self.scn['ramplength'][1]
            choplength = self.scn['chop_length']

            if ramplength > choplength:
                if ramplength % choplength != 0:
                    errmsg += 'RAMPLENGTH_b not multiple of CHOPLENGTH\n '
                if self.scn['ch_scheme'] == '4POINT':
                    errmsg += 'RAMPLENGTH_b>CHOPLENGTH not allowed for 4POINT\n '
                self.scn['subramp_length'][1] = choplength
                self.scn['subramps_per_choppos'][1] = 1
                self.scn['subramps_per_ramp'][1] = ramplength / choplength
            else:
                if choplength % ramplength != 0:
                    errmsg += 'CHOPLENGTH not multiple of RAMPLENGTH_b\n '
                self.scn['subramp_length'][1] = ramplength
                self.scn['subramps_per_choppos'][1] = choplength / ramplength
                self.scn['subramps_per_ramp'][1] = 1
                if self.scn['ch_scheme'] == '4POINT':
                    if self.scn['subramps_per_choppos'][1] % 2 == 0:
                        self.scn['subramps_per_choppos'][1] =  \
                            self.scn['subramps_per_choppos'][1] / 2
                    else:
                        errmsg += 'Even number of blue ramps required.\n '

            if self.scn['subramp_length'][1] > self.MAX_SUBRAMP_LENGTH:
                errmsg += 'Subramp length B too large\n '

            anz_frames_b = self.scn['gr_cycles'][1] *  \
                (self.scn['gr_steps_up'][1] + self.scn['gr_steps_down'][1]) *  \
                self.scn['ch_cycles'][1] * self.scn['choppos_per_cycle'] *  \
                self.scn['subramps_per_choppos'][1] *  \
                self.scn['subramp_length'][1]

            # check RED
            gr_end = self.scn['gr_start'][0] +  \
                self.scn['gr_steps_up'][0] * self.scn['gr_stepsize_up'][0]
            if gr_end < self.MIN_GR_POS or gr_end > self.MAX_GR_POS:
                errmsg += 'Red grating exceeds range on up\n '
            gr_end = gr_end -  \
                self.scn['gr_steps_down'][0] * self.scn['gr_stepsize_down'][0]
            if gr_end < self.MIN_GR_POS or gr_end > self.MAX_GR_POS:
                errmsg += 'Red grating exceeds range on down\n '

            ramplength = self.scn['ramplength'][0]
            choplength = self.scn['chop_length']

            if ramplength > choplength:
                if ramplength % choplength != 0:
                    errmsg += 'RAMPLENGTH_r not multiple of CHOPLENGTH\n '
                if self.scn['ch_scheme'] == '4POINT':
                    errmsg += 'RAMPLENGTH_r>CHOPLENGTH not allowed for 4POINT\n '
                self.scn['subramp_length'][0] = choplength
                self.scn['subramps_per_choppos'][0] = 1
                self.scn['subramps_per_ramp'][0] = ramplength / choplength
            else:
                if choplength % ramplength != 0:
                    errmsg += 'CHOPLENGTH not multiple of RAMPLENGTH_r\n '
                self.scn['subramp_length'][0] = ramplength
                self.scn['subramps_per_choppos'][0] = choplength / ramplength
                self.scn['subramps_per_ramp'][0] = 1
                if self.scn['ch_scheme'] == '4POINT':
                    if self.scn['subramps_per_choppos'][0] % 2 == 0:
                        self.scn['subramps_per_choppos'][0] =  \
                            self.scn['subramps_per_choppos'][0] / 2
                    else:
                        errmsg += 'Even number of blue ramps required.\n '

            if self.scn['subramp_length'][0] > self.MAX_SUBRAMP_LENGTH:
                errmsg += 'Subramp length R too large\n '

            anz_frames_r = self.scn['gr_cycles'][0] *  \
                (self.scn['gr_steps_up'][0] + self.scn['gr_steps_down'][0]) *  \
                self.scn['ch_cycles'][0] * self.scn['choppos_per_cycle'] *  \
                self.scn['subramps_per_choppos'][0] *  \
                self.scn['subramp_length'][0]

            if anz_frames_b != anz_frames_r:
                errmsg += 'Red and Blue parameters do not commensurate\n '
            self.scn['anz_frames'] = anz_frames_b

        if len(errmsg) == 0:
            return 'NoErrors', 'NoErrors'
        else:
            return False, '\n' + errmsg + '\n'

    def write(self, filename):
        """ write a *.scn file to folder """
        import time
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        file = open(filename, 'w')
        # seconds elapsed since 1 January 1970 UTC as time stamp below
        file.write('# Time stamp at last update: ' + str(time.time()) + '\n')
        file.write('#    ASTRONOMY\n')
        file.write('%s%s%s' % ("AOR_ID".ljust(12),  # adjust ljust param
            ('"' + self.scn["aorid"] + '"').ljust(20), '# from DCS\n'))
        file.write('%s%s%s' % ("FILEGP_R".ljust(12),
            ('"' + self.scn["filegp_r"] + '"').ljust(20),
            '# file group id RED for DPS use\n'))
        file.write('%s%s%s' % ("FILEGP_B".ljust(12),
            ('"' + self.scn["filegp_b"] + '"').ljust(20),
            '# file group id BLUE for DPS use\n'))
        file.write('%s%s%s' % ("OBSTYPE".ljust(12),
            ('"' + self.scn["obstype"] + '"').ljust(20),
            '# Observation type for DPS use\n'))
        # file.write('%s%s%s' % ("FOCUSOFF".ljust(12),
        #     str(self.scn["focusoff"]).ljust(20),
        #     '# Focus offset in microns\n'))
        file.write('%s%s%s' % ("SRCTYPE".ljust(12),
            ('"' + self.scn["srctype"] + '"').ljust(20),
            '# Source type for DPS use\n'))
        file.write('%s%s%s' % ("INSTMODE".ljust(12),
            ('"' + self.scn["instmode"] + '"').ljust(20),
            '# Instrument mode\n'))
        file.write('%s%s%s' % ("OBJ_NAME".ljust(12),
            ('"' + self.scn["target_name"] + '"').ljust(20),
            '# Name of astronomical object observed\n'))
        file.write('%s%s%s' % ("REDSHIFT".ljust(12),
            str(self.scn["redshift"]).ljust(20),
            '# redshift of the source (z)\n'))
        file.write('%s%s%s' % ("COORDSYS".ljust(12),
            ('"' + self.scn["obs_coord_sys"] + '"').ljust(20),
            '# Target coordinate system\n'))
        file.write('%s%s%s' % ("OBSLAM".ljust(12),  # adjust ljust param
            str(self.scn["target_lambda"]).ljust(20), '# in deg\n'))
        file.write('%s%s%s' % ("OBSBET".ljust(12),  # adjust ljust param
            str(self.scn["target_beta"]).ljust(20), '# in deg\n'))
        file.write('%s%s%s' % ("DET_ANGL".ljust(12),  # adjust ljust param
            str(self.scn["detangle"]).ljust(20),
            '# Detector y-axis EofN\n'))
        file.write('%s%s%s' % ("CRDSYSMP".ljust(12),  # adjust ljust param
            ('"' + self.scn["mapcoord_system"] + '"').ljust(20),
            '# Mapping coordinate system\n'))
        file.write('%s%s%s' % ("DLAM_MAP".ljust(12),
            str("%.1f" % self.scn['del_lam_map']).ljust(20), '# arcsec\n'))
        file.write('%s%s%s' % ("DBET_MAP".ljust(12),
            str("%.1f" % self.scn['del_bet_map']).ljust(20), '# arcsec\n'))
        file.write('%s%s%s' % ("CRDSYSOF".ljust(12),
            ('"' + self.scn["off_coord_sys"] + '"').ljust(20),
            '# Off position coordinate system\n'))
        file.write('%s%s%s' % ("DLAM_OFF".ljust(12),
            str("%.1f" % self.scn['offpos_lambda']).ljust(20), '# arcsec\n'))
        file.write('%s%s%s' % ("DBET_OFF".ljust(12),
            str("%.1f" % self.scn['offpos_beta']).ljust(20), '# arcsec\n'))
        file.write('%s%s%s' % ("PRIMARAY".ljust(12),
            ('"' + self.scn["primaryarray"] + '"').ljust(20),
            '# Primary array\n'))
        file.write('%s%s%s' % ("LOSF_UPD".ljust(12),
            str(self.scn['los_focus_update']).ljust(20),
            '# 0/1/2  block/allow/force updates\n'))
        file.write('%s%s%s' % ("NODPATT".ljust(12),
            ('"' + self.scn["nodpattern"] + '"').ljust(20),
            '# Nod pattern\n'))
        file.write('\n#    DICHROIC SETTING\n')
        file.write('%s%s%s' % ("DICHROIC".ljust(12),
            str(self.scn['dichroic']).ljust(20),
            '# Dichroic wavelength in um\n'))
        file.write('\n#    GRATING\n# Blue\n')
        file.write('%s%s%s' % ("G_ORD_B".ljust(12),
            str(self.scn['order']).ljust(15),
            '# Blue grating order to be used\n'))
        file.write('%s%s%s' % ("G_FLT_B".ljust(12),
            str(self.scn['blue_filter']).ljust(15),
            '# Filter number for Blue\n'))
        file.write('%s%s%s' % ("G_WAVE_B".ljust(12),
            str("%.3f" % self.scn['gr_lambda'][1]).ljust(15),
            '# Wavelength to be observed in um INFO ONLY\n'))
        file.write('%s%s%s' % ("RESTWAVB".ljust(12),
            str("%.3f" % self.scn['blue_micron']).ljust(15),
            '# Reference wavelength in um\n'))
        file.write('%s%s%s' % ("G_CYC_B".ljust(12),
            str(self.scn['gr_cycles'][1]).ljust(15),
            '# The number of grating cycles (up-down)\n'))
        file.write('%s%s%s' % ("G_STRT_B".ljust(12),
            str(self.scn['gr_start'][1]).ljust(15),
            '# absolute starting value in inductosyn units\n'))
        file.write('%s%s%s' % ("G_PSUP_B".ljust(12),
            str(self.scn['gr_steps_up'][1]).ljust(15),
            '# number of grating position up in one cycle\n'))
        file.write('%s%s%s' % ("G_SZUP_B".ljust(12),
            str(self.scn['gr_stepsize_up'][1]).ljust(15),
            '# step size on the way up; same unit as G_STRT\n'))
        file.write('%s%s%s' % ("G_PSDN_B".ljust(12),
            str(self.scn['gr_steps_down'][1]).ljust(15),
            '# number of grating position down in one cycle\n'))
        file.write('%s%s%s' % ("G_SZDN_B".ljust(12),
            str(self.scn['gr_stepsize_down'][1]).ljust(15),
            '# step size on the way down; same unit as G_STRT\n'))
        file.write('# Red\n')
        file.write('%s%s%s' % ("G_WAVE_R".ljust(12),
            str("%.3f" % self.scn['gr_lambda'][0]).ljust(15),
            '# Wavelength to be observed in um INFO ONLY\n'))
        file.write('%s%s%s' % ("RESTWAVR".ljust(12),
            str("%.3f" % self.scn['red_micron']).ljust(15),
            '# Reference wavelength in um\n'))
        file.write('%s%s%s' % ("G_CYC_R".ljust(12),
            str(self.scn['gr_cycles'][0]).ljust(15),
            '# The number of grating cycles (up-down)\n'))
        file.write('%s%s%s' % ("G_STRT_R".ljust(12),
            str(self.scn['gr_start'][0]).ljust(15),
            '# absolute starting value in inductosyn units\n'))
        file.write('%s%s%s' % ("G_PSUP_R".ljust(12),
            str(self.scn['gr_steps_up'][0]).ljust(15),
            '# number of grating position up in one cycle\n'))
        file.write('%s%s%s' % ("G_SZUP_R".ljust(12),
            str(self.scn['gr_stepsize_up'][0]).ljust(15),
            '# step size on the way up; same unit as G_STRT\n'))
        file.write('%s%s%s' % ("G_PSDN_R".ljust(12),
            str(self.scn['gr_steps_down'][0]).ljust(15),
            '# number of grating position down in one cycle\n'))
        file.write('%s%s%s' % ("G_SZDN_R".ljust(12),
            str(self.scn['gr_stepsize_down'][0]).ljust(15),
            '# step size on the way down; same unit as G_STRT\n'))
        file.write('\n#    RAMP\n')
        file.write('%s%s%s' % ("RAMPLN_B".ljust(12),
            str(self.scn['ramplength'][1]).ljust(15),
            '# number of readouts per blue ramp\n'))
        file.write('%s%s%s' % ("RAMPLN_R".ljust(12),
            str(self.scn['ramplength'][0]).ljust(15),
            '# number of readouts per red ramp\n'))
        file.write('\n#    CHOPPER\n')
        file.write('%s%s%s' % ("C_SCHEME".ljust(12),
            ('"' + self.scn["ch_scheme"] + '"').ljust(15),
            '# Chopper scheme; 2POINT or 4POINT\n'))
        file.write('%s%s%s' % ("C_CRDSYS".ljust(12),
            ('"' + self.scn["chopcoord_system"] + '"').ljust(15),
            '# Chopper coodinate system\n'))
        file.write('%s%s%s' % ("C_AMP".ljust(12),
            str(self.scn['chop_amp']).ljust(15),
            '# chop amplitude in arcsec\n'))
        file.write('%s%s%s' % ("C_TIP".ljust(12),
            str(self.scn['ch_tip']).ljust(15), '# fraction\n'))
        file.write('%s%s%s' % ("C_BEAM".ljust(12),
            str("%.1f" % self.scn['ch_beam']).ljust(15), '# nod phase\n'))
        file.write('%s%s%s' % ("C_POSANG".ljust(12),
            str(self.scn['chop_posang']).ljust(15), '# deg, S of E\n'))
        file.write('%s%s%s' % ("C_CYC_B".ljust(12),
            str(self.scn['ch_cycles'][1]).ljust(15),
            '# chopping cycles per grating position\n'))
        file.write('%s%s%s' % ("C_CYC_R".ljust(12),
            str(self.scn['ch_cycles'][0]).ljust(15),
            '# chopping cycles per grating position\n'))
        file.write('%s%s%s' % ("C_PHASE".ljust(12),
            str("%.1f" % float(self.scn['chop_manualphase'])).ljust(15),
            '# chopper signal phase shift relative to R/O in deg\n'))
        file.write('%s%s%s' % ("C_CHOPLN".ljust(12),
            str(self.scn['chop_length']).ljust(15),
            '# number of readouts per chop position\n'))
        file.write('\n#    CAPACITORS\n')
        file.write('%s%s%s' % ("CAP_B".ljust(12),
            str(self.scn['sel_cap'][1]).ljust(15),
            '# Integrating capacitors in pF\n'))
        file.write('%s%s%s' % ("CAP_R".ljust(12),
            str(self.scn['sel_cap'][0]).ljust(15),
            '# Integrating capacitors in pF\n'))
        file.write('\n#    CONVERTER\n# Blue\n')
        file.write('%s%s%s' % ("ZBIAS_B".ljust(12),
            str("%.3f" % self.scn['zero_bias'][1]).ljust(15),
                '# Voltage in mV\n'))
        file.write('%s%s%s' % ("BIASR_B".ljust(12),
            str("%.3f" % self.scn['biasr'][1]).ljust(15), '# Voltage in mV\n'))
        file.write('%s%s%s' % ("HEATER_B".ljust(12),
            str("%.3f" % self.scn['heater'][1]).ljust(15), '# Voltage in mV\n'))
        file.write('# Red\n')
        file.write('%s%s%s' % ("ZBIAS_R".ljust(12),
            str("%.3f" % self.scn['zero_bias'][0]).ljust(15),
                '# Voltage in mV\n'))
        file.write('%s%s%s' % ("BIASR_R".ljust(12),
            str("%.3f" % self.scn['biasr'][0]).ljust(15), '# Voltage in mV\n'))
        file.write('%s%s%s' % ("HEATER_R".ljust(12),
            str("%.3f" % self.scn['heater'][0]).ljust(15), '# Voltage in mV\n'))
        file.write('\n#    CALIBRATION SOURCE\n')
        file.write('%s%s%s' % ("CALSTMP".ljust(12),
            str(self.scn['cal_src_temp']).ljust(15), '# Kelvin\n'))
        file.write('\nHERE_COMETH_THE_END\n')
        file.close()
