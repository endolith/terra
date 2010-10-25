import getelnum
import numpy as np
import matplotlib.pyplot as plt
import readstars
import postfit
import matchstars
from scipy.optimize import leastsq
import starsdb
import sqlite3

def tfit(stars,save=False):

    """
    A quick look at the fits to the temperature
    """


    line = [6300,6587]
    subplot = ((1,2))
    plt.clf()
    f = plt.figure( figsize=(6,6) )
    f.set_facecolor('white')  #we wamt the canvas to be white

    f.subplots_adjust(hspace=0.0001)
    ax1 = plt.subplot(211)
    ax1.set_xticklabels('',visible=False)
    ax1.set_yticks(np.arange(-0.8,0.4,0.2))

    
    ax2 = plt.subplot(212,sharex=ax1)
    ax1.set_ylabel('[O/H]')
    ax2.set_ylabel('[C/H]')
    ax2.set_xlabel('$\mathbf{ T_{eff} }$')

    ax = (ax1,ax2)

    for i in range(2):
        o = getelnum.Getelnum(line[i])           
        fitabund, fitpar, t,abund = postfit.tfit(stars,line[i])    
        tarr = np.linspace(t.min(),t.max(),100)
        
        ax[i].scatter(t,abund,color='black',s=10)
        ax[i].scatter(o.teff_sol,0.,color='red',s=30)
        ax[i].plot(tarr,np.polyval(fitpar,tarr),lw=2,color='red')        

    plt.xlim(4500,6500)    
    if save:
        plt.savefig('Thesis/pyplots/teff.ps')


def abundhist(stars,save=False):

    """
    A quick look at the fits to the temperature
    """
    #pull in fitted abundances from tfit

    line = [6300,6587]
    antxt = ['[O/H]','[C/H]']

    subplot = ((1,2))
    plt.clf()
    f = plt.figure( figsize=(6,6) )
    f.set_facecolor('white')  #we wamt the canvas to be white

    f.subplots_adjust(hspace=0.0001)
    ax1 = plt.subplot(211)
    ax1.set_xticklabels('',visible=False)
    ax1.set_yticks(np.arange(0,200,50))


    
    ax2 = plt.subplot(212,sharex=ax1)
    ax2.set_yticks(np.arange(0,200,50))
    ax2.set_xlabel('[X/H]')



    ax = (ax1,ax2)


    for i in range(2):
        o = getelnum.Getelnum(line[i])           
        fitabund, fitpar, t,abund = postfit.tfit(stars,line[i])    
        ax[i].set_ylabel('Number of Stars')
        ax[i].hist(fitabund,range=(-1,1),bins=20,fc='gray')
        ax[i].set_ylim(0,200)
        ax[i].annotate(antxt[i],(-0.8,150))

        #output moments for tex write up
        print 'N, mean, std, min, max' + antxt[i]
        print '(%i,%f,%f,%f,%f)' % (fitabund.size,fitabund.mean(), \
            fitabund.luckstd(),fitabund.min(),fitabund.max())
        

    if save:
        plt.savefig('Thesis/pyplots/abundhist.ps')


def comp(save=False):
    files = ['smefiles/myresults.sim','smefiles/luckresults.sim']
    lines = [6300,6587]
    stars = readstars.ReadStars('keck-fit-lite.sav')
    mynames = stars.name
    lucknames,luckc,lucko = starsdb.readluck('smefiles/Luck06py.txt')

    f = plt.figure( figsize=(6,8) )

    ax1 = plt.subplot(211)



    ax2 = plt.subplot(212)
    ax1.set_xlabel('[O/H], Luck 2006')
    ax2.set_xlabel('[C/H], Luck 2006')

    ax1.set_ylabel('[O/H], This Work')
    ax2.set_ylabel('[C/H], This Work')
    ax = [ax1,ax2]



    for j in range(len(lines)):
        fitpass = postfit.fitbool(stars,lines[j])
        vpass = postfit.vbool(stars,lines[j])
        ul = postfit.ulbool(stars,lines[j])
        passidx = (np.where(~ul &fitpass & vpass))[0]
        myidx,mycomnames,luckidx,luckcomnames = matchstars.matchstars(files[0],mynames,files[1],lucknames)

        passcomidx = np.array(list(set(passidx) & set(myidx))) 
        idxidx = [] #indecies of which indecies are common to both
        for i in range(len(passcomidx)):
            idxidx.append( (np.where(mycomnames == mynames[passcomidx[i]]))[0][0])
            
        print mynames[myidx[idxidx]], lucknames[luckidx[idxidx]] 
        g = getelnum.Getelnum(lines[j])
        ncomp = len(idxidx)
        print str(ncomp)+' comparision stars '+str(lines[j])

        deg=3
        if j==0:
            a,fitpar,a,a = postfit.tfit(stars,lines[j])
            fitpar[deg] = fitpar[deg] - np.polyval(fitpar,g.teff_sol)

            y = stars.o_abund[myidx[idxidx]] - g.abnd_sol \
                - np.polyval(fitpar,stars.teff[myidx[idxidx]])
            x = lucko[luckidx[idxidx]] - g.abnd_sol_luck
            xerr = np.zeros(ncomp)+g.err_luck
            yerr = (stars.o_staterr[[myidx[idxidx]],1]).flatten()

            

        if j==1:
            a,fitpar,a,a = postfit.tfit(stars,lines[j])
            fitpar[deg] = fitpar[deg] - np.polyval(fitpar,g.teff_sol)

            y = stars.c_abund[myidx[idxidx]] - g.abnd_sol \
                - np.polyval(fitpar,stars.teff[myidx[idxidx]])


            x = luckc[luckidx[idxidx]] - g.abnd_sol_luck
            xerr = np.zeros(ncomp)+g.err_luck
            yerr = (stars.c_staterr[[myidx[idxidx]],1]).flatten()

        ax[j].errorbar(x,y,xerr=xerr,yerr=yerr,marker='o',ls='None',ms=4)
        
        fitrng = [-0.8,0.8]
        xfit = np.linspace(-2,2,100)
        yfit = np.polyval(np.polyfit(x,y,1),xfit)
        ax[j].plot(xfit,xfit)
        ax[j].set_ylim(fitrng[0],fitrng[1])
        ax[j].set_xlim(fitrng[0],fitrng[1])

#        ax[j].plot(xfit,yfit)


        print str(np.std(x-y)) + ' is stdev of differnce'
        
        if save:
            plt.savefig('Thesis/pyplots/comp.ps')



def co(save=False):
    stars = readstars.ReadStars('Stars/keck-fit-lite.sav')

    vpasso = postfit.vbool(stars,6300)
    fitpasso = postfit.fitbool(stars,6300)
    fitpassc = postfit.fitbool(stars,6587)
    ulc = postfit.ulbool(stars,6587)
    ulo = postfit.ulbool(stars,6300)    
    ratioidx = np.where(vpasso & fitpasso & fitpassc & ~ulo & ~ulc)[0]
    ax = plt.subplot(111)
    ax.scatter(stars.o_abund[ratioidx]-8.7,stars.c_abund[ratioidx]-8.5)
    ax.set_ylabel('[C/H]')
    ax.set_xlabel('[O/H]')

    x = np.linspace(-0.8,0.6,10)
    plt.plot(x,x+0.2)
    if save:
        plt.savefig('Thesis/pyplots/co.ps')
    
def cofe(save=False):
    stars = readstars.ReadStars('Stars/keck-fit-lite.sav')

    vpasso = postfit.vbool(stars,6300)
    fitpasso = postfit.fitbool(stars,6300)
    fitpassc = postfit.fitbool(stars,6587)
    ulc = postfit.ulbool(stars,6587)
    ulo = postfit.ulbool(stars,6300)    
    ratioidx = np.where(vpasso & fitpasso & fitpassc & ~ulo & ~ulc)[0]
    ax = plt.subplot(111)
    ax.scatter(stars.feh[ratioidx],10**(stars.c_abund[ratioidx]-stars.o_abund[ratioidx]))
    ax.set_ylabel('C/O')
    ax.set_xlabel('[Fe/H]')


def compmany(elstr='o'):
    if elstr == 'o':
#        tables = ['ben04','luckstars','mystars','ramstars','red03','red06']
#        tables = ['ben04','luckstars','mystars','ramstars','red03','red06']
        tables = ['mystars','ben04','red03','red06']
    if elstr =='c':
        tables = ['mystars','ben04','red03','red06']

    conn = sqlite3.connect('stars.sqlite')
    cur = conn.cursor()
    ncomp = len(tables)
    for i in range(ncomp):
        for j in range(ncomp):
            if i != j:
                tabx = tables[i]
                taby = tables[j]
            
                colx = tabx+'.'+elstr+'_abund'
                coly = taby+'.'+elstr+'_abund'
                cut  = ' WHERE '+tabx+'.oid = '+taby+'.oid '+'AND '+\
                    colx+' IS NOT NULL AND '+coly+' IS NOT NULL '
                if tabx == 'mystars' or taby == 'mystars':
                    cut = cut+' AND mystars.vsini < 8 AND mystars.'+elstr+ \
                        '_staterrlo > -0.3 AND mystars.'+elstr+'_abund > 0'
            
                ax = plt.subplot(ncomp,ncomp,i*ncomp+j+1)
                cmd = 'SELECT DISTINCT '+colx+','+coly+' FROM '+tabx+','+taby+cut
                cur.execute(cmd)
                    
                arr = np.array(cur.fetchall())
                if len(arr) > 0:
                    (x,y) = arr[:,0],arr[:,1]
                    ax.scatter(x-x.mean(),y-y.mean())

                ax.set_xlabel(tabx)
                ax.set_ylabel(taby)
                xlim = ax.get_xlim()
                x = np.linspace(xlim[0],xlim[1],10)
                ax.plot(x,x,color='red')

    plt.draw()
    conn.close()




