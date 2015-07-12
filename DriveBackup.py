import os
import json
import tempfile
import subprocess
from subprocess import PIPE

class DictJsonEncoder( json.JSONEncoder ):
    def default( self, obj ):
        return obj.__dict__

class Config( object ):
    def __init__( self, driveFile=None ):
        self.driveFile = driveFile

def newConfigFromDict( dct ):
    conf = Config()
    for k, v in dct.iteritems():
        setattr( conf, k, v )
    return conf

class StoreException( Exception ):
    def __init__( self, msg ):
        self.msg = msg
    def __str__( self ):
        return self.msg

class DataStore( object ):
    def __init__( self, version=0, data='' ):
        self.version = version
        self.data = data

def newDataStoreFromDict( dct ):
    return DataStore( version=dct[ 'version' ], data=dct[ 'data' ] )

class DriveBackupManager( object ):

    def __init__( self, localFile, driveFile=None, configFile=None ):
        ''' A copy of the drive file is stored in locaFile.
        If driveFile and configFile are not provided, driveFile will default to be the same name as
        localFile, at the root directory of Drive, minus any prefixed .'s'''
        self.localFile = localFile
        self.configFile = configFile

        defaultDriveFile = driveFile if driveFile is not None else os.path.split( localFile )[ 1 ]
        self.config = self._loadConfig( default=Config( driveFile=defaultDriveFile ) )

        self.dataStore = self._loadDataStore()
        self.tempfiles = {}

    def __del__( self ):
        for filename, delete in self.tempfiles.iteritems():
            if delete:
                os.remove( filename )

    def _openNewTmpFile( self ):
        tmpf = None
        try:
            tmpf = tempfile.NamedTemporaryFile( mode='w+b', delete=False )
            return tmpf
        finally:
            if tmpf:
                self.tempfiles[ tmpf.name ] = True

    def _toJson( self, obj, cls=DictJsonEncoder ):
        return json.dumps( obj, cls=cls )

    # These are meant to be overridable -----------
    def getSerializedDataStore( self ):
        return self._toJson( self.dataStore )

    def deserializeDataStore( self, filedata ):
        try:
            return newDataStoreFromDict( json.loads( filedata ) )
        except ValueError:
            return DataStore()

    def deserializeConfig( self, filedata ):
        try:
            return newConfigFromDict( json.loads( filedata ) )
        except ValueError:
            return Config()
    # --------------------------------------------


    def _loadFileObject( self, filename, deserializer, default ):
        if filename is not None and os.path.isfile( filename ):
            with open( filename, 'r' ) as f:
                return deserializer( f.read() )
        else:
            return default

    def _writeSerializedToFile( self, filename, serializer ):
        with open( filename, 'w' ) as f:
            f.write( serializer() )

    def _loadDataStore( self ):
        return self._loadFileObject( self.localFile,
                lambda d: self.deserializeDataStore( d ), DataStore() )

    def _writeDataStore( self ):
        self._writeSerializedToFile( self.localFile, lambda: self.getSerializedDataStore() )

    def _loadConfig( self, default=Config() ):
        return self._loadFileObject( self.configFile,
                lambda d: self.deserializeConfig( d ), default )

    def localData( self ):
        return self.dataStore.data

    def writeLocalData( self, data ):
        cachedData = self._loadDataStore()
        version = cachedData.version
        if cachedData.data != data:
            self.dataStore.data = data
            self._writeDataStore()

    def _fetchDataStoreFromDrive( self ):
        tmpfname = None
        with self._openNewTmpFile() as tmpf:
            tmpfname = tmpf.name
        proc = subprocess.Popen(
                [ 'skicka', 'download', self.config.driveFile, tmpfname ],
                stdout=PIPE, stderr=PIPE, stdin=PIPE )
        out, err = proc.communicate()
        if err:
            if 'not found on Drive' in err:
                return DataStore( version=self.dataStore.version ), None
        print out, err

        with open( tmpfname, 'r' ) as tmpf:
            dataStore = self.deserializeDataStore( tmpf.read() )
            return dataStore, tmpfname

    def _fetchValidRemoveDataStore( self ):
        driveStore, filename = self._fetchDataStoreFromDrive()
        if driveStore.version == self.dataStore.version:
            return driveStore
        else:
            beforeAfter = 'before' if driveStore.version < self.dataStore.version else 'later'
            self.tempfiles[ filename ] = False
            raise StoreException( 'Drive version (%d) is %s than local version (%d). '
                                  'Resolve the local file to version of the remote file '
                                  '( temporarily at %s )' % ( driveStore.version, beforeAfter,
                                  self.dataStore.version, filename ) )

    def pushToDrive( self ):
        driveStore = self._fetchValidRemoveDataStore()
        if driveStore.data != self.dataStore.data:
            self.dataStore.version += 1
            self._writeDataStore()

            print 'Pushing %s verison %d to Drive/%s' \
                % ( self.localFile, self.dataStore.version, self.config.driveFile )
            proc = subprocess.Popen(
                    [ 'skicka', 'upload', self.localFile, self.config.driveFile ],
                    stdout=PIPE, stderr=PIPE, stdin=PIPE )
            out, err = proc.communicate()
            print out, err
        else:
            print 'No changes to push'

    def pullFromDrive( self ):
        self._fetchValidRemoveDataStore()


