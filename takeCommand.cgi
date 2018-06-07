#!/usr/bin/python

import cgi
import cgitb
cgitb.enable()

input_data=cgi.FieldStorage()

print('Content-Type:text/html') #HTML is following
print()                         #Leave a blank line
print('<h1>command output:</h1>')

try:
    iLine = str(input_data['inputLine'].value)
    print(iLine)
except:
    print '<p>Sorry, we cannot turn your inputs into numbers (integers).</p>'
    return 1
