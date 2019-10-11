import os
import io
import math
import json
import numpy as np
from PyQt5.QtWidgets import QFileDialog

def replaceBadChar(string):
    """ replace some reserved characters with '_'
    see http://en.wikipedia.org/wiki/Filename for a list
    """
    string = string.replace('/', '_')
    string = string.replace('\\', '_')
    string = string.replace(':', '_')
    string = string.replace('*', '_')
    #string = string.replace('|', '_')
    #string = string.replace('<', '_')
    #string = string.replace('>', '_')
    string = string.replace(' ', '_')
    return string

def velocity2z(v):
    '''
    return redshift Z given velocity v in km/s
    '''
    c = 299792.458 # km/s
    return v/c
    
def radec(xra, xdec):
    '''
    radec.pro (IDL astrolib) translated to Python
    inputs: xra = RA in decimal degrees, xdec = DEC in decimal degrees
    outputs: [ihr, imin, xsec, ideg, imn, xsc] (RA-DEC sexigesimal)
    '''
    # convert RA
    ihr = int(xra / 15.)
    xmin = abs(xra * 4.0 - ihr * 60.0)
    imin = int(xmin)
    xsec = (xmin - imin) * 60.0
    # convert DEC
    ideg = int(xdec)
    xmn = abs(xdec - ideg) * 60.
    imn = int(xmn)
    xsc = (xmn - imn) * 60.

    return [ihr, imin, xsec, ideg, imn, xsc]


def readAOR(vector):
    '''
    extracts values from <Request> for tagnames defined in definitions.py
    input: xml element containing one AOR only (no Proposal info, target list)
    output: dictionary needed for FIFI-LS ObsMaker input file *.sct.  All
            values to a keyword are lists of strings.
    '''
    # to do later - add input parameter outdir, where the output files
    # are to be written

    # Reading tagnames
    path = os.path.dirname(os.path.realpath(__file__))
    file = os.path.join(path, "data", "keywords.json")
    with open(file) as f:
        config = json.load(f)
    tagnames = config['tagnames']
    aor = dict.fromkeys(tagnames)
    
    #print aor
    for tag in tagnames:
        nodes = vector.findall('.//' + tag)   # returns a list of objects
        # if the node returns values (i.e. the tag exists in the input XML):
        if nodes != []:
            if len(nodes) == 1:
                aor[tag] = [nodes[0].text]
            else:
                data = list()
                for node in nodes:
                    data.append(node.text)
                aor[tag] = data
        # if the tag does not exist, set the value to a list with an empty
        # element
        else: aor[tag] = ['']
    return aor

def writeFAOR(aor, PropID, outdir):
    '''
    writes files for input into FIFI-LS ObservationMaker
    input: output of FI_read_aor
    output: .sct and _map.txt files in outdir
    '''
    # Reading keywords and tagnames
    path = os.path.dirname(os.path.realpath(__file__))
    file = os.path.join(path, "data", "keywords.json")
    with open(file) as f:
        config = json.load(f)
    keywords = config['keywords']
    tagnames = config['tagnames']
    values=dict.fromkeys(keywords)
    
    # set default values
    values['MAPCOORD_SYSTEM'] = config['MAPCOORD_SYSTEM_default']  # 'J2000'
    values['PATTERN'] = config['PATTERN_default']  # 'File'
    values['DITHMAP_STEPSIZE'] = config['DITHMAP_STEPSIZE_default']  # 'n/a'
    values['DITHMAP_LAMBDA'] = config['DITHMAP_LAMBDA_default']  # 0.
    values['DITHMAP_BETA'] = config['DITHMAP_BETA_default']  # 0.

    values['CHOPPHASE'] = config['CHOPPHASE_default']  # 'Default'
    values['CHOP_MANUALPHASE'] = config['CHOP_MANUALPHASE_default']  #'n/a'
    values['CHOP_LENGTH'] = config['CHOP_LENGTH_default']  # 64

    values['OBSTYPE'] = config['OBSTYPE_default']  # 'OBJECT'
    values['NODPATTERN'] = config['NODPATTERN_default']  # 'ABBA'
    values['REWIND'] = config['REWIND_default']  # 'Auto'
    values['OFFPOS_REDUC'] = config['OFFPOS_REDUC_default']  # 1.

    values['SETPOINT'] = config['SETPOINT_default']  # 'n/a'

    values['BLUE_GRTCYC'] = config['BLUE_GRTCYC_default']  # 1
    values['BLUE_SIZEDOWN'] = config['BLUE_SIZEDOWN_default']  # 0.
    values['BLUE_POSDOWN'] = config['BLUE_POSDOWN_default']  # 0
    values['RED_GRTCYC'] = config['RED_GRTCYC_default']  # 1
    values['RED_SIZEDOWN'] = config['RED_SIZEDOWN_default']  # 0.
    values['RED_POSDOWN'] = config['RED_POSDOWN_default'] # 0

    values['BLUE_RAMPLEN'] = config['BLUE_RAMPLEN_default']  # 32
    values['RED_RAMPLEN'] = config['RED_RAMPLEN_default']  # 32

    values['BLUE_ZBIAS'] = config['BLUE_ZBIAS_default']  # 75
    values['BLUE_BIASR'] = config['BLUE_BIASR_default']  # 0
    values['RED_ZBIAS'] = config['RED_ZBIAS_default']  # 60
    values['RED_BIASR'] = config['RED_BIASR_default']  # 0
    values['BLUE_CAPACITOR'] = config['BLUE_CAPACITOR_default']  # 1330
    values['RED_CAPACITOR'] = config['RED_CAPACITOR_default']  # 1330

    errmsg = ''
    # for Moving targets, set lat and lon to 0, equinox to J2000
    if aor['lat'][0] == '':
        aor['lat'][0] = '0.0'
        aor['lon'][0] = '0.0'
        aor['equinoxDesc'][0] = 'J2000'
        # other parameters not set in SSpot are:
        # aor['latPm'][0]
        # aor['lonPm'][0]
        # aor['ecliptic'][0]  # should be set to 'false'
        # aor['equatorial'][0]  # should be set to 'true'
        # aor['galactic'][0]  # should be set to 'false'

    # pprint(aor)
    # if there are None values in aor, exit immediately
    empty_values = [tag for tag in tagnames if aor[tag] is None]
    if len(empty_values) > 0:
        tag_list = ''
        for item in empty_values:
            tag_list += item + ' '

        errmsg += tag_list + 'value was not set in the .aor file.\n'
        errmsg += 'Please validate ' + aor['aorID'][0] + ' in SSpot.\n'
        return errmsg

    values['TARGET_NAME'] = (aor['name'])[0].replace(" ", "_")
    values['AORID'] = (aor['aorID'])[0].replace(" ", "_")
    values['OBSID'] = values['TARGET_NAME'].replace('@', '') + '_' + \
        replaceBadChar(aor['title'][0])
    values['SRCTYPE'] = (aor['SourceType'])[0].upper()
    values['INSTMODE'] = (aor['ObsPlanMode'])[0]

    if aor['equinoxDesc'][0] != 'J2000':
        # print 'Not J2000 Coordinates'
        errmsg += 'Not J2000 Coordinates\n'
    ra = float(aor['lon'][0])   # in decimal degrees
    dec = float(aor['lat'][0])  # in decimal degrees
    # convert ra, dec in decimal degrees to hh mm ss, dd mm ss
    ihr, imin, xsec, ideg, imn, xsc = radec(ra, dec)
    sra =  str(ihr) + ' ' + str(imin) + ' ' + str(round(xsec, 2))
    sdec = '+' * (ideg >= 0) + str(ideg) + ' ' + str(imn) + ' ' +  \
        str(round(xsc, 1))
    values['TARGET_LAMBDA'] = sra
    values['TARGET_BETA'] = sdec

    detang = ((float((aor['MapRotationAngle'])[0]) + 180 + 360) % 360) - 180
    values['DETANGLE'] = detang    # in degrees
    # math.radians(x) - convert angle x from degrees to radians
    # math.degrees(x) - convert angle x from radians to degrees
    # rotation matrix - rotate counter-clockwise
    detang *= np.pi/180.0
    cosa = np.cos(detang)
    sina = np.sin(detang)
    r = np.array([[cosa, -sina], [sina, cosa]])

    if type(aor['deltaRaV']) == list:
        aor['deltaRaV'] = [float(item) for item in aor['deltaRaV']]
        aor['deltaDecW'] = [float(item) for item in aor['deltaDecW']]
    else:
        aor['deltaRaV'] = [float(item) for item in [aor['deltaRaV']]]
        aor['deltaDecW'] = [float(item) for item in [aor['deltaDecW']]]
    if len(aor['deltaRaV']) == 1:
        mapoffsets = np.array([aor['deltaRaV']] + [aor['deltaDecW']])
    else:
        mapoffsets = np.array([aor['deltaRaV'], aor['deltaDecW']])
    #print mapoffsets

    rot_mapoffsets = np.transpose(np.dot(np.transpose(r), mapoffsets))
    if len(aor['deltaRaV']) == 1:
        values['DITHMAP_NUMPOINTS'] = 1
    else:
        values['DITHMAP_NUMPOINTS'] = len(rot_mapoffsets)
    #print rot_mapoffsets, len(rot_mapoffsets)

    values['CHOPCOORD_SYSTEM'] = (aor['ChopAngleCoordinate'])[0]
    values['CHOP_AMP'] = float((aor['ChopThrow'])[0])/2.
    values['CHOP_POSANG'] = (float((aor['ChopAngle'])[0]) + 270 + 360) % 360
        # CCW from N in SSpot, S of E in ObsMaker

    if (values['CHOPCOORD_SYSTEM'] == 'HORZION') and (aor['ChopAngle'] != 0):
        # print "NON-ZERO CHOP ANGLE WITH HORIZON"
        errmsg += "NON-ZERO CHOP ANGLE WITH HORIZON\n"
    if values['CHOPCOORD_SYSTEM'] == 'HORIZON':
        values['CHOP_POSANG'] = 0

    if aor['ChopType'][0] == 'Sym':
        values['TRACKING'] = 'On'
        #values['OBSMODE'] = 'Beam switching'
        values['OBSMODE'] = 'Symmetric'
        values['OFFPOS'] = 'Matched'
        values['OFFPOS_LAMBDA'] = '0.0'
        values['OFFPOS_BETA'] = '0.0'
    elif aor['ChopType'][0] == 'Asym':
        values['TRACKING'] = 'Off'
        #values['OBSMODE'] = 'Asym chop + off'
        values['OBSMODE'] = 'Asymmetric'
        if aor['ReferenceType'][0] == 'RA_Dec':
            values['OFFPOS_LAMBDA'] = aor['RefRA'][0]
            values['OFFPOS_BETA']   = aor['RefDec'][0]
            values['OFFPOS'] = 'Absolute'
            if aor['MapRefPos'][0] == 'true':
                errmsg += \
                    """Absolute reference and mapping reference not supported.
    MapRefPos has been changed to 'false'\n"""
            # elif aor['MapRefPos'][0] == 'false':
            #     values['OFFPOS'] = 'Absolute'
        elif aor['ReferenceType'][0] == 'Offset':
            values['OFFPOS_LAMBDA'] = aor['RAOffset'][0]
            values['OFFPOS_BETA']   = aor['DecOffset'][0]
            if aor['MapRefPos'][0] == 'true':
                values['OFFPOS'] = 'Relative to active pos'
            elif aor['MapRefPos'][0] == 'false':
                values['OFFPOS'] = 'Relative to target'

    if aor['PrimeArray'][0] == 'Blue':
        values['PRIMARYARRAY'] = 'BLUE'
    elif aor['PrimeArray'][0] == 'Red':
        values['PRIMARYARRAY'] = 'RED'

    values['DICHROIC'] = ((aor['Dichroic'])[0])[0:3]  # 105 or 130

    #### updated for Cycle 4
    #  blue rest wavelength and species
    blue_lam = float((aor['WavelengthBlue'])[0])  # Wavelength in Cycle 3
    values['BLUE_LINE'] = 'Custom'
    values['BLUE_MICRON'] = blue_lam  # user-entered wavelength
    # red rest wavelength and species
    red_lam = float((aor['WavelengthRed'])[0])   # Wavelength2 in Cycle 3
    values['RED_LINE'] = 'Custom'
    values['RED_MICRON'] = red_lam  # user-entered wavelength

    # Cycle 3: offset in km/s
    # values['BLUE_OFFSET'] = diff[line_idx] / \
    #    obs_ref_blue_lambdas[idx_blue[line_idx]] * speed_of_light
    # Cycle 4: offset in either kmPerSec or z
    # ObsMaker line offset must be in kms or um
    # convert z to um: offset = obs_um - rest_um = z * um_rest
    if aor['RedshiftUnit'] == 'z':
        values['BLUE_OFFSET'] = float((aor['Redshift'])[0]) * blue_lam
        values['BLUE_OFFSET_TYPE'] = 'um'
        values['RED_OFFSET'] = float((aor['Redshift'])[0]) * red_lam
        values['RED_OFFSET_TYPE'] = 'um'
        values['REDSHIFT'] = float((aor['Redshift'])[0])
    else:  # other option is 'kmPerSec' (Cycle4), '' (Cycle5; kmPerSec implied)
        values['BLUE_OFFSET'] = float((aor['Redshift'])[0])
        values['BLUE_OFFSET_TYPE'] = 'kms'
        values['RED_OFFSET'] = float((aor['Redshift'])[0])
        values['RED_OFFSET_TYPE'] = 'kms'
        values['REDSHIFT'] = velocity2z(float((aor['Redshift'])[0]))

    # File Group IDs for DPS
    # Target_wavelength - SSpot allows 3 significant digits
    dot = str(blue_lam).find('.')
    values['FILEGP_B'] = values['TARGET_NAME'].replace('@', '') + '_' + \
        str(blue_lam)[: dot + 4]
    dot = str(red_lam).find('.')
    values['FILEGP_R'] = values['TARGET_NAME'].replace('@', '') + '_' +  \
        str(red_lam)[: dot + 4]

    #Order filter
    if blue_lam < 71:   # Wavelength in Cycle 3
        values['ORDER'] = '2'
        #blue_um_per_pix = poly(blue_lam, config['blue2_coef'])
        blue_um_per_pix = np.polyval(np.flip(config['blue2_coef']), blue_lam)
    else:
        values['ORDER'] = '1'
        blue_um_per_pix = np.polyval(np.flip(config['blue1_coef']), blue_lam)
    red_um_per_pix = np.polyval(np.flip(config['red_coef']), red_lam)
    values['BLUE_FILTER'] = values['ORDER']

    nodcycles = int((aor['Repeat'])[0])
    values['NODCYCLES'] = nodcycles

    # Bandwidths  - updated for Cycle 4
    # if NodType or ObsPlanMode is SPECTRAL_SCAN, BandwidthBlue/Red is in
    # micron; other Modes are in kmPerSec.
    if aor['NodType'][0] == 'SPECTRAL_SCAN':
        bandwidthBlue_pix = max([(float((aor['BandwidthBlue'])[0]) /  \
            blue_um_per_pix), 6.])
        bandwidthRed_pix = max([(float((aor['BandwidthRed'])[0]) /   \
            red_um_per_pix), 6.])
    else:
        bandwidthBlue_pix = max([float((aor['BandwidthBlue'])[0]) *  \
            blue_lam / (config['speed_of_light']) / blue_um_per_pix, 6.])
        bandwidthRed_pix = max([float((aor['BandwidthRed'])[0]) *  \
            red_lam / (config['speed_of_light']) / red_um_per_pix, 6.])

    blue_pix_per_nod = bandwidthBlue_pix / nodcycles
    red_pix_per_nod = bandwidthRed_pix / nodcycles

    values['BLUE_POSUP'] = int(math.ceil(blue_pix_per_nod / config['max_stepsize_inPix']) * nodcycles)
    values['BLUE_SIZEUP'] = 0.5
    # values['BLUE_SIZEUP'] = bandwidthBlue_pix / values['BLUE_POSUP']
    values['RED_POSUP'] = int(math.ceil(red_pix_per_nod / config['max_stepsize_inPix']) * nodcycles)
    values['RED_SIZEUP'] = 0.5
    # values['RED_SIZEUP'] = bandwidthRed_pix / values['RED_POSUP']

    # Cycle 5: SCANDIST is always Up, SPLITS is always 1,
    # RED_LAMBDA and BLUE_LAMBDA are always Inward dither
    values['SCANDIST'] = 'Up'
    values['RED_LAMBDA'] = 'Inward dither'
    values['BLUE_LAMBDA'] = 'Inward dither'
    values['SPLITS'] = 1
    # if max([blue_pix_per_nod, red_pix_per_nod]) <= max_grmov_per_scn_inPix:
    #     values['SCANDIST'] = 'Up'
    #     values['SPLITS'] = 1
    #     if nodcycles == 1:
    #         values['BLUE_LAMBDA'] = 'Centre'
    #         values['RED_LAMBDA'] = 'Centre'
    #     else:
    #         values['BLUE_LAMBDA'] = 'Inward dither'
    #         values['RED_LAMBDA'] = 'Inward dither'
    # else:
    #     values['SCANDIST'] = 'Split'
    #     values['BLUE_LAMBDA'] = 'Centre'
    #     values['RED_LAMBDA'] = 'Centre'
    #     values['SPLITS'] = math.ceil(min(
    #         [blue_pix_per_nod, red_pix_per_nod]) / max_grmov_per_scn_inPix)

    chopCycles_per_nod = 2. * float((aor['TimePerPoint'])[0])
    values['BLUE_CHOPCYC'] = int(math.ceil(chopCycles_per_nod * nodcycles / \
                              (values['BLUE_POSUP'] * values['SPLITS'])))
    values['RED_CHOPCYC'] = int(math.ceil(chopCycles_per_nod * nodcycles / \
                             (values['RED_POSUP'] * values['SPLITS'])))


    #write output files: .sct and _map.txt files
    #Create file name
    fn = os.path.join(outdir, values['TARGET_NAME'].replace('@', '') + '_' +  \
        replaceBadChar(aor['title'][0]) + '.sct')
    #test existence of file
    i = 0
    while os.path.exists(fn):
        i += 1
        fn = os.path.join(outdir, values['TARGET_NAME'].replace('@', '') + \
            '_' + replaceBadChar(aor['title'][0]) + '_%03d.sct' % i)
    if i == 0:
        values['MAPLISTPATH'] = values['TARGET_NAME'].replace('@', '') + \
            '_' + replaceBadChar(aor['title'][0]) + '_map.txt'
    else:
        values['MAPLISTPATH'] = values['TARGET_NAME'].replace('@', '') + \
            '_' + replaceBadChar(aor['title'][0]) + '_%03d_map.txt' % i
    #pprint(values)
    #write contents
    outfile = open(fn, 'w')
    for item in keywords:
        outfile.write("%s#%s\n" %
        (str(values[item]).ljust(max([25, len(str(values[item])) + 2])), item))
    outfile.close()

    #write map file
    outfile = open(os.path.join(outdir, values['MAPLISTPATH'].replace(
        '@', '')), 'w')
    outfile.write("%s%s" % (str(values['TARGET_LAMBDA']).rjust(12),
        str(values['TARGET_BETA']).rjust(12) + "\n"))

    if len(rot_mapoffsets[0]) > 1:
        for line in rot_mapoffsets:
            rot = str(round(line[0], 4)).rjust(12) + \
                  str(round(line[1], 4)).rjust(
                    max([12, len(str(round(line[1], 4))) + 2]))
            outfile.write(rot + "\n")
    else:
        # rot = str(round(rot_mapoffsets[0][0], 4)).rjust(12) +  \
        #       str(round(rot_mapoffsets[1][0], 4)).rjust(12)
        rot = str(rot_mapoffsets[0][0]).rjust(12) + \
              str(rot_mapoffsets[1][0]).rjust(
                max([12, len(str(rot_mapoffsets[1][0])) + 2]))
        outfile.write(rot)

    outfile.close()
    # print "%s and %s created." % (fn, values['MAPLISTPATH'])
    errmsg += fn + ' and ' + values['MAPLISTPATH'] + ' created.\n'

    return errmsg

def readSct(filename):
    """ 
    Read a *.sct file and return a dictionary.
    """
    print('Loading ', filename)
    try:
        parameters = {}
        with open(filename) as f:
            for line in f:
                line = line.rstrip('\n') 
                (val, key) = line.split('#')
                parameters[key.strip()] = val.strip()
        return parameters
    except:
        print("This is not a *.sct file")
        return None
    
def writeSct(sctPars):
    """
    Write a *.sct file from a dictionary.
    """
    fd = QFileDialog()
    fd.setLabelText(QFileDialog.Accept, "Export as")
    fd.setNameFilters(["Scan description (*.sct)", "All Files (*)"])
    fd.setOptions(QFileDialog.DontUseNativeDialog)
    fd.setViewMode(QFileDialog.List)
    if (fd.exec()):
        filenames= fd.selectedFiles()
        filename = filenames[0]
        if filename[-4:] != '.sct':
            filename += '.sct'              
        print("Exporting scan description to file: ", filename)
        with io.open(filename, mode='w') as f:
            for key in sctPars.keys():
                f.write("{0:25s}#{1:s}\n".format(sctPars[key], key.upper()))
    print('File '+filename+' exported.')
    
    
def readMap(filename=None):
    """
    Import alternate map file.
    """
    if filename is None:
        fd = QFileDialog()
        fd.setLabelText(QFileDialog.Accept, "Import")
        fd.setNameFilters(["Fits Files (*.txt)", "All Files (*)"])
        fd.setOptions(QFileDialog.DontUseNativeDialog)
        fd.setViewMode(QFileDialog.List)
        fd.setFileMode(QFileDialog.ExistingFile)
        if (fd.exec()):
            fileNames= fd.selectedFiles()
            filename = fileNames[0]
    else:
        pass
    print('Reading map ', filename)
    with open(filename) as file:
        for i, l in enumerate(file):
            continue
    numlines = i + 1
    if numlines < 2:
        print('Map file is empty.')
        return
    # read the first line - target coords in HH:MM:SS.SS, DD:MM:SS.SS
    file = open(filename)
    line = file.readline()
    if len(line.split()) != 6:
        print('File is not a map file.')
        return
    file.close()

    mapListPath = filename
    numMapPoints = numlines - 1 
    return numMapPoints, mapListPath    