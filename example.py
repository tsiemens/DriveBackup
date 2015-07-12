#!/usr/bin/env python
import sys
import DriveSync

if len( sys.argv ) < 2:
    print 'Supply some text to write as an argument'
    quit()

try:
    text = sys.argv[ 1 ]
    ser = DriveSync.DriveBackupManager( 'example.json~' )

    def printStoreData( ser ):
        print "Current data: '%s' @ version %d" % ( ser.localData(), ser.dataStore.version )

    printStoreData( ser )
    print "Writing '%s'" % text
    ser.writeLocalData( text )
    printStoreData( ser )

    ser.pushToDrive()
except DriveSync.StoreException as e:
    print str( e )
