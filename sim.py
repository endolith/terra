"""
Simulation
----------

This module implements the transit search pipeline.

Injection and recovery pipeline

"""
import os

from matplotlib import mlab
from numpy import *
import pandas

import prepro
import tfind
import tval
import keptoy
import config

def injRec(pardict):
    """
    Inject and recover

    Parameters:
    pardict : Simulation parameters. Must contain the following keys.
              - lcfile
              - gridfile
              - climb, p, tau, b
              - P, t0
              - id. returned with output.  used in merge at the end
    """
    name = "".join(random.random_integers(0,9,size=10).astype(str))

    lc0 = prepro.Lightcurve(pardict['lcfile'],mode='r')
    lc  = prepro.Lightcurve(name+'.h5',driver='core',backing_store=False)
    lc.copy(lc0['raw'],'raw')

    raw = lc['raw']

    qL = [i[0] for i in raw.items()]
    for q in qL:
        r  = raw[q][:] # pull data out of h5py file
        ft = keptoy.synMA(pardict,r['t'])
        r['f'] +=ft
        r = mlab.rec_append_fields(r,'finj',ft)

        del raw[q]
        raw[q] = r

    lc.mask()
    lc.dt()
    lc.attrs['svd_folder'] = os.environ['SCRATCH']+'/eb10k/svd/'
    lc.cal()
    lc.sQ()

    grid0 = tfind.Grid(pardict['gridfile'],mode='r')
    res0 = grid0['RES'][:]

    grid  = tfind.Grid(name+'.grid.h5',driver='core',backing_store=False)
    grid['mqcal'] = lc['mqcal'][:]

    deltaPcad = 10

    grid.P1=int(pardict['P']/config.lc - deltaPcad)
    grid.P2=int(pardict['P']/config.lc + deltaPcad)

    grid.P1=max(grid.P1 , res0['Pcad'][0] )
    grid.P2=min(grid.P2 , res0['Pcad'][-1] )

    grid.grid()
    grid.itOutRej()

    res  = grid['RES'][:]

    start = where(res0['Pcad']==res['Pcad'][0])[0]
    stop  = where(res0['Pcad']==res['Pcad'][-1])[0]
    if len(start) > 1:
        start = start[1]
    if len(stop) > 1:
        stop = stop[0]

    res0[start:stop+1] = res
    del grid['RES']
    grid['RES'] = res0

    mqcal =  grid['mqcal']
    t =  mqcal['t']

    fm   = ma.masked_array(mqcal['fcal'],mqcal['fmask'])
    finj = ma.masked_array(mqcal['finj'],mqcal['fmask'])

    p = tval.Peak(name+'.pk.h5',driver='core',backing_store=False)
    p['RES'] = grid['RES'][:]
    p['mqcal'] = grid['mqcal'][:]

    p.attrs['climb'] = array( [ pardict['a%i' % i] for i in range(1,5) ]  ) 

    p.findPeak()
    p.conv()
    p.checkHarm()
    p.at_phaseFold()
    p.at_fit()
    p.at_med_filt()
    p.at_s2ncut()
    p.at_SES()
    p.at_rSNR()
    p.at_autocorr()
    out = p.flatten(p.noDBRE)
    out['id'] = pardict['id']
    return out

