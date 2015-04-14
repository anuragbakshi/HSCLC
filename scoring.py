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


class Scores(db.Model):
    email = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    total = db.IntegerProperty(required=True, default=0)
    prob1 = db.StringProperty(required=True)
    prob2 = db.StringProperty(required=True)
    prob3 = db.StringProperty(required=True)
    prob4 = db.StringProperty(required=True)
    prob5 = db.StringProperty(required=True)
    prob6 = db.StringProperty(required=False, default="0"*50)
    prob7 = db.StringProperty(required=False, default="0"*50)
    prob8 = db.StringProperty(required=False, default="0"*50)


corpora_answers = [321450, 10, "more", 982, "super-individualistically", 17, "looked upon"]
corpora_tolerance = [{0: 5, 1: 4, 10: 3, 100: 2, 1000: 1},
                     {0: 7, 1: 2},
                     {0: 7},
                     {0: 7, 1: 5, 10: 3, 100: 1},
                     {0: 5},
                     {0: 9, 1: 2},
                     {0: 10}]

sg_answers = [2, 10, 9, 11, 12, 3, 5, 4, 6, 8, 1, 7, "'jigs.pa", "sdig.pa", "zhing",
              "Do I understand this farmer's writings?",
              "Those horse riders see us.", "Write to us!", "bdag.chos.kyi.shes.pa.thams.cad.go.'o|",
              "bdag.cag.mchod.pa.rnams.yui.kyi.zhing.pa.rnams.kyi.khyim.thams.cad.la.'bri.'o|",
              "mi.rnams.de.kyi.mchod.pa.rnams.'jigs.shig|"]
sg_tolerance = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 3, 3, 3, 3, 3, 4, 4, 4]

liol_answers = ["job center", "arcade", "primetime", "screwdriver", "aisle of church", "weak coffee", "bathroom scale",
                "beauty contest", "dress", "repetitive", "unique", "slow down", "up", "guide", "coaster",
                "sutoppu", "botoru", "shiito", "teeburu"]
liol_tolerance = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 3, 3, 3, 3]

nim_answers = ["tapr", "fsoh", 69, 42, "amiy fsohifsohi rit tthoyi fsohitapr", "rit tthoyi tapr",
               "amiy tthoyi fsoh"]
nim_tolerance = [3, 3, 4, 4, 8, 4, 4]

lev_answers = [4, 19871831, 202, 192, 1584, 277]
lev_tolerance = [{0: 3},
                 {0: 8, 1: 7, 10: 6, 100: 5, 1000: 4, 10000: 3, 100000: 2, 1000000: 1},
                 {0: 7, 1: 5, 5: 3, 25: 1},
                 {0: 10, 1: 7, 5: 4, 25: 1},
                 {0: 9, 1: 7, 5: 5, 25: 3, 125: 1},
                 {0: 13, 1: 9, 5: 5, 25: 1}]

cym_answers = ["Italy","Iceland","Jordan","Germany","Korea South","Thailand","Tuvalu","Ukraine","United Kingdom",
               "Poland"]
cym_tolerance = [1,1,1,1,1,1,1,1,1,1]

cl_answers = ['red', 'green', 'white', 'yellow', 'white', 'black', 'yellow', 'green', 'blue', 'green', 'red', 'white', "yi'", "bu'ti", "so'a", "so'a", "si'be", "si'be", "ii", "pupu", "nyian","nyian", "ii", "ii"]

list_parse = {1: corpora_answers, 2: sg_answers, 3: cym_answers, 4: lev_answers, 5: liol_answers,6: nim_answers,7:cl_answers}


class Problem:
    def __init__(self, text):
        self.text = text


def compare(word1, word2):  # uses the classical DP substring-table method, O(n^2)
    m = len(word1)
    n = len(word2)  #lengths of words

    dists = []  #table array of values

    row1 = []
    for i in range(n + 1):
        row1.append(i)
    dists.append(row1)  #first row

    for i in range(1, m + 1):  #calculating row by row, word1 vertical, word2 horizontal
        row = []
        row.append(dists[i - 1][0] + 1)  #first column

        for j in range(1, n + 1):  #filling in other cells
            if word1[i - 1] == word2[j - 1]:
                row.append(dists[i - 1][j - 1])
            else:
                row.append(min(dists[i - 1][j - 1], dists[i - 1][j], row[j - 1]) + 1)

        dists.append(row)  #adding row

    return dists[m][n]

def isQueryEmpty(q):
        count = 0
        for e in q:
                count = count +1
        if count > 0:
                return False
        return True
     

class ChallengeSystem(webapp2.RequestHandler):
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

                q = db.GqlQuery("SELECT * FROM Scores WHERE email = :member",member = user.email()).get()
                if q:
                    prob6 = (q.prob6+('0 '*50)).split()
                    prob7 = (q.prob7+('0 '*50)).split()
                    prob8 = (q.prob8+('0 '*50)).split()
                    values = {'prob6':prob6, 'prob7':prob7, 'prob8':prob8}
                    template = jinja_environment.get_template('challenges.html.jinja')
                    self.response.out.write(template.render(values))

                if not q:
                    prob6 = ('0 '*50).split()
                    prob7 = ('0 '*50).split()
                    prob8 = ('0 '*50).split()
                    values = {'prob6':prob6, 'prob7':prob7, 'prob8':prob8}
                    template = jinja_environment.get_template('challenges.html.jinja')
                    self.response.out.write(template.render(values))

    def post(self):
        user = users.get_current_user()
        # input all user answers here i think this should work
        ans = self.request.get('ans').strip()
        prob = int(self.request.get('prob'))
        prob_num = int(self.request.get('prob_num'))
        points = 0
        correct = False
        prob_num = prob_num - 1
        tries = 0
        memtries = memcache.get(user.email()+" "+str(prob)+" "+str(prob_num))
        if memtries is not None and int(memtries) <= 0:
            correct = True
            tries = -1
        else:
            # check input here
            if prob == 1:
                if type(corpora_answers[prob_num]).__name__ == 'str':
                    if corpora_answers[prob_num] == ans:
                        points = corpora_tolerance[prob_num][0]
                        correct = True
                elif ans.isdigit():
                    ans = int(ans)
                    diff = abs(corpora_answers[prob_num] - ans)
                    if diff == 0:
                        correct = True
                    for tol in corpora_tolerance[prob_num].items():
                        if diff <= tol[0]:
                            points = tol[1]
                            break


            elif prob == 2:

                if type(sg_answers[prob_num]).__name__ == 'str':
                    if sg_answers[prob_num] == ans:
                        points = sg_tolerance[prob_num]
                        correct = True

                    elif prob_num == 15 and compare(sg_answers[prob_num].split(),ans.split())<=1:
                        points = 1

                    elif prob_num == 16 and compare(sg_answers[prob_num].split(),ans.split())<=1:
                        points = 1

                    elif prob_num == 17 and compare(sg_answers[prob_num].split(),ans.split())<=1:
                        points = 1

                    elif prob_num == 18 and compare(sg_answers[prob_num].split('.'),ans.split('.'))==1:
                        points = 2
                    elif prob_num == 18 and compare(sg_answers[prob_num].split('.'),ans.split('.'))==2:
                        points = 1

                    elif prob_num == 19 and compare(sg_answers[prob_num].split('.'),ans.split('.'))==1:
                        points = 2
                    elif prob_num == 19 and compare(sg_answers[prob_num].split('.'),ans.split('.'))==2:
                        points = 1

                    elif prob_num == 20 and compare(sg_answers[prob_num].split('.'),ans.split('.'))==1:
                        points = 2
                    elif prob_num == 20 and compare(sg_answers[prob_num].split('.'),ans.split('.'))==2:
                        points = 1
                elif ans.isdigit():
                    ans = int(ans)
                    if ans == sg_answers[prob_num]:
                        points = sg_tolerance[prob_num]
                        correct = True
            elif prob == 3:
                if cym_answers[prob_num] == ans:
                        points = cym_tolerance[prob_num]
                        correct = True
            elif prob == 4 and ans.isdigit():
                ans = int(ans)
                logging.warning(str(ans))
                diff = abs(lev_answers[prob_num] - ans)
                for tol in lev_tolerance[prob_num].items():
                    if diff == 0:
                        points = tol[1]
                        correct = True
                        break
                    elif diff <= tol[0]:
                        points = tol[1]
                        break

            elif prob == 5:
                if liol_answers[prob_num] == ans:
                        points = liol_tolerance[prob_num]
                        correct = True

            elif prob == 6:
                if type(nim_answers[prob_num]).__name__ == 'str':
                    ans = ans.strip()
                    diff = compare(ans.split(), nim_answers[prob_num].split())
                    if nim_answers[prob_num] == ans:
                        points = nim_tolerance[prob_num]
                        correct = True
                    elif diff == 1 and prob_num == 4:
                        points = 5
                    elif diff == 2 and prob_num == 4:
                        points = 2
                    elif diff == 1 and prob_num == 5:
                        points = 1
                    elif diff == 1 and prob_num == 6:
                        points = 1 
                elif ans.isdigit():
                    ans = int(ans)
                    if nim_answers[prob_num] == ans:
                        points = nim_tolerance[prob_num]
                        correct = True

            elif prob == 7:
                if cl_answers[prob_num] == ans:
                        points = 1
                        correct = True

            elif prob == 8:
                if prob_num == 0:
                    ans = ans.strip()
                    if ans == '29':
                        points = 3
                        correct = True
                elif prob_num == 1:
                    ans = ans.lower()
                    if 'walk' in ans or 'go' in ans or 'move' in ans:
                        points = 2
                        correct = True
                elif prob_num == 2:
                    ans = ans.lower()
                    if 'face' in ans or 'turn' in ans:
                        points = 2
                        correct = True
                elif prob_num == 3:
                    ans = ans.lower()
                    if 'cross' in ans or 'intersection' in ans:
                        points = 2
                        correct = True
                elif prob_num == 4:
                    ans = ans.lower()
                    if 'until' in ans or 'to' in ans:
                        points = 2
                        correct = True
                elif prob_num == 5:
                    ans = ans.lower()
                    if 'left' in ans:
                        points = 2
                        correct = True
                elif prob_num == 6:
                    ans = ans.lower()
                    if 'west' in ans:
                        points = 2
                        correct = True
                elif prob_num == 7:
                    ans = ans.lower()
                    if '20' in ans and 'wugchy' in ans and 'xylywbu' in ans:
                        points = 3
                        correct = True
                elif prob_num == 8:
                    ans = ans.lower()
                    if 'bumnu yf' in ans and 'wugchy' in ans and '3' in ans and 'wlot' in ans:
                        points = 3
                        correct = True
                elif prob_num == 9:
                    ans = ans.lower()
                    if 'buau zlyhny' in ans and 'hilny' in ans:
                        points = 3
                        correct = True

            


            # answer validation stops here

            q = db.GqlQuery("SELECT * FROM Scores WHERE email = :member", member=user.email()).get()
            new_score = None
            if not q:
                new_score = Scores(email=user.email(), total=points,
                                   prob1=generate_prob_string(1, prob, len(list_parse[1]), prob_num, points,correct)[0],
                                   prob2=generate_prob_string(2, prob, len(list_parse[2]), prob_num, points,correct)[0],
                                   prob3=generate_prob_string(3, prob, len(list_parse[3]), prob_num, points,correct)[0],
                                   prob4=generate_prob_string(4, prob, len(list_parse[4]), prob_num, points,correct)[0],
                                   prob5=generate_prob_string(5, prob, len(list_parse[5]), prob_num, points,correct)[0],
                                   prob6=generate_prob_string(6, prob, len(list_parse[6]), prob_num, points,correct)[0],
                                   prob7=generate_prob_string(7, prob, len(list_parse[7]), prob_num, points,correct)[0],
                                   prob8=generate_prob_string(8, prob, 10, prob_num, points,correct)[0])
                new_score.put()
                tries = 2
                if correct:
                    tries = 0

            else:
                arr = None
                if prob == 1:
                    arr = gen_dup(q.prob1,prob_num,points,correct)
                    q.prob1= arr[0]
                    tries= int(arr[1])
                elif prob == 2:
                    arr = gen_dup(q.prob2,prob_num,points,correct)
                    q.prob2= arr[0]
                    tries= int(arr[1])
                elif prob == 3:
                    arr = gen_dup(q.prob3,prob_num,points,correct)
                    q.prob3= arr[0]
                    tries= int(arr[1])
                elif prob == 4:
                    arr = gen_dup(q.prob4,prob_num,points,correct)
                    q.prob4= arr[0]
                    tries= int(arr[1])
                elif prob == 5:
                    arr = gen_dup(q.prob5,prob_num,points,correct)
                    q.prob5= arr[0]
                    tries= int(arr[1])
                elif prob == 6:
                    arr = gen_dup(q.prob6,prob_num,points,correct)
                    q.prob6= arr[0]
                    tries= int(arr[1])
                elif prob == 7:
                    arr = gen_dup(q.prob7,prob_num,points,correct)
                    q.prob7= arr[0]
                    tries= int(arr[1])
                elif prob == 8:
                    arr = gen_dup(q.prob8,prob_num,points,correct)
                    q.prob8= arr[0]
                    tries= int(arr[1])
                if tries >= 0:
                    q.total = getPoints(q.prob1)+getPoints(q.prob2)+getPoints(q.prob3)+getPoints(q.prob4)+getPoints(q.prob5)+getPoints(q.prob6)+getPoints(q.prob7)+getPoints(q.prob8)
                q.put()

            if new_score is None:
                new_score = q

            memcache.set(user.email()+" scores", str(new_score.total)+" "+str(getPoints(new_score.prob1))+
                         " "+str(getPoints(new_score.prob2))+" "+str(getPoints(new_score.prob3))+" "+
                            str(getPoints(new_score.prob4))+" "+str(getPoints(new_score.prob5))+" "+
                                str(getPoints(new_score.prob6))+" "+str(getPoints(new_score.prob7))+" "+str(getPoints(new_score.prob8)), time=300)

            memcache.set(user.email()+" "+str(prob)+" "+str(prob_num), str(tries), time=300)

        if correct:
            output={'points':points,'correct':'Yes', 'tries':str(tries)}
        else:
            output={'points':points,'correct':'No', 'tries':str(tries)}
        output=json.dumps(output)
        self.response.out.write(output)


def getPoints(values):
    score_list = values.split()
    i = 0
    points = 0
    while i < len(score_list):
        points = points + int(score_list[i])
        i = i + 2
    return points


def gen_dup(string, prob_num, points, correct):
    score_str = string.split()
    if len(score_str) < 50:
        string = string + " 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0  "
        score_str = string.split()
    orig_score = score_str[prob_num*2]
    if int(score_str[prob_num*2+1]) < 3:
        if points >= int(score_str[prob_num*2]):
            score_str[prob_num*2] = str(points)
        score_str[prob_num*2+1] = str(int(score_str[prob_num*2+1])+1)
    else:
        return [string, '-1']
    if correct:
        score_str[prob_num*2+1] = '3'
    #logging.info(score_str[prob_num*2+1])
    gen = ""
    i = 0
    while i < len(score_str):
        gen += str(score_str[i])+" "
        i += 1
    return [gen, str(3-int(score_str[prob_num*2+1])), orig_score]

def generate_prob_string(prop, q_num, leng, prob_num, points, correct):
    i = 0
    gen = ""
    if prop == q_num:
        while i < leng:
            if i == prob_num:
                if correct:
                    gen = gen + str(points) + " 3 "
                else:
                    gen = gen + str(points) + " 1 "
            else:
                gen = gen + "0 0 "
            i = i + 1
    else:
        while i < leng:
            gen = gen + "0 0 "
            i = i + 1
    if correct:
        return [gen, '-1']
    else:
        return [gen, '2']
