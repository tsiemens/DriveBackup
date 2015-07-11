import os
import json

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

class Metadata( object ):
    def __init__( self ):
        self.lastKnownDriveVersion = 0

def newMetadataFromDict( dct ):
    md = Metadata()
    md.lastKnownDriveVersion = dct[ 'lastKnownDriveVersion' ]

class DataStore( object ):
    def __init__( self, version=0, data='' ):
        self.version = version
        self.data = data

def newDataStoreFromDict( dct ):
    return DataStore( version=dct[ 'version' ], data=dct[ 'data' ] )

class DriveSynchronizer( object ):

    def __init__( self, localFile, driveFile=None, metadataFile=None, configFile=None ):
        ''' A copy of the drive file is stored in locaFile.
        If driveFile and configFile are not provided, driveFile will default to be the same name as
        localFile, at the root directory of Drive, minus any prefixed .'s.
        metadataFile defaults to localFile.metadata if not provided.'''
        self.localFile = localFile
        self.metadataFile = metadataFile if metadataFile is not None else \
                os.path.splitext( localFile )[ 0 ] + '.metadata'
        self.configFile = configFile

        defaultDriveFile = driveFile if driveFile is not None else os.path.split( localFile )[ 1 ]
        self.config = self._loadConfig( default=Config( driveFile=defaultDriveFile ) )

        self.metadata = self._loadMetadata()

        self.dataStore = self._loadDataStore()

    def _toJson( self, obj, cls=DictJsonEncoder ):
        return json.dumps( obj, cls=cls )

    # These are meant to be overridable -----------
    def getSerializedDataStore( self ):
        return self._toJson( self.dataStore )

    def deserializeDataStore( self, filedata ):
        return newDataStoreFromDict( json.loads( filedata ) )

    def getSerializedMetadata( self ):
        return self._toJson( self.metadata )

    def deserializeMetadata( self, filedata ):
        return newMetadataFromDict( json.loads( filedata ) )

    def deserializeConfig( self, filedata ):
        return newConfigFromDict( json.loads( filedata ) )

    def mergeFiles( self, localData, driveData ):
        return driveData
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

    def _loadMetadata( self ):
        return self._loadFileObject( self.metadataFile,
                lambda d: self.deserializeMetadata( d ), Metadata() )

    def _writeMetadata( self ):
        self._writeSerializedToFile( self.metadataFile, lambda: self.getSerializedMetadata() )

    def _loadConfig( self, default=Config() ):
        return self._loadFileObject( self.configFile,
                lambda d: self.deserializeConfig( d ), default )

    def localData( self ):
        return self.dataStore.data

    def writeLocalData( self, data ):
        cachedData = self._loadDataStore()
        version = cachedData.version
        if cachedData.data != data:
            version += 1
            self.dataStore.version = version
            self.dataStore.data = data
            self._writeDataStore()

    def pushToDrive( self ):
        pass

    def pullFromDrive( self ):
        pass


