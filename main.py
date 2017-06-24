# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import webapp2
import cgi
from htmlform import *
import re
import jinja2
import os
from google.appengine.ext import db

template_dir=os.path.join(os.path.dirname(__file__),'templates')
jinja_env=jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),autoescape=True)

months = ['January',
          'February',
          'March',
          'April',
          'May',
          'June',
          'July',
          'August',
          'September',
          'October',
          'November',
          'December']

username_re = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
password_re=re.compile(r"^.{3,20}$")
email_re=re.compile(r"^[\S]+@[\S]+.[\S]+$")
def rot13function(text):
    textbox=[]
    for char in text:
        if char.isalpha():
            asciival=ord(char)+13
            if char.isupper():
                if asciival>90:
                    asciival-=26
            else:
                if asciival>122:
                    asciival -= 26
            textbox.append(chr(asciival))
        else:
            textbox.append(char)
    return (''.join(textbox))

def valid_month(month):
    if month.capitalize() in months:
        return month.capitalize()
def valid_day(day):
    if day.isdigit():
        day=int(day)
        if 1<=day<=31:
            return day
def valid_year(year):
    if year and year.isdigit():
        year=int(year)
        if 1900<=year<=2020:
            return year
def escape_html(s):
    return cgi.escape(s,quote=True)
def valid_username(user):
    return username_re.match(user)
def valid_password(password):
    return password_re.match(password)
def valid_email(email):
    return email_re.match(email) or not email
def match_password(password1,password2):
    return password1==password2

class Handler(webapp2.RequestHandler):
    def write(self,*a,**kw):
        self.response.out.write(*a,**kw)
    def render_str(self,template,**params):
        t=jinja_env.get_template(template)
        return t.render(params)
    def render(self,template,**kw):
        self.write(self.render_str(template,**kw))

class MainPage(Handler):
    # def write_form(self,error="",month="",day="",year=""):
    #     self.response.write(form % {'error': error,
    #                                 'month':escape_html(month),
    #                                 escape_html('day'):day,
    #                                 'year':escape_html(year)})
    def get(self):
        self.render('form.html')
    def post(self):
        user_month=self.request.get("month")
        user_day=self.request.get("day")
        user_year=self.request.get("year")
        bmonth=valid_month(user_month)
        bday=valid_day(user_day)
        byear=valid_year(user_year)
        if bmonth and bday and byear:
            self.redirect("/thanks")
        else:
            self.render('form.html',year=user_year,month=user_month,day=user_day,error='Not a Valid Date')
class Thanks(Handler):
    def get(self):
        self.response.write("Thanks for a valid date")
class rot13(Handler):
    def write_rot13form(self,text=""):
        self.response.write(rot13page %{'text':escape_html(text)})
    def get(self):
        self.write_rot13form()
    def post(self):
        textval=self.request.get("text")
        self.write_rot13form(rot13function(textval))

class usersignup(Handler):
    def write_signupform(self,user="",usererror="",pwerror="",matchingerror="",email=""):
        self.response.write(usersignupform % {'user':user,'usererror':usererror,
                                          'pwerror':pwerror,
                                          'matchingerror':matchingerror,
                                          'email':email})
    def get(self):
        self.write_signupform()
    def post(self):
        usererror = ""
        pwerror = ""
        matchingerror = ""
        input_user=self.request.get("username")
        input_password=self.request.get("password")
        input_verify=self.request.get("verify")
        input_email=self.request.get("email")
        username=valid_username(input_user)
        password=valid_password(input_password)
        matching=match_password(input_password,input_verify)
        email=valid_email(input_email)
        if username and password and matching and email:
            self.redirect("/welcome?username="+input_user)
        else:
            if not username:
                usererror="That's not a valid username."
            if not password:
                pwerror="That's not a valid password."
            if not matching:
                matchingerror="Your passwords didn't match."
            if not email:
                pass
            self.write_signupform(input_user,usererror,pwerror,matchingerror,input_email)

class welcome(Handler):
    def get(self):
        user=self.request.get("username")
        self.response.write("Welcome "+user)

class Pic(db.Model):
    title=db.StringProperty(required=True)
    pic=db.TextProperty(required=True)
    date=db.DateTimeProperty(auto_now_add=True)
class blogentry(db.Model):
    title=db.StringProperty(required=True)
    entry=db.TextProperty(required=True)
class ascii(Handler):
    def render_front(self,title="",pic="",error=""):
        pics=db.GqlQuery("select * from Pic order by date DESC")
        self.render('ascii.html',title=title,pic=pic,error=error,pics=pics)
    def get(self):
        self.render_front()
    def post(self):
        title=self.request.get("title")
        pic=self.request.get("asciipic")
        if title and pic:
            a=Pic(title=title,pic=pic)
            a.put()
            self.render_front()
        else:
            self.render_front(title=title, pic=pic,error="Please include both values")
class blog(Handler):
    def render_front(self,title="",entry="",error=""):
        entries=db.GqlQuery("select * from blogentry order by title DESC")
        self.render('blog.html',title=title,entry=entry,error=error,entries=entries)
    def get(self):
        self.render_front()

app = webapp2.WSGIApplication([
    ('/', MainPage),("/thanks",Thanks),("/rot13",rot13),("/usersignup",usersignup),("/welcome",welcome),
    ("/ascii",ascii),("/blog",blog)],debug=True)
