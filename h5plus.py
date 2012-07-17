import sim
import h5py
import glob
import numpy as np
import os
from matplotlib import mlab
import atpy
import sys
import pyfits

def compChunks(elsize,ncolmax):
   """
   Compute Chunck Size
   """

   # Compute chunksize.
   csize     = 300e3 # Target size uncompressed size for the chunks.
   crowsize = 100
   ccolsize  = int(csize/elsize/crowsize)
   ccolsize  = min(ccolsize,ncolmax)
   chunks = (ccolsize,crowsize)
   return chunks

def atpy2h5(files,out,diff='all',name='ds'):
   """
   atpy format to h5

   Parameters
   ----------

   inp  : globable string specifying where the input files are
   out  : output h5 file.  In none exists, we create it.

   diff : List of fields that are stored as stacked arrays.  Those
          that are not different, we store the first element.
   """
   nfiles = len(files)
   t0 = atpy.Table(files[0])
   h5 = File(out)
   ds,ds1d = diffDS(t0.table_name,t0.data.dtype,(nfiles,t0.data.size)
                    ,h5,diff=diff)
   
   kicL = []   
   nFail = 0 
#   import pdb;pdb.set_trace()
   for i in range(nfiles):
      if np.mod(i,100)==0:
         print i
      try:
         hdu = pyfits.open(files[i])
         data = hdu[1].data
         kic  = hdu[1].header['KEPLERID']
         assert type(kic) == int
         kicL.append(kic)
         
         if diff!='all':
            data = mlab.rec_keep_fields(data,diff)
            ds1d[:] =  mlab.rec_drop_fields(data,diff)

         ds[i-nFail] = data
   
      except:
         print sys.exc_info()[1]
         nFail +=1
         
   ds.resize(ds.shape[0]-nFail,axis=0)
   kicL = np.array(kicL)
   h5.create_dataset('KIC',data=kicL)
   print "%i files failed" % nFail
   h5.close()

def File(file):
   if os.path.exists(file):
      os.remove(file)
      print 'removing %s ' % file
   return h5py.File(file)


def diffDS(name,dtype,shape,h5,diff='all'):
   """
   Create Datasets

   Try to chunk it up into 300K sizes.

   Parameters
   ----------
   name   : Table name
   dtype  : Element data type
   shape  : 2D array shape (nLightCurves, nCadences)
   f      : h5 file handle
   """
   nrows,ncols = shape

   names = list(dtype.names)
   if diff != 'all':
      [names.remove(d)  for d in diff]
      dnames = diff
      
      sstr = "%s " % ', '.join(map(str,names))
      dstr = "%s " % ', '.join(map(str,dnames))

      print """
Same Columns
------------
%s

Diff Columns
------------
%s 

""" %(sstr,dstr )  

      sdtype = np.dtype([ (n,dtype[n]) for n in names])
      ds1d     = h5.create_dataset(name+'1d',shape=(ncols,),dtype=sdtype)
   else:
      ds1d = None
      dnames = names

   ddtype = np.dtype([ (n,dtype[n]) for n in dnames])


   # There chunksize cannot be bigger than shape (there should be a
   # more explicit warning for this.

   chunks = compChunks(dtype.itemsize,nrows)
   chunks = min(chunks[0],ncols),chunks[1]
   ds = h5.create_dataset(name,shape,ddtype,chunks=chunks,compression='lzf',
                          shuffle=True)

   print "ds.shape = (%i,%i); ds.chunks=(%i,%i)" % (ds.shape + ds.chunks)
   return ds,ds1d

def attchKW(ds,kwL,keys):
   """
   Attach keywords 

   Parameters
   ----------
   tL    : List of open tables
   keys  : List of h5 compatible keywords

   """
   for k in keys:
      k = str(k) # h5 saves saves keys as unicode
      kwarray = np.array( [kw[k] for kw in kwL] )
      try:
         ds.attrs[k] = kwarray
      except:
         print "could not attach %s" % k

   return ds