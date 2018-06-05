#!/usr/bin/python

############################### Copycat Agent ###################################
#                                                                               #
#   Agent for the phpipam/pdns/dnsmasq solution.                                #
#                                                                               #
# Author: J Lyons                                                               #
# Created: 9/30/2016                                                            #
# Last Update: 11/7/2016                                                        #
#                                                                               #
#################################################################################

try:
    import os
    import sys
    import util
    import json
    import records
    import logging
    import traceback
    import exceptions
    import communicator
    import logging.handlers
    from os import mkdir
    from filters import Filter
    from urllib2 import URLError
    from dhkey import DiffieHellman
    from twisted.internet import reactor
    from twisted.python import log as tlog
    from sortedcontainers import SortedSet
    from twisted.application import service
    from twisted.web import resource, server
    from ConfigParser import SafeConfigParser
    from os.path import dirname, realpath, join, isdir
    from signal import signal, SIGTERM, SIGHUP, SIGINT
    from os.path import dirname, realpath, join, isdir, isfile
except ImportError:
    print(('\n' * 2).join(["Error importing a module:", '\t' + str(sys.exc_info()[1]), 'Install the module and try again.']))
    raise SystemExit(1)

# Location of config file
configFile = 'agent.cfg'

# Empty initialization of the master list
master = {'domains': '', 'ns_records': '', 'a_records': '', 'ptr_records': ''}

def shutdown(sigNum, frame):
    """
    Method run when shutdown is called.
    runs well.
    """
    reactor.stop()
    if log is not None:
        log.info('Agent has been shut down.')
    print ""
    return

class HelloResource(resource.Resource):
    isLeaf = True
    
    def render_GET(self, request):
        global filters
        if request.path == "/alive": # Status check
            request.responseHeaders.addRawHeader(b"content-type", b"application/json")
            return json.dumps({'success':True})
        else:
            request.setResponseCode(501)
            return ""
    
    def render_POST(self, request):
        global master, key, filters
        log.debug(request.path)
        
        if request.path == "/handshake": # Generates new key. All other POST bodies are encoded with this secret key.
            key.generateKey(long(request.content.getvalue()))
            log.debug(key.getKey())
            log.debug("Handshake complete. Secret key generated.")
            return str(key.publicKey)
        
        log.debug(util.decode(request.content.getvalue(), key.getKey()))
        reqJSON = json.loads(util.decode(request.content.getvalue(), key.getKey())) # Decode POST body 
        if request.path[:5] == "/init":
            if request.path == "/init":
                log.info("Master is online. Initial retrieval of DNS settings begun.")
                
                # Remove all conf files to create fresh ones
                try:
                    os.remove(ns_file)
                except:
                    log.warning("NS file (" + ns_file + ") has already been deleted.")
                try:
                    os.remove(a_file)
                except:
                    log.warning("A file (" + a_file + ") has already been deleted.")
                try:
                    os.remove(ptr_file)
                except:
                    log.warning("PTR file (" + ptr_file + ") has already been deleted.")
                
                # Create new conf files
                ns_f = open(ns_file, 'a')
                a_f = open(a_file, 'a')
                ptr_f = open(ptr_file, 'a')
                
                # Write headers to each new conf file
                ns_f.write("######### NS Records #########\n\n")
                a_f.write("######### A Records #########\n\n")
                ptr_f.write("######### PTR Records #########\n\n")
        
                ns_f.close()
                a_f.close()
                ptr_f.close()
                
                filters = {}
                return json.dumps({'success': True})
            # Endpoints to initialize each record type
            if request.path[5:] == '/ns':
                communicator.receiveFromFile(ns_file, reqJSON, filters)
                return json.dumps({'success': True})
            elif request.path[5:] == '/a':
                communicator.receiveFromFile(a_file, reqJSON, filters)
                return json.dumps({'success': True})
            elif request.path[5:] == '/ptr':
                communicator.receiveFromFile(ptr_file, reqJSON, filters)
                return json.dumps({'success': True})
        elif request.path[:4] == '/ns/':
            if request.path[4:] == 'delete':
                ns_records = communicator.fromJSON(reqJSON, log)['ns_records']
                
                communicator.logSet(ns_records, log, "- ")
                communicator.deleteFromFile(ns_records, ns_file, log)
                request.responseHeaders.addRawHeader(b"content-type", b"application/json")
                return json.dumps({'success': True})
            elif request.path[4:] == "add":
                ns_records = communicator.fromJSON(reqJSON, log)['ns_records']
                
                communicator.logSet(ns_records, log, "+ ")
                communicator.addToFile(ns_records, ns_file, filters, log)
                request.responseHeaders.addRawHeader(b"content-type", b"application/json")
                return json.dumps({'success': True})
            else:
                request.setResponseCode(501)
                return ""
        elif request.path[:3] == '/a/':
            if request.path[3:] == 'delete':
                a_records = communicator.fromJSON(reqJSON, log)['a_records']
                
                communicator.logSet(a_records, log, "- ")
                communicator.deleteFromFile(a_records, a_file, log)
                request.responseHeaders.addRawHeader(b"content-type", b"application/json")
                return json.dumps({'success': True})
            elif request.path[3:] == "add":
                a_records = communicator.fromJSON(reqJSON, log)['a_records']
                
                communicator.logSet(a_records, log, "+ ")
                communicator.addToFile(a_records, a_file, filters, log)
                request.responseHeaders.addRawHeader(b"content-type", b"application/json")
                return json.dumps({'success': True})
            else:
                request.setResponseCode(501)
                return ""
        elif request.path[:5] == '/ptr/':
            if request.path[5:] == 'delete':
                ptr_records = communicator.fromJSON(reqJSON, log)['ptr_records']
                
                communicator.logSet(ptr_records, log, "- ")
                communicator.deleteFromFile(ptr_records, ptr_file, log)
                request.responseHeaders.addRawHeader(b"content-type", b"application/json")
                return json.dumps({'success': True})
            elif request.path[5:] == "add":
                ptr_records = communicator.fromJSON(reqJSON, log)['ptr_records']
                
                communicator.logSet(ptr_records, log, "+ ")
                communicator.addToFile(ptr_records, ptr_file, filters, log)
                request.responseHeaders.addRawHeader(b"content-type", b"application/json")
                return json.dumps({'success': True})
            else:
                request.setResponseCode(501)
                return ""
        elif request.path == '/filters':
            log.debug("Filters:")
            filters[reqJSON['code']] = Filter(reqJSON['filter'])
            log.info("Added filter '" + reqJSON['code'] + "'")
            log.debug(json.dumps(reqJSON['filter']))
            request.responseHeaders.addRawHeader(b"content-type", b"application/json")
            return json.dumps({'success': True})
        elif request.path == '/reload':
            log.info("DNS settings up to date. Reloading.")
            util.execute("systemctl restart dnsmasq")
            log.debug("DNSMasq reloaded.")
            return json.dumps({'success': True})
        else:
            request.setResponseCode(501)
            return ""

if __name__ == '__main__':
    """
    main:
        - Initializes global key variable
        - Reads in configFile settings
        - Initializes logger
        - Requests handshake with master
        - Requests init with master
        - Starts server
    """
    global key, filters
    
    installPath = dirname(realpath(__file__))
    configFilePath = join(installPath, configFile)
    
    if not isfile(configFilePath):
        print 'CRITICAL: The ' + configFile + ' file is missing. It should be in ' + installPath + '/'
        exit(1)
    cfg = SafeConfigParser()
    cfg.read(configFilePath)
    
    # Read in config settings to gloabl variables
    section = 'Logging'
    completeLog = cfg.get(section, 'completeLog')
    errorLog = cfg.get(section, 'errorLog')
    logToConsole = cfg.getboolean(section, 'logToConsole')
    cfgLogLevel = cfg.get(section, 'cfgLogLevel')
    log_max_size = cfg.getint(section, 'log_max_size')
    log_max_backup = cfg.getint(section, 'log_max_backup')
 
    section = 'Settings'
    name = cfg.get(section, 'name')
    port = cfg.getint(section, 'port')
    home = "http://" + cfg.get(section, 'home')
    
    section = 'DNSMasq'
    dnsmasq = cfg.get(section, 'dnsmasq')
    ns_file = join(dnsmasq, cfg.get(section, 'ns_file'))
    a_file = join(dnsmasq, cfg.get(section, 'a_file'))
    ptr_file = join(dnsmasq, cfg.get(section, 'ptr_file'))
    
    filters = {} 
    key = DiffieHellman()
    
    # Add handler to system terminate signal
    signal(SIGINT, shutdown)
    signal(SIGHUP, shutdown)
    signal(SIGTERM, shutdown)

    #----- Logging Configuration ------#
    # Logging Levels:
    #	logging.CRITICAL
    #	logging.WARNING
    #	logging.INFO
    #	logging.DEBUG
    
    # Logger
    if cfgLogLevel == 'critical':
        logLevel = logging.CRITICAL
    elif cfgLogLevel == 'error':
        logLevel = logging.ERROR
    elif cfgLogLevel == 'warning':
        logLevel = logging.WARNING
    elif cfgLogLevel == 'debug':
        logLevel = logging.DEBUG  
    else:
        logLevel = logging.INFO
    
    # Name of log file
    installPath = dirname(realpath(__file__))
    logFile = join(installPath, 'log', completeLog + '.log')
    errFile = join(installPath, 'log', errorLog + '.log')
    if not isdir(join(installPath, 'log')):
        mkdir(join(installPath, 'log'))
              
    # Log size in Bytes
    #logSize = 1048576
    # Number of log files to keep
    #logBackupCount = 5
    # Text prior to message...which is a timestamp in this case. 
    logFormat = '[%(asctime)s] - %(levelname)s - %(message)s'
    #-------------------------------#
    
    log = logging.getLogger('copycat-agent')
    log.setLevel(logLevel)
    
    # Create custom handler to manage rotating logs and auto log cleanup
    mainHandler = logging.handlers.RotatingFileHandler(logFile, maxBytes=log_max_size, backupCount=log_max_backup)
    mainHandler.setFormatter(logging.Formatter(logFormat))
    
    # Create custom handler for the errors only
    errHandler = logging.handlers.RotatingFileHandler(errFile, maxBytes=log_max_size, backupCount=log_max_backup)
    errHandler.setFormatter(logging.Formatter(logFormat))
    errHandler.setLevel(logging.ERROR)
    
    # Create stream handler for logging to the console
    if logToConsole:
        stdHandler = logging.StreamHandler()
        stdHandler.setFormatter(logging.Formatter(logFormat))
        stdHandler.setLevel(logLevel)
        log.addHandler(stdHandler)
    
    # Add handlers to log instance
    log.addHandler(mainHandler)
    log.addHandler(errHandler)
    
    try:
        # try:
        key.generateKey(util.send_post(home + '/handshake',{'name': name, 'port': port, 'key': key.publicKey}, log))
        log.debug(key.getKey())
        log.info("Handshake complete. Secret key generated.")
        util.send_get(home + '/init', {'name': name, 'port': port}, log)
        # except URLError, err:
        #     log.warning("Could not call home: " + str(err.reason))
            
        reactor.listenTCP(port, server.Site(HelloResource()))
        log.info("Server started on port " + str(port))
        reactor.run()
    except:
        error = 'Failure: ' + str(sys.exc_info()[0])
        log.critical(error)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        error = ''.join('!! ' + line for line in lines)
        log.critical(error)
        exit(1)