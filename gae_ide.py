import cgi
import os
import sys
import StringIO

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template

class File(db.Model):
  author = db.UserProperty()
  content = db.StringProperty(multiline=True)
  file_name = db.StringProperty()
  creation_date = db.DateTimeProperty(auto_now_add=True)

class MainPage(webapp.RequestHandler):
  def get(self):
    files_query = File.all().order('-creation_date')
    files = files_query.fetch(10)
    for f in files:
      f.id = f.key().id()
    if users.get_current_user():
      url = users.create_logout_url(self.request.uri)
      url_linktext = 'Logout'
    else:
      url = users.create_login_url(self.request.uri)
      url_linktext = 'Login'

    template_values = {
      'files': files,
      'url': url,
      'url_linktext': url_linktext,
      }

    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, template_values))
    
class EditPage(webapp.RequestHandler):
  def get(self):
    my_id = self.request.get('id')
    if my_id == 'new':
        my_file = File()
    else:
        my_file = File.get_by_id(int(my_id))

    SAVEDOUT = sys.stdout
    
    try:
      content = my_file.content.strip()
      capture = StringIO.StringIO()
      sys.stdout = capture
      
      exec(content)

      out = str(capture.getvalue())

      
      exception = 'No error found, try harder'
    except Exception, e:
      exception = e
      out = 'Exception occurred see below'
    finally:
      sys.stdout = SAVEDOUT
      
    template_values = {
      'id': my_id,
      'file': my_file,
      'output': out,
      'exception': exception
    }
    path = os.path.join(os.path.dirname(__file__), 'edit.html')
    self.response.out.write(template.render(path, template_values))

class Gae_Ide(webapp.RequestHandler):
  def post(self):
     my_id = self.request.get('id')
     if my_id == 'new':
       
       my_file = File()
     else:
        my_file = File.get_by_id(int(my_id))
     if users.get_current_user():
       my_file.author = users.get_current_user()

     my_file.content = self.request.get('content')
     my_file.file_name = self.request.get('file_name')
     my_file.put()
     self.redirect('/edit?id=' + str(my_file.key().id()))

application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/sign', Gae_Ide),
                                      ('/edit', EditPage)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
