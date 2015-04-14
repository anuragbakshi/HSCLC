import webapp2
import jinja2
import os
import re
import logging
import time
import string
import random
import cPickle
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import mail
from google.appengine.api import memcache
from scoring import *
from scoring_final import *

jinja_environment = jinja2.Environment(autoescape=True,
        loader = jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
        trim_blocks=True)

class MainPage(webapp2.RequestHandler):
        def get(self):
                user = users.get_current_user()
                values = {}
                if not user:
                        values = {'is_signed_in':False}
                else:
                        values = {'is_signed_in':True, 'nickname':user.nickname()}
                        
                template = jinja_environment.get_template('index.html.jinja')
                self.response.out.write(template.render(values))

class About(webapp2.RequestHandler):
        def get(self):
                template = jinja_environment.get_template('about.html.jinja')
                self.response.out.write(template.render())

class Rules(webapp2.RequestHandler):
        def get(self):
                template = jinja_environment.get_template('rules.html.jinja')
                self.response.out.write(template.render())

class Prizes(webapp2.RequestHandler):
        def get(self):
                template = jinja_environment.get_template('prizes.html.jinja')
                self.response.out.write(template.render())

class ChallengeFace(webapp2.RequestHandler):
        def get(self):
                template = jinja_environment.get_template('challenge_face.html.jinja')
                self.response.out.write(template.render())

class Resources(webapp2.RequestHandler):
        def get(self):
                template = jinja_environment.get_template('resources.html.jinja')
                self.response.out.write(template.render())

class Dashboard(webapp2.RequestHandler):
        def get(self):
                user = users.get_current_user()
                if not user:
                        self.redirect('/sign_in')
                if user:
                        mem = memcache.get(user.email())
                        if mem is None:
                            q = db.GqlQuery("SELECT * FROM User WHERE email = :member",member = user.email()).get()
                            if not q:
                                self.redirect('/register_form')
                            else:
                                memcache.add(key=user.email(), value="Yes", time=3600)
                if user:
                        template = jinja_environment.get_template('dashboard.html.jinja')
                        memscores = memcache.get(user.email()+" scores")
                        if memscores is None:
                            score = db.GqlQuery("SELECT * FROM Scores WHERE email = :member",member = user.email()).get()
                            if not score:
                                total = 0
                                total_prob2 = 0
                                total_prob1 = 0
                                total_prob3 = 0
                                total_prob4 = 0
                                total_prob5 = 0
                                total_prob6 = 0
                                total_prob7 = 0
                                total_prob8 = 0
                            else:
                                total = score.total
                                total_prob1 = getPoints(score.prob1)
                                total_prob2 = getPoints(score.prob2)
                                total_prob3 = getPoints(score.prob3)
                                total_prob4 = getPoints(score.prob4)
                                total_prob5 = getPoints(score.prob5)

                                total_prob6 = getPoints(score.prob6)
                                total_prob7 = getPoints(score.prob7)
                                total_prob8 = getPoints(score.prob8)
                                memcache.add(key=user.email()+" scores", value=str(total)+" "+str(total_prob1)
                                        +" "+str(total_prob2)+" "+str(total_prob3)+" "+str(total_prob4)+
                                        " "+str(total_prob5)+" "+str(total_prob6)+" "+str(total_prob7)+
                                        " "+str(total_prob8), time=300)
                        else:
                            list_score = memscores.split()
                            total = int(list_score[0])
                            total_prob1 = int(list_score[1])
                            total_prob2 = int(list_score[2])
                            total_prob3 = int(list_score[3])
                            total_prob4 = int(list_score[4])
                            total_prob5 = int(list_score[5])

                            total_prob6 = int(list_score[6])
                            total_prob7 = int(list_score[7])
                            total_prob8 = int(list_score[8])

                        values = {'user_name':user.nickname(),'total':total, 'prob1':total_prob1
                            ,'prob2':total_prob2,'prob3':total_prob3, 'prob4':total_prob4, 'prob5':total_prob5,
                            'prob6':total_prob6, 'prob7':total_prob7, 'prob8':total_prob8}
                        self.response.out.write(template.render(values))

def getPoints(values):
    score_list = values.split()
    i = 0
    points = 0
    while i < len(score_list):
        points = points + int(score_list[i])
        i = i + 2
    return points

class Organizers(webapp2.RequestHandler):
        def get(self):
                template = jinja_environment.get_template('organizers.html.jinja')
                self.response.out.write(template.render())


class GoogleCrawl(webapp2.RequestHandler):
        def get(self):
                template = jinja_environment.get_template('google248e68ea1abe161a.html')
                self.response.out.write(template.render())


class FAQ(webapp2.RequestHandler):
        def get(self):
                template = jinja_environment.get_template('faq.html.jinja')
                self.response.out.write(template.render())

class Lead:
    def __init__(self, rank, first, last, school, score, email, state):
        self.rank = rank
        self.name = first+" "+last
        self.school = school
        self.state = state
        self.email = email
        self.score = score

class Leader(webapp2.RequestHandler):
        def get(self):
            # memleader = memcache.get("leaderboard")
            # if memleader is None:
            #     query = db.GqlQuery("SELECT * FROM FinalScores ORDER BY final_total DESC")
            #     leaders = []
            #     i = 1
            #     for q in query:
            #         if i == 11:
            #             break
            #         person = db.GqlQuery("SELECT * FROM User WHERE email = :member",member = q.email).get()
            #         leaders.append(Lead(i, person.first_name, person.last_name, person.school, q.total, person.email,
            #                             person.state))
            #         i += 1
            #     #logging.info(cPickle.dumps(leaders))
            #     memcache.add(key="leaderboard", value=cPickle.dumps(leaders), time=250)
            # else:
            #     leaders = cPickle.loads(memleader)

            # values = {'leaders':leaders}
            template = jinja_environment.get_template('leaderboard.html.jinja')
            self.response.out.write(template.render())

class SignIn(webapp2.RequestHandler):
        def get(self):
                user = users.get_current_user()
                if not user:
                        self.redirect(users.create_login_url(dest_url='/sign_in'))
                else:
                        q = db.GqlQuery("SELECT * FROM User WHERE email = :member",member = user.email())
                        
                        if isQueryEmpty(q):                             
                                self.redirect('/register_form')
                        else:
                                self.redirect('/about')

                

class SignOut(webapp2.RequestHandler):
        def get(self):
                user = users.get_current_user()
                if user:
                        self.redirect(users.create_logout_url('/'))
                else:
                        self.redirect('/')

class User(db.Model):
        first_name = db.StringProperty(required=True)
        last_name = db.StringProperty(required=True)
        email = db.StringProperty(required=True)
        graduation = db.StringProperty(required=True)
        state = db.StringProperty(required=True)
        school = db.StringProperty(required=False)
        time_stamp = db.DateTimeProperty(auto_now_add=True)
        total = db.IntegerProperty(required=True, default=0)
        prob1 = db.BooleanProperty(required=True, default=False)
        prob2 = db.BooleanProperty(required=True, default=False)

class UserReg(webapp2.RequestHandler):
        def get(self):
                user = users.get_current_user()
                if not user:
                        self.redirect('/sign_in')
                template = jinja_environment.get_template('register_form.html.jinja')
                self.response.out.write(template.render())
        def post(self):
                user = users.get_current_user()
                email = user.email()
                first_name = self.request.get('first-name')
                last_name = self.request.get('last-name')
                graduation = self.request.get('graduation')
                state = self.request.get('state')
                school = self.request.get('school')

                # do this if all the data is validated and ready to be pushed to db
                u = User(first_name=first_name, last_name=last_name, graduation = graduation,
                 state = state, email=email, school=school)
                u.put()

                # now send email with welcome info
                mail.send_mail(sender="HSCLC Team <team@hss-linguistics-competition.appspotmail.com>",
              to=email,
              subject="HSCLC Registration Confirmation",
              body="""
Thanks for registering """+user.nickname()+""",

Our weekly challenges are expected to start on Monday, October 27th. You will have the chance to win great prizes and test your skills against fellow competitors from around the world!

In the meantime, to sharpen your linguistics, try your hand at some of the practice problems on our site at http://hsc.lc/resources.

Happy coding everyone!

Regards,
HSCLC Team
                                """)

                self.redirect('/')

class Redeem(webapp2.RequestHandler):
        def get(self):
            query = db.GqlQuery("SELECT * FROM Scores")
            for q in query:
                to_change = q.prob2.split()
                if to_change[2*15] != '3':
                    to_change[2*15+1] = '0'
                if to_change[2*16] != '3':
                    to_change[2*16+1] = '0'
                if to_change[2*17] != '3':
                    to_change[2*17+1] = '0'

                if to_change[2*18] != '4':
                    to_change[2*18+1] = '0'
                if to_change[2*19] != '4':
                    to_change[2*19+1] = '0'
                if to_change[2*20] != '4':
                    to_change[2*20+1] = '0'
                gen = ""
                for i in to_change:
                    gen = gen + i+" "
                q.prob2 = gen
                q.put()
            self.redirect('/')

def isQueryEmpty(q):
        count = 0
        for e in q:
                count = count +1
        if count > 0:
                return False
        return True



application = webapp2.WSGIApplication([
                ('/', MainPage),
                # ('/challenges', ChallengeHandler),
                ('/leaderboard', Leader),
                ('/dashboard', Dashboard),
                #('/organizers', Organizers),
                #('/forum', Forum),
                ('/sign_in', SignIn),
                ('/user_session', SessionHandler),
                ('/sign_out', SignOut),
                ('/register_form', UserReg)
        ], debug=True)
