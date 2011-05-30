import cgi
import os
import sys
import StringIO
import traceback
import logging

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template

class File(db.Model):
  author = db.UserProperty()
  content = db.StringProperty(multiline=True, required=True)
  file_name = db.StringProperty()
  creation_date = db.DateTimeProperty(auto_now_add=True)

class MainPage(webapp.RequestHandler):
  def get(self):
    files_query = File.all().order('-creation_date')
    author = users.get_current_user()
    files_query.filter("author", author)
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
      'python_version': sys.version,
      'server_software': os.environ['SERVER_SOFTWARE']
      }

    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, template_values))
    
class EditPage(webapp.RequestHandler):
  def get(self):
    my_id = self.request.get('id')
    if my_id == 'new':
        author = users.get_current_user()
        my_file = File(content='print 3 * "Hi"', author=author)
    else:
        my_file = File.get_by_id(int(my_id))

    SAVEDOUT = sys.stdout
    
    capture = StringIO.StringIO()

    sys.stdout = capture
    
    # extract the statement to be run
    statement = my_file.content
    logging.info('#'+statement)

    # the python compiler doesn't like network line endings
    statement = statement.replace('\r\n', '\n')

    # add a couple newlines at the end of the statement. this makes
    # single-line expressions such as 'class Foo: pass' evaluate happily.
    statement += '\n\n'

    # log and compile the statement up front
    exc = ''
    out = ''
    try:
      logging.info('Compiling and evaluating:\n%s' % statement)
      compiled = compile(statement, '<string>', 'exec')
      exec (compiled)
      out = str(capture.getvalue())
    except:
      exc = traceback.format_exc()

    finally:
      sys.stdout = SAVEDOUT
      
    template_values = {
      'id': my_id,
      'file': my_file,
      'output': out,
      'exception': exc
    }
    path = os.path.join(os.path.dirname(__file__), 'edit.html')
    self.response.out.write(template.render(path, template_values))

class Gae_Ide(webapp.RequestHandler):
  def post(self):
     my_id = self.request.get('id')
     if my_id == 'new':
       my_file = File(content = self.request.get('statement'))
     else:
       my_file = File.get_by_id(int(my_id))
       my_file.content = self.request.get('statement')
     if users.get_current_user():
       my_file.author = users.get_current_user()

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
