import numpy as np
import pandas as pd
import os
import time

def inductosyn2wavelength(gratpos, dichroic, array, order, obsdate=''):
    '''
    Usage:
    l,lw = inductosyn2wavelength(gratpos=1496600, order=1, array='RED',
                   dichroic=105, obsdate='1909')
    '''
	# if obsdate not specified, assume today
    if obsdate == '':
        today = str(time.gmtime().tm_year)[2:]
        today += ('0' + str(time.gmtime().tm_mon))[-2:]
        obsdate = today

    if array == 'RED':
        channel = 'R'
    else:
        if order == '1':
            channel = 'B1'
        else:
            channel = 'B2'

    path0 = os.path.dirname(os.path.realpath(__file__))
    wvdf = pd.read_csv(os.path.join(path0, 'data', 'CalibrationResults.csv'), header=[0, 1])
    ndates = (len(wvdf.columns) - 2) // 4
    dates = np.zeros(ndates)
    for i in range(ndates):
        dates[i] = wvdf.columns[2 + i * 4][0]

    # Select correct date
    for i, date in enumerate(dates):
        if date < int(obsdate):
            pass
        else:
            break
    cols = range(2 + 4 * i , 2 + 4 * i + 4)
    w1 = wvdf[wvdf.columns[cols]].copy()
    if channel == 'R':
        if dichroic == 105:
            co = w1.columns[0]
        else:
            co = w1.columns[1]
    elif channel == 'B1':
        co = w1.columns[2]
    else:
        co = w1.columns[3]

    g0 = w1.iloc[0][co]
    NP = w1.iloc[1][co]
    a = w1.iloc[2][co]
    ISF = w1.iloc[3][co]
    gamma = w1.iloc[4][co]
    PS = w1.iloc[5][co]
    QOFF = w1.iloc[6][co]
    QS = w1.iloc[7][co]
    ISOFF = w1.iloc[8:][co].values

    ng = len(gratpos)
    pix = np.arange(16) + 1.
    result = np.zeros((ng, 25, 16))
    result_dwdp = np.zeros((ng, 25, 16))
    for ig, gp in enumerate(gratpos):
        for module in range(25):
            phi = 2. * np.pi * ISF * (gp + ISOFF[module]) / 2.0 ** 24
            sign = np.sign(pix - QOFF)
            delta = (pix - 8.5) * PS + sign * (pix - QOFF) ** 2 * QS
            slitPos = 25 - 6 * (module // 5) + module % 5
            g = g0 * np.cos(np.arctan2(slitPos - NP, a))  # Careful with arctan
            lambd = 1000. * (g / order) * (np.sin(phi + gamma + delta) + np.sin(phi - gamma))
            dwdp = 1000. * (g / order) * (PS + 2. * sign * QS * (pix - QOFF)) * np.cos(phi + gamma + delta)
            result[ig, module, :] = lambd
            result_dwdp[ig, module, :] = dwdp

    return result, result_dwdp

def wavelength2inductosyn(wave, dichroic, array, order, obsdate=''):
    """
    Inverse of previous function. Call the previous function to compute the curve and
    uses interpolation to invert the function.
    """
    
    grating = np.arange(0,3000,10)*1000.
    w, dw = inductosyn2wavelength(grating, dichroic, array, order, obsdate)
    
    return np.interp(wave, np.mean(w, axis=(1,2)), grating)
    
    