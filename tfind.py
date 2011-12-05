"""
Transit finder: A new approach to finding low signal to noise transits.
"""

from scipy import ndimage as nd
import numpy as np


def LDMF(f,dK):
    """
    Locally-detrended Matched Filter.

    Finds box-shaped signals irrespective of a local continuum slope.


    Parameters
    ----------
    f : flux time series
    dK: Depth kernel.


    Returns
    -------
    dM : Mean depth of transit.

    """
    dM = nd.convolve1d(f,dK,mode='wrap')
    
    return dM


def GenK(twd,fcwd=1):
    """
    Generate Kernels.  
    
    Parameters
    ----------
    twid  : length of the transit (in units of cadence length)
    fcwid : Each side of the continuum is fcwd * twid (default is 1)

    Returns
    -------
    bK : Before transit kernel.
    tK : Trasit kernel.
    aK : After transit kernel.
    dK : Depth kernel.

    Notes
    -----
    Recall that conv(f,g) will flip g.

    """
    cwd = twd * fcwd
    kSize = 2*cwd + twd  # Size of the kernel
    kTemp = np.zeros(kSize) # Template kernal of appropriate length.

    bK = kTemp.copy()
    bK[-cwd:] = np.ones(1) / cwd # Before transit kernel


    boxK = kTemp.copy()
    boxK[cwd:-cwd] = np.ones(1) # Box shaped kernel

    tK = boxK.copy()
    tK[cwd:-cwd] /= twd # transit kernel

    aK = kTemp.copy()
    aK[:cwd] = np.ones(1) / cwd # After transit kernel

    dK = kTemp.copy() 
    dK = 0.5*(bK+aK) - tK # Depth kernel

    return bK,boxK,tK,aK,dK


def dThresh(dM,dMi=50,dMa=1000):
    """
    Depth threshold.

    Applies a cut to the possible transits based on their depth.

    Parameters
    ----------
    dM  : Mean depth of transit.
    dMa : The maximum depth (ppm).
    dMi : The minimum depth (ppm).

    Returns
    -------

    tCand : Boolean array with showing which cadances are cadidate
            mid-transit.

    """
    
    dMi *= 1e-6
    dMa *= 1e-6

    tCand = (dM > dMi) & (dM < dMa)

    return tCand

def pCheck(tCand,P0,nTMi=3):
    """
    Periodicity check.

    Throw out transit cadidates that are not consistent with a single
    period.

    Parameters
    ----------
    tCand : Boolean array with showing which cadances are cadidate
            mid-transit.
    P0    : Trial period (units of cadence)
    nTMi  : Require that signals repeat a certain number of times.  

    Returns
    -------
    phCand : List of phases consistent with a transit.

    """

    tCand = XWrap(tCand,P0)
    nT = tCand.sum(axis=0)
    boolT = (nT >= nTMi) # Tag values have enough periodic candidates.

    ph = np.arange(P0,dtype=np.float) / P0
    phCand = ph[ np.where(boolT)[0] ] 

    return phCand

def XWrap(x,ifold):
    """
    Extend and wrap array.
    
    Fold array every y indecies.  There will typically be a hanging
    part of the array.  This is padded out.

    Parameters
    ----------

    x     : input
    ifold : Wrap array after ifold indecies.

    Return
    ------

    xwrap : Wrapped array.

    """

    assert type(ifold) is int, "ifold must be an int."
    ncad = x.size # Number of cadences
    nrow = int(np.floor(ncad/ifold) + 1)
    nExtend = nrow * ifold - ncad # Pad out remainder of array with 0s.
    
    x = np.append( x , np.zeros(nExtend) )
    xwrap = x.reshape( nrow,-1 )

    return xwrap

def lseg(x,P,ph,wid):
    """
    List of segments.

    Fold input according to P.  Return segments of the array at a
    specific phase of a specific width.

    Parameters
    ----------
    x   : Array to be extracted
    P   : Fold array every P indecies (cad)
    ph  : Return every points at ph. (cad)
    wid : Width of each returned segment (cad)

    """
    
    sl = 0 # low end of the slice.
    sh = 0 # Upper end of the slice.
    iseg = 0
    xlseg = []

    n = len(x)
    while sl < n:
        sl = P * iseg + ph - wid/2
        sh = P * iseg + ph + wid/2
        xlseg.append(x[sl:sh])
        iseg += 1

    return xlseg




def boxBR(fsig,dTrans,sig,boxK):
    """
    Box Bayes Ratio.

    Compute the Bayes ratio of Prob( transit ) / Prob( flat ).


    Parameters
    ----------
    fsig   : Detrended flux time series.
    dTrans : Depth of transit.
    boxK   : Model constructed from the same kernel.
    sig    : Point by point sigma.

    Returns
    -------
    BR : log of Bayes Ratio.

    """

    # Compute Chi^2 for the transit model
    tMod = -1.*depth*boxK
    tChi2 = Chi2(fsig,tMod,sig)

    # Compute Chi^2 for the null model
    nlMod = 0.*boxK
    nlChi2 = Chi2(fsig,nlMod,sig)

    BR = tChi2 - nlChi2 

    return BR


def Chi2(data,model,sig):
    """
    Chi^2 with constant sigma.
    """
    
    r = data - model
    nr = r/sig
    chi2 = (nr**2).sum()

    return chi2

def taylorDT(f,bM,aM,cad,twd,cwd):
    """
    Taylor series detrending.
    
    Perform a local detrending at a particular cadence.

    Arguments
    ---------
    f    : Array of flux values.  For the detrending to be sucessful, it
           should be relatively small
    bM   : The mean of the continuum before the transit.
    tM   : The mean of the continuum after the transit.
    cad  : Array of cadence identifers.
    cwd  : Width of the continuum region.
    twd  : Width of the transit region.    

    Returns
    -------
    trend : Fluxes corresponding to the detrended light curve.

    """
    n = cad.size
    assert f.size == cad.size, "Flux and cadence must be of equal length"

    DfDcad = (aM-bM)/(cwd+twd) # This is the slope flux on cadence.

    # Cadance of mid-transit (can be fractional).
    cad0 = cad.min() + cad.ptp()/2 
    
    f0     = 0.5 * (aM + bM)    # The mean value of f mid transit.
    trend  = DfDcad*( cad - cad0 ) + f0

    return trend


