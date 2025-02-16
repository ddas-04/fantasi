from fenics import *
from mshr import *
import numpy as np

'''
The LLG equation for Zeeman fields defined by (Hx, Hy and Hz)

The functions expect gam_fac to be "gamma / (1+alpha*alpha)"
'''
def dmdt_happx(gam_fac, alph_damp, Hx, q_degree):
	dmdt=Expression(("G*a*(1-x[0]*x[0])*H","-1.0*G*(x[2]+a*x[0]*x[1])*H","G*(x[1]-a*x[0]*x[2])*H"),G=gam_fac, a=alph_damp, H=Hx, degree=q_degree)
	return dmdt

def dmdt_happy(gam_fac, alph_damp, Hy, q_degree):
	dmdt=Expression(("G*(x[2]-a*x[0]*x[1])*H","G*a*(1-x[1]*x[1])*H","-1.0*G*(x[0]+a*x[1]*x[2])*H"),G=gam_fac, a=alph_damp, H=Hy, degree=q_degree)
	return dmdt

def dmdt_happz(gam_fac, alph_damp, Hz, q_degree):
	dmdt=Expression(("-1.0*G*(x[1]+a*x[0]*x[2])*H","G*(x[0]-a*x[1]*x[2])*H","G*a*(1-x[2]*x[2])*H"),G=gam_fac, a=alph_damp, H=Hz, degree=q_degree)
	return dmdt

'''
The LLG equation for uniaxial anisotropy fields defined by (Huax, Huay and Huaz)

The functions expect gam_fac to be "gamma / (1+alpha*alpha)"
These functions can be combined to calculate the shape anisotropy
effective field
'''
def dmdt_huax(gam_fac, alph_damp, Huax, q_degree):
	dmdt=Expression(("G*a*(1-x[0]*x[0])*H*x[0]","-1.0*G*(x[2]+a*x[0]*x[1])*H*x[0]","G*(x[1]-a*x[0]*x[2])*H*x[0]"),G=gam_fac, a=alph_damp, H=Huax, degree=q_degree)
	return dmdt

def dmdt_huay(gam_fac, alph_damp, Huay, q_degree):
	dmdt=Expression(("G*(x[2]-a*x[0]*x[1])*H*x[1]","G*a*(1-x[1]*x[1])*H*x[1]","-1.0*G*(x[0]+a*x[1]*x[2])*H*x[1]"),G=gam_fac, a=alph_damp, H=Huay, degree=q_degree)
	return dmdt

def dmdt_huaz(gam_fac, alph_damp, Huaz, q_degree):
	dmdt=Expression(("-1.0*G*(x[1]+a*x[0]*x[2])*H*x[2]","G*(x[0]-a*x[1]*x[2])*H*x[2]","G*a*(1-x[2]*x[2])*H*x[2]"),G=gam_fac, a=alph_damp, H=Huaz, degree=q_degree)
	return dmdt

'''
The LLG equation for spin torque

The calculation of the torque term follows the prescription in OOMMF (see the Oxs_SpinXferEvolve class)

Expected inputs to the function are as follows
gam_fac      : gyromagnetic ratio (expecting 1.7595e11 rad/Ts)
alph_damp    : Gilbert damping parameter
Pfix         : polarization at interface with fixed layer
Pfree        : polarization at interface with free layer
LambFix      : asymmetry factor at interface with fixed layer
LambFree     : asymmetry factor at interface with free layer
epsPrime     : factor for field-like torque
Icurr        : charge current that is generating spin-current
vol          : volume of free layer
Ms_          : saturation magnetization of free layer
mp           : 3d magnetization vector for fixed layer magnetization (the function will normalize this vector)
'''

def dmdt_mp(gam_fac, alph_damp, Pfix, Pfree, LambFix, LambFree, epsPrime, Icurr, vol, Ms_, mp, q_degree):
	HBAR=1.05457173E-34
	QE=1.60217646E-19
	MU0=np.pi * 4.0E-7
	lambFix2=0.0
	if (LambFix < 1.0):
		print("ERROR: LambFix must be greater than or equal to 1.0\n")
		exit()
	else:
		lambFix2=LambFix*LambFix

	lambFree2=0.0
	if (LambFree < 1.0):
		print("ERROR: LambFree must be greater than or equal to 1.0\n")
		exit()
	else:
		lambFree2=LambFree*LambFree


	lambdafreePlus = 1.0
	lambdafreeMinus = 0.0
	lambdafreePlus = np.sqrt(lambFree2 + 1.0)
	if (lambFree2 > 1.0):
		lambdafreeMinus = np.sqrt(lambFree2 - 1.0)

	lambdafixPlus = 1.0
	lambdafixMinus = 0.0
	lambdafixPlus = np.sqrt(lambFix2 + 1.0)
	if (lambFix2 > 1.0):
		lambdafixMinus = np.sqrt(lambFix2 - 1.0)


	plus_ratio = lambdafreePlus / lambdafixPlus
	minus_ratio = 1.0
	if (lambdafreeMinus > 0.0):
		minus_ratio = lambdafixMinus / lambdafreeMinus

	plus_factor = Pfix * lambFix2 * plus_ratio;
	minus_factor = Pfree * lambFree2 * minus_ratio;
	q_plus = plus_factor + minus_factor;
	q_minus = plus_factor - minus_factor;
	lplus2 = lambdafreePlus * lambdafixPlus;
	lminus2 = lambdafreeMinus * lambdafixMinus;

	pnorm = np.sqrt(mp[0]*mp[0] + mp[1]*mp[1] + mp[2]*mp[2]);
	if (pnorm == 0.0):
		print("ERROR: mp must not be null vector!\n")

	beta=(HBAR / vol) * ( Icurr / (2.0 * Ms_ * QE * pnorm) )

	# pdotm = (px*x[0] + py*x[1] + pz*x[2])
	# A_plus = lplus2 + (lminus2 * pdotm)
	# A_minus = lplus2 - (lminus2 * pdotm)
	# epsilon = (q_plus / A_plus) - (q_minus / A_minus)

	# A = epsilon
	# B = epsPrime

	# gilb     = beta / (1.0 + alph_damp * alph_damp);
	# mxpxmFac = gilb * (A + alph_damp * B)
	# pxmFac   = gilb * (B - alph_damp * A)

	# Cross-product 1
	# pxm.x = py*mz - pz*my
	# pxm.y = mx*pz - mz*px
	# pxm.z = px*my - py*mx

	# Cross-product 2
	# mxpxm.x = my*pxm.z - mz*pxm.y
	# mxpxm.y = pxm.x*mz - pxm.z*mx
	# mxpxm.z = mx*pxm.y - my*pxm.x

	# Form compiler needs variables that are not expressions of other variables. gilb needs
	# to be factored into a constant part and the part that depends on current
	# gilb=((gam_fac*beta) / (1.0 + alph_damp*alph_damp))
	#     = beta * (gam_fac / (1.0 + alph_damp*alph_damp)
	# beta=(HBAR / vol) * ( Icurr / (2.0 * Ms_ * QE * pnorm) )
	#     = Icurr * (HBAR / (vol * 2.0 * Ms_ *QE *pnorm))
	# gilb = gilbF * Icurr
	gilbF=Constant((gam_fac / (1.0 + alph_damp*alph_damp)) * (HBAR / ( 2.0 * vol * Ms_ * QE * MU0 * pnorm)))
	
	dmdt=Expression(("(gilb * Icurr * (B - alpha * ((q_plus / (lplus2 + (lminus2 * (px*x[0] + py*x[1] + pz*x[2])))) + (q_minus / (lplus2 - (lminus2 * (px*x[0] + py*x[1] + pz*x[2]))))))) * (py*x[2] - pz*x[1]) + (gilb * Icurr * (((q_plus / (lplus2 + (lminus2 * (px*x[0] + py*x[1] + pz*x[2])))) + (q_minus / (lplus2 - (lminus2 * (px*x[0] + py*x[1] + pz*x[2]))))) + alpha * B)) * (x[1]*(px*x[1] - py*x[0]) - x[2]*(x[0]*pz - x[2]*px))", "(gilb * Icurr * (B - alpha * ((q_plus / (lplus2 + (lminus2 * (px*x[0] + py*x[1] + pz*x[2])))) + (q_minus / (lplus2 - (lminus2 * (px*x[0] + py*x[1] + pz*x[2]))))))) * (x[0]*pz - x[2]*px) + (gilb * Icurr * (((q_plus / (lplus2 + (lminus2 * (px*x[0] + py*x[1] + pz*x[2])))) + (q_minus / (lplus2 - (lminus2 * (px*x[0] + py*x[1] + pz*x[2]))))) + alpha * B)) * (x[2]*(py*x[2] - pz*x[1]) - x[0]*(px*x[1] - py*x[0]))", "(gilb * Icurr * (B - alpha * ((q_plus / (lplus2 + (lminus2 * (px*x[0] + py*x[1] + pz*x[2])))) + (q_minus / (lplus2 - (lminus2 * (px*x[0] + py*x[1] + pz*x[2]))))))) * (px*x[1] - py*x[0]) + (gilb * Icurr * (((q_plus / (lplus2 + (lminus2 * (px*x[0] + py*x[1] + pz*x[2])))) + (q_minus / (lplus2 - (lminus2 * (px*x[0] + py*x[1] + pz*x[2]))))) + alpha * B)) * (x[0]*(x[0]*pz - x[2]*px) - x[1]*(py*x[2] - pz*x[1]))"), gilb=gilbF, Icurr=Icurr, alpha=alph_damp, B=epsPrime, q_minus=q_minus, q_plus=q_plus, lplus2=lplus2, lminus2=lminus2, px=mp[0], py=mp[1], pz=mp[2], degree=q_degree)
	return dmdt

