#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Michael Liao (askxuefeng@gmail.com)'

import os
import cgi
import time
import logging
import simplejson

from google.appengine.api import xmpp
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch
from google.appengine.runtime import apiproxy_errors
from google.appengine.api import memcache
from google.appengine.api import users

from Cheetah.Template import Template

import weather
import store

def get_city(request):
    # try get city from cookie:
    if 'Cookie' in request.headers:
        all = request.headers['Cookie']
        if all:
            cookies = all.split(';')
            for cookie in cookies:
                c = cookie.strip()
                if c.startswith('city='):
                    return c[5:]
    return None

def fetch_weather_in_cache(city):
    data = memcache.get(str(city.code))
    if data:
        return data
    data = fetch_weather(city)
    if data is None:
        return None
    memcache.set(str(city.code), data, 3600)
    return data

def fetch_weather(city):
    data = fetch_rss(city.code)
    if data is None:
        return None
    return str(weather.Weather(city.name, data))

def fetch_rss(code):
    url = 'http://weather.yahooapis.com/forecastrss?w=%s' % code
    logging.info('Fetch RSS: %s' % url)
    try:
        result = urlfetch.fetch(url, follow_redirects=False)
    except (urlfetch.Error, apiproxy_errors.Error):
        return None
    if result.status_code!=200:
        return None
    return result.content

class XmppHandler(webapp.RequestHandler):
    def post(self):
        message = xmpp.Message(self.request.POST)
        logging.info('XMPP from %s: %s' % (message.sender, message.body))
        name = message.body.strip()
        if name=='':
            message.reply('Please type your city to get weather forecast.')
            return
        city = store.find_city(name, return_default=False)
        if city is None:
            message.reply(':( Could not find your city "%s"' % name)
            return
        json = fetch_weather_in_cache(city)
        if json is None:
            return message.reply('Oops! Service is unavailable now. Please try again later!')
        if isinstance(json, unicode):
            json = json.encode('utf-8')
        w = simplejson.loads(json, encoding='utf-8')
        logging.info(w)
        return message.reply(
                u'''%s：
今日：%s，%s～%s度
明日：%s，%s～%s度
发布于：%s
                ''' % (
                w[u'name'],
                w[u'forecasts'][0][u'text'], w[u'forecasts'][0][u'low'], w[u'forecasts'][0][u'high'],
                w[u'forecasts'][1][u'text'], w[u'forecasts'][1][u'low'], w[u'forecasts'][1][u'high'],
                w[u'pub'])
        )

class HomeHandler(webapp.RequestHandler):
    def get(self):
        name = get_city(self.request)
        cities = store.get_cities()
        city = store.find_city(name)
        if city is None:
            self.response.set_status(500)
            return
        root = os.path.dirname(__file__)
        t = Template(file=os.path.join(root, 'home.html'), searchList=[{'city' : city, 'cities' : cities}])
        self.response.out.write(t)

class AdminHandler(webapp.RequestHandler):

    def get(self):
        login = self.get_login_url()
        if login:
            self.redirect(login)
            return
        action = self.request.get('action', '')
        if action=='delete_city':
            key = self.request.get('key')
            store.delete_city(key)
            self.redirect_admin()
            return
        if action=='':
            cities = store.get_cities()
            root = os.path.dirname(__file__)
            t = Template(file=os.path.join(root, 'admin.html'), searchList=[{'cities' : cities}])
            self.response.out.write(t)
            return
        self.response.set_status(400)

    def post(self):
        login = self.get_login_url()
        if login:
            self.redirect(login)
            return
        action = self.request.get('action')
        if action=='create_city':
            name = cgi.escape(self.request.get('name')).strip().lower()
            aliases = [cgi.escape(x).lower() for x in self.request.get_all('aliases') if x.strip()]
            code = int(self.request.get('code'))
            store.create_city(name, aliases, code)
            self.redirect_admin()
            return
        self.response.set_status(400)

    def get_login_url(self):
        if not users.is_current_user_admin():
            return users.create_login_url('/admin')
        return None

    def redirect_admin(self):
        self.redirect('/admin?t=%s' % time.time())

class ApiHandler(webapp.RequestHandler):

    CACHE_TIME = 600 # 600 seconds

    def get(self):
        callback = ''
        c = ''
        extension = self.request.get('extension', '')
        if extension=='chrome':
            # detect city from cookie:
            c = get_city(self.request)
            if not c:
                c = 'beijing'
        else:
            callback = cgi.escape(self.request.get('callback', '').strip())
            c = cgi.escape(self.request.get('city', '')).lower()
        if not c:
            return self.send_error('MISSING_PARAMETER', 'Missing parameter \'city\'')
        city = store.find_city(c, return_default=False)
        if city is None:
            return self.send_error('CITY_NOT_FOUND', 'City not found')
        weather = fetch_weather_in_cache(city)
        if weather is None:
            return self.send_error('SERVICE_UNAVAILABLE', 'Service unavailable')
        if callback:
            if isinstance(callback, unicode):
                callback = callback.encode('utf-8')
            self.write_json('%s(%s);' % (callback, weather))
        else:
            self.write_json(weather)

    def send_error(self, code, msg):
        json = '{ "error" : "%s", "message" : "%s"}' % (code, msg)
        self.write_json(json)

    def write_json(self, json):
        if isinstance(json, unicode):
            json = json.encode('utf-8')
        self.response.headers['Content-Type'] = 'application/json; charset=utf-8'
        self.response.out.write(json)

application = webapp.WSGIApplication([
        ('^/$', HomeHandler),
        ('^/api$', ApiHandler),
        ('^/admin$', AdminHandler),
        ('^/_ah/xmpp/message/chat/$', XmppHandler),
], debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
