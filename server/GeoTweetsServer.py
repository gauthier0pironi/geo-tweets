# -*- coding: utf-8 -*-
__author__ = 'gauthierpironi'

#   TODO : - connect to DB?
#          - allow query + search?
#          - batch mode
#          - multiple client
#          - detect broken connection
#

from twitter import *
from datetime import datetime

import sys
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import json
import urllib


######################################################################################
GeoTweets_version = '0.2'
max_number_of_tweet_to_send_to_client = 50
close_connection_after_max_number_of_tweets_sent_to_client = False
######################################################################################
MESSAGE_TYPE_TWEET = 'tweet'
MESSAGE_TYPE_ERROR = 'error'
######################################################################################


def writeTweets(wsHandler, language, keyword):
    auth = OAuth(
        consumer_key='xGXeoEyZFRbPcSRQQLoooNhMM',
        consumer_secret='kIiZCh8lIWLjP4PpyY0o1H79WyW1CAXtAcmBcqxYld6WxLYXbz',
        token='1949527872-JQmEZOPqPcyFPnNPQYcBqxQav6x0TqPHtSdI4IN',
        token_secret='SDZBATV34i8gBFlFApU77ZV1K0b2j896uE7xT9Q814ZYK'
    )

    number_of_tweets_received = 0
    number_of_geo_tweets_received = 0
    twitter_sample_stream = TwitterStream(auth=auth, domain='stream.twitter.com')
    # Expect at least one parameter: follow track locations

    # LANG + LOCATIONS = OK
    # PROBLEM FOR TRACK. HAVE TO REMOVE LOCATION...

    d = {}
    if keyword == '':
        d['locations'] = '-180,-90,180,90'
    else:
        d['track'] = keyword
    d['language'] = language

    try:
        print  datetime.now().strftime("%Y-%m-%d %H:%M"),'Connecting to twitter with language :',language,'and keyword :', keyword
        for msg in twitter_sample_stream.statuses.filter(**d):
            try:
                number_of_tweets_received = number_of_tweets_received + 1
                if 'text' in msg and msg['geo'] is not None:
                    tweet = msg['text'].encode('utf8')
                    d = datetime.strptime( msg['created_at'], '%a %b %d %H:%M:%S +0000 %Y');
                    time_created = d.strftime('%Y-%m-%d %H:%M:%S')
                    id = msg['id']
                    geo_data = msg['geo']
                    coordinates = geo_data['coordinates']
                    coordinates_x = coordinates[0]
                    coordinates_y = coordinates[1]
                    number_of_geo_tweets_received = number_of_geo_tweets_received + 1
                    message = {}
                    message['type'] = MESSAGE_TYPE_TWEET
                    message['text'] = tweet
                    message['x'] = coordinates_x
                    message['y'] = coordinates_y
                    message['time'] = time_created
                    message['id'] =  id
                    #send message to very nice client:
                    wsHandler.write_message(message)
                    #log tous les 100 tweets
                    if number_of_geo_tweets_received % 100 == 0:
                        print datetime.now().strftime("%Y-%m-%d %H:%M"),'Sent',number_of_geo_tweets_received,'geo tweets'
                        sys.stdout.flush()
                    if max_number_of_tweet_to_send_to_client <= number_of_geo_tweets_received:
                        print datetime.now().strftime("%Y-%m-%d %H:%M"),'Sent max number of',max_number_of_tweet_to_send_to_client,'tweets.'
                        sys.stdout.flush()
                        if close_connection_after_max_number_of_tweets_sent_to_client:
                            wsHandler.close(code = 1001, reason = 'Sent max number of ' + str(max_number_of_tweet_to_send_to_client) + ' tweets')
                        else:
                            message = {}
                            message['type'] = MESSAGE_TYPE_ERROR
                            message['code'] = '1001'
                            message['reason'] = 'Sent max number of ' + str(max_number_of_tweet_to_send_to_client) + ' tweets '
                            wsHandler.write_message(message)
                        break
            except Exception as e:
                print  datetime.now().strftime("%Y-%m-%d %H:%M"),'Erreur',str(e)
                sys.stdout.flush()
                message = {}
                message['type'] = MESSAGE_TYPE_ERROR
                message['code'] = '1003'
                message['reason'] = str(e)
                wsHandler.write_message(message)
                #wsHandler.close(code = 1002, reason = str(e))
    except Exception as e:
        print  datetime.now().strftime("%Y-%m-%d %H:%M"),'Erreur : ', str(e)
        sys.stdout.flush()
        message = {}
        message['type'] = MESSAGE_TYPE_ERROR
        message['code'] = '1003'
        message['reason'] = str(e)
        wsHandler.write_message(message)
        #wsHandler.close(code = 1002, reason = str(e))


class WSHandler(tornado.websocket.WebSocketHandler):
   # def open(self):

    def on_connection_close(self):
        print  datetime.now().strftime("%Y-%m-%d %H:%M"),'The client has disconnected'
        sys.stdout.flush()

    def on_message(self, message):
        print  datetime.now().strftime("%Y-%m-%d %H:%M"),'message received : %s' % message
        sys.stdout.flush()
        try:
            messageJSON = json.loads(str(message))
            language = messageJSON['language']
            keyword = messageJSON['keyword']
        except Exception as e:
            #self.close(code = 1002, reason = 'Wrong query : ' + message +' with error message : ' + str(e))
            print datetime.now().strftime("%Y-%m-%d %H:%M"),'Wrong query:',message,'with error message : ',str(e)
            sys.stdout.flush()
            message = {}
            message['type'] = MESSAGE_TYPE_ERROR
            message['code'] = '1003'
            message['reason'] = str(e)
            self.write_message(message)
        writeTweets(self, str(language),str(keyword))


    def on_close(self):
      print  datetime.now().strftime("%Y-%m-%d %H:%M"),'server closed'
      sys.stdout.flush()

    def check_origin(self, origin):
        print  datetime.now().strftime("%Y-%m-%d %H:%M"),'A client has connected from',origin
        sys.stdout.flush()
        return True
        #return origin == 'null'
     #   return origin.endswith("pironiga.no-ip.org")

application = tornado.web.Application([
    (r'/wsGeoTweets', WSHandler),
],)

if __name__ == '__main__':
    try:
        print datetime.now().strftime("%Y-%m-%d %H:%M"),'GeoTweets Server v'+GeoTweets_version+ ' is launching...'
        sys.stdout.flush()
        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(8888)
        tornado.ioloop.IOLoop.instance().start()
    except Exception as e:
        print  datetime.now().strftime("%Y-%m-%d %H:%M"),str(e)
        sys.stdout.flush()


