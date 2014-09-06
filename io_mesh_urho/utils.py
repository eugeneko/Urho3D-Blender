
#
# This script is licensed as public domain.
#

# http://docs.python.org/2/library/struct.html

from xml.etree import ElementTree as ET
from xml.dom import minidom
import os
import struct
import array
import logging

log = logging.getLogger("ExportLogger")


def enum(**enums):
    return type('Enum', (), enums)
PathType = enum(
    ROOT        = "ROOT",
    MODELS      = "MODE",
    ANIMATIONS  = "ANIM",
    TRIGGERS    = "TRIG",
    MATERIALS   = "MATE",
    TECHNIQUES  = "TECH",
    TEXTURES    = "TEXT",
    MATLIST     = "MATL",
    OBJECTS     = "OBJE",
    SCENES      = "SCEN")

# Options for file utils
class FOptions:
    def __init__(self):
        self.useStandardDirs = True
        self.fileOverwrite = False
        self.paths = {}
        self.exts = {
                        PathType.MODELS : "mdl",
                        PathType.ANIMATIONS : "ani",
                        PathType.TRIGGERS : "xml",
                        PathType.MATERIALS : "xml",
                        PathType.TECHNIQUES : "xml",
                        PathType.TEXTURES : "png",
                        PathType.MATLIST : "txt",
                        PathType.OBJECTS : "xml",
                        PathType.SCENES : "xml"
                    }
        self.preserveExtTemp = False


#--------------------
# File utilities
#--------------------

# Get a file path for the object 'name' in a folder of type 'pathType'
def GetFilepath(pathType, name, fOptions):

    # Get the root path
    rootPath = fOptions.paths[PathType.ROOT]

    # Append the relative path to get the full path
    fullPath = rootPath
    if fOptions.useStandardDirs:
        fullPath = os.path.join(fullPath, fOptions.paths[pathType])

    # Create the full path if missing
    if not os.path.isdir(fullPath):
        log.info( "Creating path {:s}".format(fullPath) )
        os.makedirs(fullPath)

    # Compose filename
    filename = name
    if type(filename) is list or type(filename) is tuple:
        filename = os.path.sep.join(filename)

    # Add extension to the filename, if present we can preserve the extension
    ext = fOptions.exts[pathType]
    if ext and (not fOptions.preserveExtTemp or os.path.extsep not in filename):
        filename += os.path.extsep + ext
        #filename = bpy.path.ensure_ext(filename, ".mdl")
    fOptions.preserveExtTemp = False

    # Replace all characters besides A-Z, a-z, 0-9 with '_'
    #filename = bpy.path.clean_name(filename)

    # Compose the full file path
    fileFullPath = os.path.join(fullPath, filename)

    # Get the Urho path (relative to root)
    fileUrhoPath = os.path.relpath(fileFullPath, rootPath)
    fileUrhoPath = fileUrhoPath.replace(os.path.sep, '/')

    # Return full file path and relative file path
    return (fileFullPath, fileUrhoPath)


# Check if 'filepath' is valid
def CheckFilepath(filepath, fOptions):

    fp = filepath
    if type(filepath) is tuple:
        fp = filepath[0]

    if os.path.exists(fp) and not fOptions.fileOverwrite:
        log.error( "File already exists {:s}".format(fp) )
        return False
        
    return True


#--------------------
# XML formatters
#--------------------

def FloatToString(value):
    return "{:g}".format(value)

def Vector3ToString(vector):
    return "{:g} {:g} {:g}".format(vector[0], vector[1], vector[2])

def Vector4ToString(vector):
    return "{:g} {:g} {:g} {:g}".format(vector[0], vector[1], vector[2], vector[3])

def XmlToPrettyString(elem):
    rough = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough)
    pretty = reparsed.toprettyxml(indent="\t")
    i = pretty.rfind("?>")
    if i >= 0:
        pretty = pretty[i+2:]
    return pretty.strip()


#--------------------
# XML writers
#--------------------

# Write XML to a text file
def WriteXmlFile(xmlContent, filepath, fOptions):
    try:
        file = open(filepath, "w")
    except Exception as e:
        log.error("Cannot open file {:s} {:s}".format(filepath, e))
        return
    try:
        file.write(XmlToPrettyString(xmlContent))
    except Exception as e:
        log.error("Cannot write to file {:s} {:s}".format(filepath, e))
    file.close()


#--------------------
# Binary writers
#--------------------

class BinaryFileWriter:

    # We try to write the file with a single API call to avoid
    # the Editor crashing while reading a not completed file.
    # We set the buffer to 1Mb (if unspecified is 64Kb, and it is
    # 8Kb with multiple file.write calls)

    # Constructor.
    def __init__(self):
        self.filename = None
        self.buffer = None
    
    # Open file stream.
    def open(self, filename):
        self.filename = filename
        self.buffer = array.array('B')
        return True

    def close(self):
        file = open(self.filename, "wb", 1024 * 1024)
        self.buffer.tofile(file)
        file.close()

    # Writes an ASCII string without terminator
    def writeAsciiStr(self, v):
        self.buffer.extend(bytes(v, "ascii"))

    # Writes a 32 bits unsigned int
    def writeUInt(self, v):
        self.buffer.extend(struct.pack("<I", v))

    # Writes a 16 bits unsigned int
    def writeUShort(self, v):
        self.buffer.extend(struct.pack("<H", v))

    # Writes one 8 bits unsigned byte
    def writeUByte(self, v):
        self.buffer.extend(struct.pack("<B", v))

    # Writes four 32 bits floats .w .x .y .z
    def writeQuaternion(self, v):
        self.buffer.extend(struct.pack("<4f", v.w, v.x, v.y, v.z))

    # Writes three 32 bits floats .x .y .z
    def writeVector3(self, v):
        self.buffer.extend(struct.pack("<3f", v.x, v.y, v.z))

    # Writes a 32 bits float
    def writeFloat(self, v):
        self.buffer.extend(struct.pack("<f", v))