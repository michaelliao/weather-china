#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Michael Liao (askxuefeng@gmail.com)'

import os
import cgi
import time

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch
from google.appengine.runtime import apiproxy_errors
from google.appengine.api import memcache
from google.appengine.api import users

from Cheetah.Template import Template

import weather
import store

class HomeHandler(webapp.RequestHandler):
    def get(self):
        city = store.get_cities()
        if city is None:
            self.response.set_status(500)
            return
        root = os.path.dirname(__file__)
        t = Template(file=os.path.join(root, 'home.html'), searchList=[{'city' : city}])
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
        c = cgi.escape(self.request.get('city', '')).lower()
        if not c:
            return self.send_error('MISSING_PARAMETER', 'Missing parameter \'city\'')
        city = store.find_city(c)
        if city is None:
            return self.send_error('CITY_NOT_FOUND', 'City not found')
        weather = self.fetch_weather_in_cache(city.code)
        if weather is None:
            return self.send_error('SERVICE_UNAVAILABLE', 'Service unavailable')
        self.write_json(weather)

    def send_error(self, code, msg):
        json = '{ "error" : "%s", "message" : "%s"}' % (code, msg)
        self.write_json(json)

    def write_json(self, json):
        if isinstance(json, unicode):
            json = json.encode('utf-8')
        self.response.headers['Content-Type'] = 'application/json; charset=utf-8'
        self.response.out.write(json)

    def fetch_weather_in_cache(self, code):
        data = memcache.get(str(code))
        if data:
            return data
        data = self.fetch_weather(code)
        if data is None:
            return None
        memcache.set(str(code), data, 3600)
        return data

    def fetch_weather(self, code):
        data = self.fetch_rss(code)
        if data is None:
            return None
        return str(weather.Weather(data))

    def fetch_rss(self, code):
        url = 'http://weather.yahooapis.com/forecastrss?u=c&w=%s' % code
        try:
            result = urlfetch.fetch(url, follow_redirects=False)
        except (urlfetch.Error, apiproxy_errors.Error):
            return None
        if result.status_code!=200:
            return None
        return result.content

application = webapp.WSGIApplication([
        ('^/$', HomeHandler),
        ('^/api$', ApiHandler),
        ('^/admin$', AdminHandler),
], debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
