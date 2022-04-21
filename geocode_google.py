import csv

from geopy.geocoders import GoogleV3

API = "YOUR API KEY"

ifile = "/home/remi/Downloads/cities.csv"
ofile = "/home/remi/Downloads/cities_out.csv"

with open(ifile, 'r') as ihandle:
    lines = csv.reader(ihandle)
    out_lines = []
    for line in lines:
        out_line = line
        loc_string = line[0]
        geolocator = GoogleV3(api_key=API)
        location = geolocator.geocode(loc_string)
        out_line.extend([location.raw['address_components'][-1]['short_name'], location.latitude, location.longitude])
        out_lines.append(out_line)

with open(ofile, 'w') as ohandle:
    write = csv.writer(ohandle)
    write.writerow(["location", "start_year", "population", "cyclovia_model", "country", "latitude", "longitude"])
    write.writerows(out_lines)

