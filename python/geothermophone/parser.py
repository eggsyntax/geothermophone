from scipy.io import netcdf


f = netcdf.netcdf_file('/Users/egg/Temp/air.mon.mean.nc', 'r')
time = 0
lat = 0
lon = 0
air = f.variables['air']
print air[time][lat][lon]
