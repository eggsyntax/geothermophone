'''
NOTE! Data are scaled and offset. See http://www.esrl.noaa.gov/psd/data/gridded/faq.html#2
Same with time.
I don't want the R2 reanalysis; it's better but doesn't go back far enough in time.
2.5 degree grid (144x73). 90N - 90S, 0E - 357.5E
Dividing into 8:
	2 long (36 each, with one skipped).
	4 lat  (36 each)

Temp is in Kelvin (but clearly has offset/scale -- raw sample temp is -34, aka -540 F)
Wait, no, it says it's in degC (via air.units).
Hmm. maybe no offset. air.actual range is -73..41, which in F is -99..106. Seems reasonableish.
Per Wikipedia, min/max records are -89, 57. And these are monthly means, so they wouldn't be as extreme.
# time slots
'''
from scipy.io import netcdf

f = netcdf.netcdf_file('/Users/egg/Temp/air.mon.mean.nc', 'r')
time = 0
lat = 0
lon = 0
air = f.variables['air']
print air[time][lon][lat]
print air.actual_range # 794, which makes sense as # months from 1948-2014
import IPython; IPython.embed() #TD REPL
print 'lon,', len(air[time]) # 73
print 'lat,', len(air[time][lon]) # 144
