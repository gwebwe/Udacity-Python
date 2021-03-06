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
import hashlib
import hmac
import urllib2
from xml.dom import minidom
import json

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
IP_URL="http://freegeoip.net/xml/"
GMAPS_URL = "http://maps.googleapis.com/maps/api/staticmap?size=380x263&sensor=false&"
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
def check_user(input_user):
    checkuser = db.GqlQuery("select user from useraccounts where user=:1", input_user)
    return checkuser==input_user




def get_coords(ip):
    url=IP_URL+ip
    content= None
    try:
        content=urllib2.urlopen(url).read()
    except URLError:
        return "error"
    if content:
        parseval=minidom.parseString(content)
        if parseval:
            lat=parseval.getElementsByTagName("Latitude")[0].childNodes[0].nodeValue
            lon = parseval.getElementsByTagName("Longitude")[0].childNodes[0].nodeValue
            return db.GeoPt(lat,lon)


def gmaps_img(points):
    ###Your code here
    query="&".join("markers=%s,%s" % (p.lat,p.lon) for p in points)
    return GMAPS_URL + query

class Handler(webapp2.RequestHandler):
    def write(self,*a,**kw):
        self.response.out.write(*a,**kw)
    def render_str(self,template,**params):
        t=jinja_env.get_template(template)
        return t.render(params)
    def render(self,template,**kw):
        self.write(self.render_str(template,**kw))
    def render_json(self, d):
        json_txt = json.dumps(d)
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.write(json_txt)

class MainPage(Handler):
    def write_form(self,error="",month="",day="",year=""):
        self.render('form.html',error=error,month=month,day=day,year=year,)
    def get(self):
        self.write_form()
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
            self.write_form(error='Not a Valid Date',month=user_month,day=user_day,year=user_year)
class Thanks(Handler):
    def get(self):
        self.response.write("Thanks for a valid date")
class rot13(Handler):
    def write_rot13form(self,textval=""):
        self.render('rot13.html',textval=textval)
    def get(self):
        self.write_rot13form()
    def post(self):
        textval=self.request.get("text")
        self.write_rot13form(rot13function(textval))

class usersignup(Handler):
    def write_signupform(self,user="",usererror="",pwerror="",matchingerror="",email=""):
        self.render('signup.html',user=user,usererror=usererror,
                    pwerror=pwerror,
                    matchingerror=matchingerror,
                    email=email)
    def get(self):
        self.write_signupform()
    def post(self):
        usererror = ""
        pwerror = ""
        matchingerror = ""
        cookie_user=str(self.request.cookies.get('name'))
        input_user=str(self.request.get("username"))
        input_password=self.request.get("password")
        input_verify=self.request.get("verify")
        input_email=self.request.get("email")
        username=valid_username(input_user)
        password=valid_password(input_password)
        matching=match_password(input_password,input_verify)
        email=valid_email(input_email)
        hashpassword=hashlib.md5(input_password).hexdigest()
        checkuser=check_user(input_user)
        if username and password and matching and email and (input_user!=cookie_user) and not checkuser:
            useracc=useraccounts(user=input_user,password=hashpassword)
            useracc.put()
            self.response.headers.add_header('Set-Cookie', 'name=%s; Path=/' % input_user)
            self.redirect("/welcome")
        else:
            if checkuser or input_user==cookie_user:
                usererror="User already exist, try a new user"
            if not username:
                usererror="That's not a valid username."
            if not password:
                pwerror="That's not a valid password."
            if not matching:
                matchingerror="Your passwords didn't match."
            if not email:
                pass
            self.write_signupform(input_user,usererror,pwerror,matchingerror,input_email)

class login(Handler):
    def render_login(self,loginerror=''):
        self.render('login.html',loginerror=loginerror)
    def get(self):
        self.render_login()
    def post(self):
        input_user = str(self.request.get("username"))
        input_password = hashlib.md5(self.request.get("password")).hexdigest()
        checkinfo = db.GqlQuery("select * from useraccounts where user=:1", input_user)
        if  checkinfo[0].user==input_user and checkinfo[0].password==input_password:
            self.response.headers.add_header('Set-Cookie', 'name=%s; Path=/' % input_user)
            self.redirect("/welcome")
        else:
            self.render_login("Invalid Login")

class logoff(Handler):
    def get(self):
        input_user=''
        hashpassword=''
        self.response.headers.add_header('Set-Cookie', 'name=%s; Path=/' % input_user)
        self.response.headers.add_header('Set-Cookie', 'password=%s; Path=/' % hashpassword)
        self.redirect("/signup")


class welcome(Handler):
    def get(self):
        user=self.request.cookies.get('name')
        self.response.write("Welcome "+ user)

class Pic(db.Model):
    title=db.StringProperty(required=True)
    pic=db.TextProperty(required=True)
    date=db.DateTimeProperty(auto_now_add=True)
    coords=db.GeoPtProperty()
class blogentry(db.Model):
    subject=db.StringProperty(required=True)
    content=db.TextProperty(required=True)
    dateid=db.DateTimeProperty(auto_now_add=True)
    def as_dict(self):
        time_fmt = '%c'
        d = {'subject': self.subject,
             'content': self.content,
             'created': self.dateid.strftime(time_fmt)}
        return d

class useraccounts(db.Model):
    user=db.StringProperty(required=True)
    password=db.StringProperty(required=True)
    date = db.DateTimeProperty(auto_now_add=True)

cache={}
def front_art():
    key='front'
    if key in cache:
        pics=cache[key]
    else:
        pics = db.GqlQuery("select * from Pic order by date DESC")
        pics = list(pics)
        cache[key]=pics
    return pics
class ascii(Handler):
    def render_front(self,title="",pic="",error=""):
        pics=front_art()
        hascoords=[coordval.coords for coordval in pics if coordval.coords!=None]
        img=None
        if hascoords:
            img=gmaps_img(hascoords)
        self.render('ascii.html',title=title,pic=pic,error=error,pics=pics,img=img)
    def get(self):
        self.render_front()
    def post(self):
        title=self.request.get("title")
        pic=self.request.get("asciipic")
        coord=get_coords(self.request.remote_addr)
        if title and pic:
            a=Pic(title=title,pic=pic)
            if coord:
                a.coords=coord
            a.put()
            self.render_front()
        else:
            self.render_front(title=title, pic=pic,error="Please include both values")
class blog(Handler):
    def get(self,subject="",content="",error=""):
        entries=db.GqlQuery("select * from blogentry order by subject DESC")
        if self.request.url.endswith('.json'):
            return self.render_json([entry.as_dict() for entry in entries])
        else:
            self.render('blog.html', subject=subject, content=content, error=error, entries=entries)
class blogselectedvalue(Handler):
    def get(self,id):
        entry=db.GqlQuery("select * from blogentry where __key__=KEY('blogentry',:1)",int(id))

        if not entry:
            self.error(404)
            return
        if self.request.url.endswith('.json'):
            return self.render_json([val.as_dict() for val in entry])
        else:
            self.render('blogentry.html', entry=entry)
class newblogpost(Handler):
    def render_front(self,subject="",content="",error=""):
        self.render('newblogpost.html',subject=subject,content=content,error=error)
    def get(self):
        self.render_front()
    def post(self):
        subject=self.request.get("subject")
        content=self.request.get("content")
        if subject and content:
            b=blogentry(subject=subject,content=content)
            b.put()
            self.redirect('/blog/'+str(b.key().id()))
        else:
            self.render_front(subject=subject,content=content,error="Please enter both values")


app = webapp2.WSGIApplication([
    ('/', MainPage),("/thanks",Thanks),("/rot13",rot13),("/signup",usersignup),("/welcome",welcome),("/login",login),
    ("/logout", logoff),("/ascii",ascii),("/blog(?:.json)?",blog),("/blog/newpost",newblogpost),("/blog/([0-9]+)(?:.json)?",blogselectedvalue)], debug=True)
