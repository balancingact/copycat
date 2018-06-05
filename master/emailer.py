#!/usr/bin/python

################################## Emailer ######################################
#                                                                               #
#   Creates the body of the email for copycat error emailing.                   #
#                                                                               #
# Author: J Lyons                                                               #
# Created: 9/30/2016                                                            #
# Last Update: 11/7/2016                                                        #
#                                                                               #
#################################################################################

try:
    import sys
    import util
    import logging
    import smtplib
    import datetime
    import traceback
    from util import sendEmail
    from email.mime.text import MIMEText
except ImportError:
    print(('\n' * 2).join(["Error importing a module:", '\t' + str(sys.exc_info()[1]), 'Install the module and try again.']))
    raise SystemExit(1)

def getEmailBody(s):
    return """<!doctype html>
<html>
  <head>
    <style>
      /*! normalize.css v3.0.3 | MIT License | github.com/necolas/normalize.css */
      html{font-family: sans-serif;-ms-text-size-adjust: 100%;-webkit-text-size-adjust: 100%;}body{margin: 0;}article,aside,details,figcaption,figure,footer,header,hgroup,main,menu,nav,section,summary{display: block;}audio,canvas,progress,video{display: inline-block;vertical-align: baseline;}audio:not([controls]){display: none;height: 0;}[hidden],template{display: none;}a{background-color: transparent;}a:active,a:hover{outline: 0;}abbr[title]{border-bottom: 1px dotted;}b,strong{font-weight: bold;}dfn{font-style: italic;}h1{font-size: 2em;margin: 0.67em 0;}mark{background: #ff0;color: #000;}small{font-size: 80%;}sub,sup{font-size: 75%;line-height: 0;position: relative;vertical-align: baseline;}sup{top: -0.5em;}sub{bottom: -0.25em;}img{border: 0;}svg:not(:root){overflow: hidden;}figure{margin: 1em 40px;}hr{box-sizing: content-box;height: 0;}pre{overflow: auto;}code,kbd,pre,samp{font-family: monospace, monospace;font-size: 1em;}button,input,optgroup,select,textarea{color: inherit;font: inherit;margin: 0;}button{overflow: visible;}button,select{text-transform: none;}button,html input[type="button"],input[type="reset"],input[type="submit"]{-webkit-appearance: button;cursor: pointer;}button[disabled],html input[disabled]{cursor: default;}button::-moz-focus-inner,input::-moz-focus-inner{border: 0;padding: 0;}input{line-height: normal;}input[type="checkbox"],input[type="radio"] {box-sizing: border-box;padding: 0;}input[type="number"]::-webkit-inner-spin-button,input[type="number"]::-webkit-outer-spin-button{height: auto;}input[type="search"]{-webkit-appearance: textfield;box-sizing: content-box;}input[type="search"]::-webkit-search-cancel-button,input[type="search"]::-webkit-search-decoration{-webkit-appearance: none;}fieldset{border: 1px solid #c0c0c0;margin: 0 2px;padding: 0.35em 0.625em 0.75em;}legend{border: 0;padding: 0;}textarea{overflow: auto;}optgroup{font-weight: bold;}table{border-collapse: collapse;border-spacing: 0;}td,th{padding: 0;}

      /* Email CSS */
      html, body {
        margin: 0;
        padding: 0;
        height: 100vh;
      }
      body {
        background: #CCC;
      }

      .header {
        font-family: Georgia,Times,'Times New Roman',serif;
        font-size: 36px;
        color: white;
        width: 100%;
        background: #282b2e;
        text-align: center;
        text-shadow: black 2px 2px 2px;
        padding: 15px 0px;
        margin: 0;
        z-index: 1;
        position: relative;

      }

      .footer {
        font-family: Georgia,Times,'Times New Roman',serif;
        font-size: 36px;
        color: white;
        width: 100%;
        background: #282b2e;
        text-align: center;
        text-shadow: black 2px 2px 2px;
        padding: 15px 0px;
        left: 0px;
        bottom: 0px;
        position: relative;
        z-index: 1;
      }

      .body {
        width: 80%;
        margin-left: -40%;
        left: 50%;
        background: white;
        position: relative;;
        top: 0;
        bottom: 0;
        z-index: 0;
      }

      .content {
        font-family: sans-serif;
        color: #282b2e;
        width: 90%;
        margin: 0 auto;
      }
    </style>
    <script src="https://cdn.rawgit.com/google/code-prettify/master/loader/run_prettify.js"></script>
  </head>
  <body>
    <div class="body">
      <div class="header">
        <span>Error in phpipam</span>
      </div>
      <div class="content">
        <h2>The following error occured in copycat-master.py:</h2>
        <pre class="prettyprint">""" + s + """        </pre>
      </div>
      <div class="footer">
        <span>phpipam</span>
      </div>
    </div>
  </body>
</html>"""

if __name__ == '__main__':
    try:
        print "hello" + 3 + False
    except:
        error = 'Failure: ' + str(sys.exc_info()[0])
        exc_type, exc_value, exc_traceback = sys.exc_info()
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tracebk = ''.join('!! ' + line for line in lines)
        sendEmail(["joshua.lyons@byu.edu"], "[copycat] -- ERROR -- util.py", "joshua.lyons@byu.edu", getEmailBody(error + "\n" + tracebk))