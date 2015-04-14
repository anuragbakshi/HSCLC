import webapp2
import jinja2
import os
import re
import logging
import json
import time
import string
import cPickle
import random
from operator import attrgetter
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import mail
from google.appengine.api import memcache
from main import *

jinja_environment = jinja2.Environment(autoescape=True,
                                       loader=jinja2.FileSystemLoader(
                                           os.path.join(os.path.dirname(__file__), 'templates')),
                                       trim_blocks=True)

inuit_answers = ["samekip", "peggalep legvin", "nigammipeagen", "nigap epeikan", "enalaemmipeagen etten", "enalaen epeikan", "amiammemmipeagen", "legvinasaen apchenkrep", "samekinasaen peggalep samekip", "samekinasaen nigap samekip etten", "kakelenasaen amiammemmipeagen", "peggalenasaen peggalep samekip etten", "peggalenasaen enalaen epeikan", "apchenkrenasaen enalaen", "69", "131", "82", "93.5"]
inuit_val = [1,1,1,1,1,1,3,2,2,2,4,4,4,3,2,2,2,4]

vowel_answers = ["AA", "AAA", "AAAA", "A", "AE", "AEAEA", "AEA", "AEAE", "AI", "AIAIA", "AIA", "AIAI", "AOA", "AOAO", "AO", "AOAOA", "AUA", "AUAU", "AUAUA", "AU", "I", "U", "E", "O", "IEIE", "UIA", "AAE", "IIAAO"]
vowel_exceptions = ["UIA", "IEIE", "AAE", "IIAAO"]

music_answers = ["D", "C", "F", "G", "A", "B", "E"]

class FinalScores(db.Model):
    email = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    final_total = db.IntegerProperty(required=True)
    weeks_total = db.IntegerProperty(required=True)
    start = db.StringProperty(required=True)
    end = db.StringProperty(required=True)
    done = db.StringProperty(required=True, default="No")
    prob1 = db.StringProperty(required=False)
    prob2 = db.StringProperty(required=False)
    prob3 = db.StringProperty(required=False)



class SessionHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect('/sign_in')
        q = db.GqlQuery("SELECT * FROM FinalScores WHERE email = :member",member = user.email()).get()
        q.done = "Yes"
        q.put()

    def post(self):
        start = self.request.get('start')
        end = self.request.get('end')
        user = users.get_current_user()
        if not user:
                self.redirect('/sign_in')
        q = db.GqlQuery("SELECT * FROM Scores WHERE email = :member",member = user.email()).get()
        f = FinalScores(email=user.email(), final_total=q.total, weeks_total=q.total, start=start,done="No", end=end)
        f.put()
        # set session memcache
        memcache.add(key=user.email()+" end_time", value=end, time=10850)


class ChallengeHandler(webapp2.RequestHandler):
    def get(self):
        # start, end, eli, end_time
        user = users.get_current_user()
        if not user:
            self.redirect('/sign_in')
        else:
            start = True
            end = True
            eli = True
            end_time = ""
            # mem = memcache.get(user.email()+" ChallengeHandler")
            # if mem is None:
            q = db.GqlQuery("SELECT * FROM FinalScores WHERE email = :member",member = user.email()).get()
            if not q:
                start = False
                end = False
                guy = db.GqlQuery("SELECT * FROM Scores WHERE email = :member",member = user.email()).get()
                if guy.total < 15:
                    eli = False
            else:
                if q.done == "Yes":
                    start = False
                end_time = q.end
                    # memcache.add(key=user.email()+" ChallengeHandler", value=str(start)+" "+str(end)+" "+str(eli), time=10850)
                # else:
                #     vals = mem.split()
                #     start = vals[0]
                #     end = vals[1]
                #     eli = vals[2]
                #     mem = memcache.get(user.email()+" end_time")
                #     if mem is None:
                #         q = db.GqlQuery("SELECT * FROM FinalScores WHERE email = :member",member = user.email()).get()
                #         if not q:
                #             end_time = ""
                #         else:
                #             end_time = q.end
                #     else:
                #         end_time = mem

            values = {'start':start, 'end':end, 'eli':eli, 'end_time':'"'+end_time+'"'}
            template = jinja_environment.get_template('challenges.html.jinja')
            self.response.out.write(template.render(values))
    def post(self):
        user = users.get_current_user()
        if not user:
            self.redirect('/sign_in')
        q = db.GqlQuery("SELECT * FROM FinalScores WHERE email = :member",member = user.email()).get()
        if q.done == 'Yes':
            return
        inu_ans = []
        i = 1
        while i <= 18:
            inu_ans.append(self.request.get('1-'+str(i)))
            i += 1
        i = 1
        vowel_ans = []
        while i <= 28:
            vowel_ans.append(self.request.get('2-'+str(i)))
            i += 1
        i = 1
        music_ans = []
        while i <= 7:
            music_ans.append(self.request.get('3-'+str(i)))
            i += 1

        total = 0
        # grade inu below
        i = 0
        while i < 18:
            if inu_ans[i] == inuit_answers[i]:
                total += inuit_val[i]
            i += 1
        total = total*2

        # grade vowel below, don't double this problem
        i = 0
        while i < 24:
            if vowel_ans[i] == vowel_answers[i]:
                total += 1
            i += 1

        while i < 28:
            if vowel_ans[i] == vowel_answers[i] or vowel_ans[i] == vowel_exceptions[i-24]:
                total += 1
            i += 1

        # grade music below
        i = 0
        while i < 7:
            if music_ans[i] == music_answers[i]:
                total += 2
            i += 1

        q.done = "Yes"
        q.final_total = q.weeks_total+total
        q.put()
        self.redirect('/about')


