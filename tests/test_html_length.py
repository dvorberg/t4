#!/usr/bin/env python

from t4.web import html_length, html_area

print html_length(120) # 120px
print html_length("120") # 120px
print html_length("120px") # 120px
print html_length("12em") # 120px
print
print html_length(100) + html_length(100) # 200px
print html_length(100) - html_length(100) # 0px
print html_length(100) * html_length(100) # 10000px
print html_length(100) / html_length(100) # 1px
print
print html_length(100) + 100 # 200px
print html_length(100) - 100 # 0px
print html_length(100) * 100 # 10000px
print html_length(100) / 100 # 1px

print
print

print html_area(800, 600)
print html_area(800, 600) * 2
print html_area(800, 600).thumb_size ( (640, 480,) )
print html_area(800, 600).thumb_size( (640, 480,) ).size()

