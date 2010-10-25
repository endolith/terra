import readstars
import numpy as np
import re
from elixir import *
import matplotlib
import fxwid

def res2id(file):
    """
    convert simbad query result into list simbad id
    """
    f = open(file,'r')
    lines = f.readlines()
    idxarr =[]
    oidarr = []

    for i in np.arange(len(lines)):
        if re.search('#1',lines[i]) is not None:
            idx,sep,oid = lines[i].partition('#1: ')
            idxarr.append(int(idx[idx.rfind('x')+1:]))
            oidarr.append(int(oid[:-1]))

    idxarr = np.array(idxarr)
    oidarr = np.array(oidarr)
    return idxarr,oidarr

def readluck(file):
    """
    Reads in file from Luck06
    """
    f = open(file,'r')
    txt = f.readlines()
    txt = txt[31:] #data starts at line 32
    nstars = len(txt)
    star = np.zeros(nstars,dtype='|S10')
    luckc = np.zeros(nstars,dtype=np.float)
    lucko = np.zeros(nstars,dtype=np.float)

    for i in np.arange(nstars):
        line = txt[i]
        star[i],luckc[i],lucko[i] = line[0:11],line[55:60],line[85:89]


    return star,luckc,lucko

def readramirez(file):
    """
    Reads in file from ramirez.dat
    """
    f = open(file,'r')
    txt = f.readlines()
    nstars = len(txt)

    star = np.zeros(nstars,dtype='|S10') #hiparcos name 
    teff = np.zeros(nstars,dtype=np.float) #effective temp
    o = np.zeros(nstars,dtype=np.float) #oxygen abudnance n-LTE corrected
    o_err = np.zeros(nstars,dtype=np.float) #oxygen abundance error n-LTE

    for i in np.arange(nstars):
        line = txt[i]
        star[i],teff[i],o[i],o_err[i] = \
            line[0:6],line[14:18],line[73:78],line[79:83]

    return star,teff,o,o_err


def readbensby(file):
    """
    Reads in file from bensby04.dat
    """
    f = open(file,'r')
    txt = f.readlines()
    nstars = len(txt)

    star = np.zeros(nstars,dtype='|S10') #hiparcos name 
    o_abund = np.zeros(nstars,dtype=np.float) #oxygen abudnance n-LTE corrected

    for i in np.arange(nstars):
        line = txt[i]        
        o = line[8:13]
        if o.strip() is '':
            o = None

        star[i],o_abund[i]= line[0:6],o

    return star,o_abund

def readbensby06(file):
    """
    Reads in file from bensby06.dat
    """
    f = open(file,'r')
    txt = f.readlines()
    nstars = len(txt)

    star = np.zeros(nstars,dtype='|S10') #HD name 
    c_abund = np.zeros(nstars,dtype=np.float) #oxygen abudnance n-LTE corrected

    for i in np.arange(nstars):
        line = txt[i]        
        line = line.split('\t')

        star[i],c_abund[i]= line[1],line[3]

    return star,c_abund

class Mystars(Entity):
    
    using_table_options(useexisting=True)
    using_options(allowcoloverride=True,tablename='mystars')
    name = Field(Text)
    oid  = Field(Text)

    vsini = Field(Float(precision=5))
    teff = Field(Float(precision=5))

    o_abund = Field(Float(precision=5))
    c_abund = Field(Float(precision=5))

    o_staterrlo = Field(Float(precision=5))
    o_staterrhi = Field(Float(precision=5))

    c_staterrlo = Field(Float(precision=5))
    c_staterrhi = Field(Float(precision=5))

    o_nierrlo = Field(Float(precision=5))
    o_nierrhi = Field(Float(precision=5))


class Luckstars(Entity):    
    using_table_options(useexisting=True)
    using_options(allowcoloverride=True,tablename='luckstars')

    name = Field(Text)
    oid  = Field(Text)

    o_abund = Field(Float(precision=5))
    c_abund = Field(Float(precision=5))


class Ramstars(Entity):    
    using_table_options(useexisting=True)
    using_options(allowcoloverride=True,tablename='ramstars')

    name = Field(Text)
    oid  = Field(Text)

    teff = Field(Float(precision=5))
    o_abund = Field(Float(precision=5))
    o_err = Field(Float(precision=5))

class Exo(Entity):    
    using_table_options(useexisting=True)
    using_options(allowcoloverride=True,tablename='exo')

    name = Field(Text)
    oid  = Field(Text)

    msini = Field(Float(precision=5))
    ecc = Field(Float(precision=5))
    a = Field(Float(precision=5))
    per = Field(Float(precision=5))


class Ben04(Entity):    
    using_table_options(useexisting=True)
    using_options(allowcoloverride=True,tablename='ben04')

    name = Field(Text)
    oid  = Field(Text)
    o_abund = Field(Float(precision=5))

class Ben06(Entity):    
    using_table_options(useexisting=True)
    using_options(allowcoloverride=True,tablename='ben06')

    name = Field(Text)
    oid  = Field(Text)
    c_abund = Field(Float(precision=5))

class Red03(Entity):    
    using_table_options(useexisting=True)
    using_options(allowcoloverride=True,tablename='red03')

    name = Field(Text)
    oid  = Field(Text)
    c_abund = Field(Float(precision=5))
    o_abund = Field(Float(precision=5))
    feh = Field(Float(precision=5))

class Red06(Entity):    
    using_table_options(useexisting=True)
    using_options(allowcoloverride=True,tablename='red06')

    name = Field(Text)
    oid  = Field(Text)
    c_abund = Field(Float(precision=5))
    o_abund = Field(Float(precision=5))



def mkdb():
    metadata.bind = "sqlite:///stars.sqlite"
#    metadata.bind.echo = True


    #### Add in mydata ####
    stars = readstars.ReadStars('keck-fit-lite.sav')
    idxarr,oidarr = res2id('Comparison/myresults.sim')

    setup_all(True)
    for i in range(len(stars.name)):        
        if (idxarr == i).any():
            oid = str(oidarr[np.where(idxarr == i)[0][0]])
        else:
            oid = None


        Mystars(name=stars.name[i],
                oid = oid,
                vsini = round(stars.vsini[i],3),
                teff  = round(stars.teff[i],0),
                o_abund = round(stars.o_abund[i],3),
                c_abund = round(stars.c_abund[i],3),
                o_staterrlo = round(stars.o_staterr[i,0],3),
                o_staterrhi = round(stars.o_staterr[i,1],3),
                
                c_staterrlo = round(stars.c_staterr[i,0],3),
                c_staterrhi =  round(stars.c_staterr[i,1],3),
                
                o_nierrlo = round(stars.o_nierr[i,0],3),
                o_nierrhi = round(stars.o_nierr[i,1],3),
                )


    #### Add in Luck Data ####
    luckname,luckc,lucko = readluck('Comparison/Luck06/Luck06py.txt')
    idxarr,oidarr = res2id('Comparison/Luck06/luckresults.sim')

    for i in range(len(luckname)):        
        if (idxarr == i).any():
            oid = str(oidarr[np.where(idxarr == i)[0][0]])
        else:
            oid = None

        Luckstars(name=luckname[i],
                  oid = oid,
                  o_abund = round(lucko[i],3),
                  c_abund = round(luckc[i],3)
                  )

    #### Add in Exo Data ####
    idxarr,oidarr = res2id('Comparison/exoresults.sim')
    rec = matplotlib.mlab.csv2rec('Comparison/exoplanets-org.csv')
    for i in range(len(rec['star'])):        
        if (idxarr == i).any():
            oid = str(oidarr[np.where(idxarr == i)[0][0]])

        else:
            oid = None

        Exo(name=rec['star'][i],
            oid = oid,
            msini = round(rec['msini'][i],3),
            ecc   = round(rec['ecc'][i],3),
            a     = round(rec['a'][i],3),
            per   = round(rec['per'][i],3)
            )            


    #### Add in Ramirez Data ####
    idxarr,oidarr = res2id('Comparison/Ramirez07/ramirezresults.sim')
    names,teff,o,o_err = readramirez('Comparison/Ramirez07/ramirez.dat')

    for i in range(len(names)):        
        if (idxarr == i).any():
            oid = str(oidarr[np.where(idxarr == i)[0][0]])
        else:
            oid = None

        Ramstars(name=names[i],
                  oid = oid,
                  teff = round(teff[i],0),
                  o_abund = round(o[i],3),
                  o_err = round(o_err[i],3)
                  )

    #### Add in Bensby Data ####
    idxarr,oidarr = res2id('Comparison/Bensby04/bensby04results.sim')
    names,o_abund = readbensby('Comparison/Bensby04/bensby04.dat')

    for i in range(len(names)):        
        if (idxarr == i).any():
            oid = str(oidarr[np.where(idxarr == i)[0][0]])
        else:
            oid = None

        Ben04(name=names[i],
              oid = oid,
              o_abund = round(o_abund[i],3),
              )
        

    idxarr,oidarr = res2id('Comparison/Bensby06/bensby06results.sim')
    names,c_abund = readbensby06('Comparison/Bensby06/bensby06.dat')

    for i in range(len(names)):        
        if (idxarr == i).any():
            oid = str(oidarr[np.where(idxarr == i)[0][0]])
        else:
            oid = None

        Ben06(name=names[i],
              oid = oid,
              c_abund = round(c_abund[i],3),
              )
        

    idxarr,oidarr = res2id('Comparison/Reddy03/reddy03results.sim')
    names,feh = fxwid.rdfixwid('Comparison/Reddy03/table1.dat',
                                  [[0,6],[17,22]],['|S10',np.float])
    
    names,c_abund,o_abund = fxwid.rdfixwid('Comparison/Reddy03/table5.dat',
                               [[0,6],[7,12],[19,23]],
                               ['|S10',np.float,np.float],empstr='----')
    

    for i in range(len(names)):        
        if (idxarr == i).any():
            oid = str(oidarr[np.where(idxarr == i)[0][0]])
        else:
            oid = None

        Red03(name=names[i],
              oid = oid,
              feh = round(feh[i],3),
              c_abund = round(c_abund[i]+feh[i],3),
              o_abund = round(o_abund[i]+feh[i],3),
              )
        




    idxarr,oidarr = res2id('Comparison/Reddy06/reddy06results.sim')    
    names,feh,c_abund,o_abund = fxwid.rdfixwid('Comparison/Reddy06/table45.dat',
                               [[17,23],[24,29],[30,35],[36,41]],
                               ['|S10',np.float,np.float,np.float],empstr='---')
    

    for i in range(len(names)):        
        if (idxarr == i).any():
            oid = str(oidarr[np.where(idxarr == i)[0][0]])
        else:
            oid = None

        Red06(name=names[i],
              oid = oid,
              c_abund = round(c_abund[i]+feh[i],3),
              o_abund = round(o_abund[i]+feh[i],3),
              )
        
    session.commit()
    session.close()
