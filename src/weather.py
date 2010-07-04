#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Michael Liao (askxuefeng@gmail.com)'

import datetime
from xml.parsers.expat import ParserCreate

locations = {
        'beijing'      : 2151330,

        'chengdu'      : 2158433,

        'hong kong'    : 2165352,

        'jinan'        : 2168327,

        'mianyang'     : 2158439,

        'sanya'        : 2162784,
        'shanghai'     : 2151849,
        'shijiazhuang' : 2171287,

        'tianjin'      : 2159908,

        'wuhan'        : 2163866,
}

codes = {
        0 : u'龙卷风', # tornado
        1 : u'热带风暴', # tropical storm
        2 : u'飓风', # hurricane
        3 : u'风暴', # severe thunderstorms
        4 : u'雷雨', # thunderstorms
        5 : u'雨夹雪', # mixed rain and snow
        6 : u'雨夹冰雹', # mixed rain and sleet
        7 : u'雪夹冰雹', # mixed snow and sleet
        8 : u'冰毛毛雨', # freezing drizzle
        9 : u'毛毛雨', # drizzle
        10 : u'冰雨', # freezing rain
        11 : u'阵雨', # showers
        12 : u'阵雨', # showers
        13 : u'小雪', # snow flurries
        14 : u'小雨雪', # light snow showers
        15 : u'风雪', # blowing snow
        16 : u'下雪', # snow
        17 : u'冰雹', # hail
        18 : u'雨夹雪', # sleet
        19 : u'尘土', # dust
        20 : u'雾', # foggy
        21 : u'霾', # haze
        22 : u'烟雾', # smoky
        23 : u'狂风', # blustery
        24 : u'大风', # windy
        25 : u'寒冷', # cold
        26 : u'多云', # cloudy
        27 : u'多云', # mostly cloudy (night)
        28 : u'多云', # mostly cloudy (day)
        29 : u'局部多云', # partly cloudy (night)
        30 : u'局部多云', # partly cloudy (day)
        31 : u'晴朗', # clear (night)
        32 : u'晴', # sunny
        33 : u'晴朗', # fair (night)
        34 : u'晴朗', # fair (day)
        35 : u'雨夹冰雹', # mixed rain and hail
        36 : u'炎热', # hot
        37 : u'局部雷雨', # isolated thunderstorms
        38 : u'零星雷雨', # scattered thunderstorms
        39 : u'零星雷雨', # scattered thunderstorms
        40 : u'零星阵雨', # scattered showers
        41 : u'大雪', # heavy snow
        42 : u'零星雨夹雪', # scattered snow showers
        43 : u'大雪', # heavy snow
        44 : u'局部多云', # partly cloudy
        45 : u'雷阵雨', # thundershowers
        46 : u'小雪', # snow showers
        47 : u'局部雷雨', # isolated thundershowers
        3200 : u'暂无数据' # not available
}

class Wind(object):
    def __init__(self, chill, direction, speed):
        self.chill = chill
        self.direction = direction
        self.speed = speed

    def __str__(self):
        return r'{"chill" : %s, "direction" : %s, "speed" : %s}' % (self.chill, self.direction, self.speed)

    __repr__ = __str__

class Atmosphere(object):
    def __init__(self, humidity, visibility, pressure, rising):
        self.humidity = humidity
        self.visibility = visibility
        self.pressure = pressure
        self.rising = rising

    def __str__(self):
        return r'{"humidity" : %s, "visibility" : %s, "pressure" : %s, "rising": %s}' % (self.humidity, self.visibility, self.pressure, self.rising)

    __repr__ = __str__

class Astronomy(object):
    def __init__(self, sunrise, sunset):
        self.sunrise = sunrise
        self.sunset = sunset

    def __str__(self):
        return r'{"sunrise" : "%s", "sunset": "%s"}' % (self.sunrise, self.sunset)

    __repr__ = __str__

class Forecast(object):
    '<yweather:forecast day="Wed" date="30 Jun 2010" low="24" high="30" text="Mostly Cloudy" code="28" />'
    def __init__(self, day, date, low, high, code):
        self.day = day
        self.date = date
        self.low = low
        self.high = high
        self.code = code

    def __str__(self):
        return '{"date" : "%s", "day" : %s, "code" : %s, "text" : "%s", "low" : %d, "high" : %d, "image_large" : "%s", "image_small" : "%s"}' % (
                self.date, self.day, self.code, codes[self.code].encode('utf-8'), self.low, self.high,
                "http://weather-china.appspot.com/static/w/img/d%s.png" % self.code,
                "http://weather-china.appspot.com/static/w/img/s%s.png" % self.code,
        )

    __repr__ = __str__

def index_of(list, data):
    for i, item in enumerate(list):
        if data==item:
            return i
    return None

def get_day(day):
    return index_of(('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'), day)

def get_date(date):
    '30 Jun 2010'
    ss = date.split(' ')
    month = index_of(('', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'), ss[1])
    return datetime.date(int(ss[2]), month, int(ss[0]))

def to_24hour(time):
    ' convert "4:39 pm" to "16:39" '
    if time.endswith(' am'):
        return time[:-3]
    if time.endswith(' pm'):
        time = time[:-3]
        n = time.find(':')
        to_24h = int(time[:n]) + 12
        return "%d:%s" % (to_24h, time[n+1:])
    return time

class Weather(object):

    def char_data(self, text):
        if self.__isLastBuildDate:
            n = text.find(', ')
            text = text[n+2:]
            n1 = text.find(' ')
            n2 = text.find(' ', n1+1)
            m = text[n1+1:n2]
            month = index_of(('', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'), m)
            text = text.replace(m, str(month))
            if not text.endswith(' CST'):
                return
            text = text[:-4]
            is_pm = text.endswith(' pm')
            text = text[:-3]
            time = datetime.datetime.strptime(text, '%d %m %Y %I:%M')
            h = time.hour
            if is_pm:
                h = h + 12
            self.pub = '%d-%#02d-%#02d %#02d:%#02d' % (time.year, time.month, time.day, h, time.minute)

    def end_element(self, name):
        if name=='lastBuildDate':
            self.__isLastBuildDate = False

    def start_element(self, name, attrs):
        if name=='lastBuildDate':
            self.__isLastBuildDate = True
            return
        if name=='yweather:forecast':
            self.forecasts.append(Forecast(
                    get_day(attrs['day']),
                    get_date(attrs['date']),
                    int(attrs['low']),
                    int(attrs['high']),
                    int(attrs['code'])
            ))
        if name=='yweather:astronomy':
            self.astronomy.sunrise = to_24hour(attrs['sunrise'])
            self.astronomy.sunset = to_24hour(attrs['sunset'])
        if name=='yweather:atmosphere':
            self.atmosphere.humidity = attrs['humidity']
            self.atmosphere.visibility = attrs['visibility']
            self.atmosphere.pressure = attrs['pressure']
            self.atmosphere.rising = attrs['rising']
        if name=='yweather:wind':
            self.wind.chill = attrs['chill']
            self.wind.direction = attrs['direction']
            self.wind.speed = attrs['speed']

    def __init__(self, data):
        self.__isLastBuildDate = False
        self.pub = None
        self.wind = Wind(None, None, None)
        self.atmosphere = Atmosphere(None, None, None, None)
        self.astronomy = Astronomy(None, None)
        self.forecasts = []
        parser = ParserCreate()
        parser.returns_unicode = False
        parser.StartElementHandler = self.start_element
        parser.EndElementHandler = self.end_element
        parser.CharacterDataHandler = self.char_data
        parser.Parse(data)

    def __str__(self):
        pub = 'null'
        if self.pub:
            pub = r'"%s"' % self.pub
        return '{"pub" : %s, "wind" : %s, "astronomy" : %s, "atmosphere" : %s, "forecasts" : %s}' \
                % (pub, self.wind, self.astronomy, self.atmosphere, self.forecasts)

    __repr__ = __str__
