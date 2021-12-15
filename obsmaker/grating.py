import numpy as np
import pandas as pd
import os
import time


def inductosyn2wavelength(gratpos, dichroic, array, order, obsdate=''):
    """
    Usage:
    l,lw = inductosyn2wavelength(gratpos=1496600, order=1, array='RED',
                   dichroic=105, obsdate='1909')
    """
    # if obsdate not specified, assume today
    if obsdate == '':
        year =  str(time.gmtime().tm_year)
        month = '{0:02d}'.format(time.gmtime().tm_mon)
        day = '{0:02d}'.format(time.gmtime().tm_mday)
        obsdate = year+month+day
    
    # Case of array/dichroic/order
    if array == 'RED':
        if dichroic == '105':
            channel = 'R105'
        else:
            channel = 'R130'
    else:
        if order == '1':
            channel = 'B1'
        else:
            channel = 'B2'

    # Read file with wavelength calibration coefficients
    path0 = os.path.dirname(os.path.realpath(__file__))
    header_list = ["Date", "ch", "g0","NP","a","PS","QOFF","QS",
               "I1","I2","I3","I4","I5","I6","I7","I8","I9","I10",
               "I11","I12","I13","I14","I15","I16","I17","I18","I19","I20",
               "I21","I22","I23","I24","I25"]

    wvdf = pd.read_csv(os.path.join(path0, 'data' ,'FIFI_LS_WaveCal_Coeffs.txt'), 
                   comment='#', delimiter='\s+', names=header_list)
    
    # Fixed variables
    ISF = 1
    if array == 'RED':
        gamma = 0.0167200
    else:
        gamma = 0.0089008
        
    print('obsdate ', obsdate)
    

    # Select calibration date
    dates = np.unique(wvdf['Date'])
    print('dates ', dates)
    for i, date in enumerate(dates):
        if date < int(obsdate):
            pass
        else:
            break
        
    idx = dates < int(obsdate)
    print('idx ', idx)
    caldate = np.max(dates[idx])   
        
    # Select line in calibration file with caldate and channel
    idx = (wvdf["Date"] == caldate) & (wvdf["ch"] == channel)
    wcal = wvdf.loc[idx]

    g0 = wcal['g0'].values[0]
    NP = wcal['NP'].values[0]
    a = wcal['a'].values[0]
    PS = wcal['PS'].values[0]
    QOFF = wcal['QOFF'].values[0]
    QS = wcal['QS'].values[0]
    ISOFF = wcal.iloc[0][8:].values

    order = int(order)
    try:
        ng = len(gratpos)
    except:
        ng = 1
        gratpos = [gratpos]
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

    grating = np.arange(0, 3000, 10) * 1000.
    w, dw = inductosyn2wavelength(grating, dichroic, array, order, obsdate)

    return np.interp(wave, np.mean(w, axis=(1, 2)), grating)
