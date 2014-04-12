'''
Here's the key datasource: http://www.esrl.noaa.gov/psd/data/gridded/data.ncep.reanalysis.html
Many bookmarks in Other Bookmarks/gridded _climate

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
Per Wikipedia, global min/max records are -89, 57. And these are monthly means, so they wouldn't be as extreme.

What vars are interesting?
Temperature, obviously.
std dev of temp would be awesome, to show the climate getting more variable, but they only have
	them starting in 1981. Could calculate myself, of course. We're really getting a very averaged-out
	temperature, since we're taking monthly mean and averaging it over 1/8 of the earth. So we don't
	get to see that side of climate change.
	Ah, I can get 2-meter 4x daily temp (presumably instantaneous) from here: http://www.esrl.noaa.gov/psd/cgi-bin/db_search/DBSearch.pl?Dataset=NCEP+Reanalysis+Surface+Flux&Variable=Air+Temperature
	Daily and sub-daily vals are in files by year.

prate is measured in Kg/m^2/s (which appear to be units of flux)

Note: precip is gridded differently :(
	#lon/lat -- 94 x 192 -- ARGH WTF WTF. And 1st value is -32758, which is worrying
	# This one came from ESRL, though -- maybe they resample?
	# No, same directly from ftp site where I got air. So OK, gridding is inconsistent between vars.
	# Yeah, it actually says it on the web page. Gotta just go with it, I guess.

OK, here's some tests:

testing air
sample value, -34.9268
actual range, [-73.78000641  41.74901962]
lon, 73
lat, 144
apparent date: 1948-01-01 00:00:00


testing prate
sample value, 1.91279e-06
actual range, [ -2.32830644e-10   5.89039992e-04]
lon, 94
lat, 192
apparent date: 1948-01-01 00:00:00


testing rhum
sample value, 93.0323
actual range, [   0.          100.01000214]
lon, 73
lat, 144
apparent date: 1948-01-01 00:00:00


testing wspd
sample value, -19809
actual range, [  0.50300378  21.32439613]
lon, 73
lat, 144
apparent date: 1948-01-01 00:00:00


Strategy:
For each variable, divide data into eight sections -- 2 based on lat, 4 based on lon
Average data in each section for each time. I think I can just base it on a set of values.
Note that I want to start with whatever time index represents 1960 and use 600 values ((2010-1960) * 12)
Output list of times, containing:
	Dict from section key to a set of values (at each time)
	key is a tuple(lon_section, lat_section) -- ordered based on their unusual ordering

To start:
	do air.
'''
from datetime import timedelta, datetime
import math
from scipy.io import netcdf
import numpy

shortener = 10 # TD for testing (set to 1 or delete later)
basetime = datetime(1901, 1, 1, 0, 0, 0)
starttime = datetime(1960, 1, 1, 0, 0, 0)
endtime = datetime(2010, 1, 1, 0, 0, 0)
timeoffset = timedelta(days=693962) # Arbitrary offset by trial and error

def from_datetime(dt):
	''' Convert from datetime to hours since 1-1-1 00:00:0.0 '''
	new_dt = dt	+ timeoffset - basetime
	seconds = new_dt.total_seconds()
	hours = seconds / (60 * 60)
	return hours

def to_datetime(hours):
	''' Convert from hours since 1-1-1 00:00:0.0 to datetime '''
	td = timedelta(hours=hours)
	return td + basetime - timeoffset

def test_to_from_datetime():
	test_hours = 7000
	dt = to_datetime(test_hours)
	hours = from_datetime(dt)
	assert hours == test_hours, 'Going to and then from datetime didn\'t get us back to the original'

class LonLatSplitter(object):
	''' Name and params follow unconventional ordering in files '''
	def __init__(self, lon_range, lat_range):
		''' Note that we can use either the range of indices or the actual
		 range of lat/lon values as long as we're consistent. '''
		self.lon_range = lon_range
		self.lat_range = lat_range
		self.lon_divisor = lon_range / 4.0
		self.lat_divisor = lat_range / 2.0

	def split_to_octs(self, lon, lat):
		''' return the key (0..3, 0..1) for which octant the lat/lon is in. '''
		assert lon < self.lon_range, 'Longitude %d is outside range (max should be %d)' % (lon, self.lon_range-1)
		assert lat < self.lat_range, 'Latitude %d is outside range (max should be %d)' % (lat, self.lat_range-1)

		lon_key = int(math.floor(lon / self.lon_divisor))
		lat_key = int(math.floor(lat / self.lat_divisor))
		return (lon_key, lat_key)

def _test_var(var, filename):
	print; print
	print 'testing', var
	f = netcdf.netcdf_file(filename, 'r')
	time = 0
	lat = 0
	lon = 0
	data = f.variables[var]
	print 'sample value,', data[time][lon][lat]
	print 'actual range,',data.actual_range
	print 'lon,', len(data[time])
	print 'lat,', len(data[time][lon])
	print 'lon range:', f.variables['lon'].actual_range
	print 'lat range:', f.variables['lat'].actual_range
	print 'apparent date:', to_datetime(f.variables['time'][0])
	import IPython; IPython.embed() #TD REPL


def get_data(var, filename):
	f = netcdf.netcdf_file(filename, 'r')
	data = f.variables[var]

	results = []
	num_lons = len(data[0])
	num_lats = len(data[0][0])
	oct_splitter = LonLatSplitter(num_lons, num_lats)
	for time in range(len(data.data)):
		#TD limit to 600 values starting in 1960
		results_for_t = {}
		for lon in range(len(data[time])):
			for lat in range(len(data[time][lon])):
				oct_key = oct_splitter.split_to_octs(lon, lat)
				results_for_oct = results_for_t.setdefault(oct_key, []) # list because numpy.mean doesn't like sets
				value = data[time][lon][lat]
				if value != data.missing_value:
					results_for_oct.append(value)
		results.append(results_for_t)

	# Now we go through and replace each set of values with its average
	for results_for_time in results:
		for key, results_for_oct in results_for_time.items():
			# print type(results_for_oct)
			results_for_time[key] = numpy.mean(results_for_oct)

	# Now we reconfigure to a dict of octants, containing 8 lists of average
	# values by time.
	keys = results[0].keys()
	result_lists = {}
	for results_for_time in results:
		for key in keys:
			result_lists.setdefault(key, []).append(results_for_time[key])

	for octant in sorted(result_lists.keys()):
		print 'octant:',octant
		print result_lists[octant]

def test_all_vars():
	''' Really just prints a bunch of stuff about each var, no actual tests. '''
	for var, filename in (
			# ('air', '/Users/egg/Temp/GriddedData/air.mon.mean.nc'),
			('prate', '/Users/egg/Temp/GriddedData/prate.sfc.mon.mean.nc',),
			# ('rhum', '/Users/egg/Temp/GriddedData/rhum.mon.mean.nc'),
			# ('wspd', '/Users/egg/Temp/GriddedData/wspd.mon.mean.nc'),
		):
		_test_var(var, filename)

def test_lon_lat_splitter():
	lls = LonLatSplitter(73, 144) # air is like this
	def test_vals(lon, lat, expected):
		octant = lls.split_to_octs(lon, lat)
		assert octant == expected, \
			'Expected %s but got %s.' % (expected, octant)

	test_vals(0, 0, (0, 0))
	test_vals(72, 143, (3, 1))
	test_vals(37, 73, (2, 1))

if __name__ == '__main__':
	get_data('air', '/Users/egg/Temp/GriddedData/air.mon.mean.nc')