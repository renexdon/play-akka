from xml.dom.minidom import Document
import ConfigParser
import re
import sys,os,inspect

config = ConfigParser.ConfigParser()
akka = {};

#option comes in looking something like: akka.stm.service
#this function splits option by "." and uses each part as a key to a map.
#when the final item in the split option is found, its value is pulled from the config.
#the above ends up looking like {"akka":{"stm":{"service":"on"}}}
def parseOption(option, section):
    parts = option.split(".")
    if(re.search("^akka.log", option)):
        parts = parts[1:]
    length = len(parts)
    previousDict = akka
    count = 0
    for p in parts:
        count = count + 1
        if count != length:
            if previousDict.has_key(p) != True:
                previousDict[p] = {}
            previousDict = previousDict[p]
        else:
            previousDict[p] = config.get(section, option)

            
#takes a dict like: {"akka":{"stm":{"service":"on"}}}
#and turns it into <akka><stm>service=on</stm></akka>
#this is done through recursive calls.  The tab count is used to make the output look pretty,
#and it should incremented with each call
def toXML(d, tabCount):
    xml = ""
    stack = []
    
    ### begin cosmetics ###
    tabs = ""
    if tabCount > 0:
        for i in range(tabCount):
            tabs += "\t"
    ### end cosmetics ###
    
    for item in d.items():
        key, value = item
        if isinstance(value, dict):
            stack.append(item)
        else:
            if value != "on" and value != "off":
                value = '"' + value + '"'
            xml = xml + tabs + key + '=' + value + '\n'
    while(len(stack) > 0):
        key, value = stack.pop()
        xml = xml + tabs + "<" + key + ">\n" + toXML(value, tabCount + 1) + tabs + "</" + key + ">\n\n"
    return xml

def createAkkaConf():
    shutil.copyfile(os.path.join(application_path, "conf/application.conf"), os.path.join(tempfile.gettempdir(), "application.conf"))
    f = open(os.path.join(tempfile.gettempdir(), "application.conf"))
    text = f.read()
    f.close()
    f = open(os.path.join(tempfile.gettempdir(), "application.conf"), "w")
    f.write("[PlayConfig]\n")
    f.write(text)
    f.close()
    config.readfp(open(os.path.join(tempfile.gettempdir(), "application.conf")))
    for section in config.sections():
        for option in config.options(section):
            if(re.search("^akka", option)):
                parseOption(option, section)
    xml = toXML(akka, 0)
    f = open(os.path.join(application_path, "conf/akka.conf"), "w")
    f.write("#THIS FILE IS AUTO-GENERATED FROM THE conf/application.conf FILE EVERY TIME 'play run' IS INVOKED\n")
    f.write(xml)
    f.close()



    
#reads the conf/application.conf file and looks for akka properties, like akka.stm.service=on
#and turns it into an akka.conf file that can be understood by akka - places it in the conf dir.
if play_command == 'akka:config':
    createAkkaConf()
    sys.exit(0)

#this is stolen from the play executable.  There is a bug in the current build that does not allow one to 
#override the if play_command == "run" section.  The only thing I'm adding here is a '-Dakka.home=...'
if play_command == "akka:run":
    createAkkaConf()
    global modules
    check_application()
    load_modules()
    do_classpath()
    disable_check_jpda = False
    if remaining_args.count('-f') == 1:
        disable_check_jpda = True
        remaining_args.remove('-f')
    do_java()
    print "~ Ctrl+C to stop"
    print "~ "
    if application_mode == 'dev':
        if not disable_check_jpda: check_jpda()
        java_cmd.insert(2, '-Xdebug')
        java_cmd.insert(2, '-Xrunjdwp:transport=dt_socket,address=%s,server=y,suspend=n' % jpda_port)
        java_cmd.insert(2, '-Dplay.debug=yes')
        java_cmd.insert(2, '-Dakka.config.file=' + os.path.join(application_path, "conf/akka.conf"))
    try:
        subprocess.call(java_cmd, env=os.environ)
    except OSError:
        print "Could not execute the java executable, please make sure the JAVA_HOME environment variable is set properly (the java executable should reside at JAVA_HOME/bin/java). "
        sys.exit(-1)
    print
    sys.exit(0)