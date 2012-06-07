"""
    Secure user infos
"""

# Modules
import os
import sys

# get setting id
settingId = sys.argv[ 1 ]

# check id setting
if settingId not in "username|password":
    raise "Cine-Passion::useraccount: %r" % sys.argv

# Modules General
from hashlib import sha1
from base64 import b64encode

# Modules XBMC
import xbmc
import xbmcvfs
from xbmcaddon import Addon


# get scraper object
AddonId = "metadata.media.passion.org"
Addon   = Addon( AddonId )

# set variables
token   = Addon.getSetting( "token" )
token64 = Addon.getSetting( "token64" )
login   = Addon.getSetting( "username" )
passw   = Addon.getSetting( "password" )

if settingId == "username":
    default = login
    heading = Addon.getLocalizedString( 30003 )
    hidden  = False
elif settingId == "password":
    default = passw
    heading = Addon.getLocalizedString( 30004 )
    hidden  = True

# condition pour mettre a jour la base
UpdateUserDB = False

# initialize Keyboard
kb = xbmc.Keyboard( default, heading, hidden )
# optional hidden pass
kb.setHiddenInput( hidden )
# call Keyboard
kb.doModal()
# si confirmation on continue les changement
if kb.isConfirmed():
    # recup du text
    text = kb.getText()
    # si le text est pas vide et pas pareil que le default ou pas de token, on change
    if text:# and ( text != default or not hasToken ):
        # set our codes
        if settingId == "username":
            token = sha1( text.lower() + passw ).hexdigest()
            tokenb64 = b64encode( text )
            login = text
            if not passw:
                xbmc.executebuiltin( "Action(Down)" )
        else:
            token = sha1( login.lower() + text ).hexdigest()
            tokenb64 = b64encode( login )
            passw = text
        # save cached settings infos
        Addon.setSetting( "token", token )
        Addon.setSetting( "tokenb64", tokenb64 )
        # save setting for visible infos
        Addon.setSetting( settingId, text )
        UpdateUserDB = True
# reset hidden input
kb.setHiddenInput( False )


if UpdateUserDB:
    # Modules General
    import time
    # temps du depart
    t1 = time.time()
    from re import findall, sub
    from urllib import quote_plus

    # chemin des settings de l'user
    settingsXML = os.path.join( xbmc.translatePath( Addon.getAddonInfo( "path" ) ), "resources", "settings.xml" )
    #print settingsXML
    # formation du settings.xml en une seul ligne
    strSettings = "<settings>"
    for id in sorted( findall( 'id="(.*?)"', open( settingsXML ).read() ) ):
        if   id == "username": value = login
        elif id == "password": value = passw
        elif id == "token":    value = token
        elif id == "tokenb64": value = tokenb64
        else: value = Addon.getSetting( id )
        strSettings += '<setting id="%s" value="%s" />' % ( id, value )
    strSettings += "</settings>"

    # commande sql
    sql_update = "UPDATE path SET strSettings='%s' WHERE strScraper='%s'" % ( strSettings, AddonId )
    # execution de l'update
    ok = xbmc.executehttpapi( "ExecVideoDatabase(%s)" % quote_plus( sql_update ) ).replace( "<li>", "" )
    # print infos dans le output, mais enleve les infos secrets |username|tokenb64
    print "%s: ExecVideoDatabase(%s)" % ( ok, sub( '(id="(password|token)" value=)"(.*?)"', '\\1"****"', sql_update ) )

    from xml.dom.minidom import parseString
    try:
        dom = parseString( strSettings )
        strSettings = dom.toprettyxml( indent='    ', encoding="utf-8" )
        strSettings = strSettings.replace( '<?xml version="1.0" encoding="utf-8"?>\n', '' )
        settingsXML = xbmc.translatePath( Addon.getAddonInfo( "profile" ).rstrip( "/" ) + "/settings.xml" )
        if not xbmcvfs.exists( os.path.dirname( settingsXML ) ): os.makedirs( os.path.dirname( settingsXML ) )
        tmp = settingsXML + ".tmp"
        file( tmp, "wb" ).write( strSettings )
        print xbmcvfs.copy( tmp, settingsXML )
    except:
        from traceback import print_exc
        print_exc()
    #print sub( '(id="(password|token)" value=)"(.*?)"', '\\1"****"', strSettings )
    # print le temps que cela a pris
    print time.time() - t1
