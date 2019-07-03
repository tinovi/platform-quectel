# WizIO 2019 Georgi Angelov
# http://www.wizio.eu/
# https://github.com/Wiz-IO

import os
from os.path import join
from shutil import copyfile
from SCons.Script import ARGUMENTS, DefaultEnvironment, Builder
from bg96 import upload_app

from subprocess import check_output, CalledProcessError, call
import tempfile
def _exec_command(adb_cmd):
    t = tempfile.TemporaryFile()
    final_adb_cmd = []
    for e in adb_cmd:
        if e != '':  # avoid items with empty string...
            final_adb_cmd.append(e)  # ... so that final command doesn't
            # contain extra spaces
    #print('\n[RUN] ' + ' '.join(adb_cmd))
    try:
        output = check_output(final_adb_cmd, stderr=t)
    except CalledProcessError as e:
        t.seek(0)
        result = e.returncode, t.read()
    else:
        result = 0, output
        print('\n' + result[1])
    return result 


def dev_uploader(target, source, env):
    return
    uploader_dir = env.PioPlatform().get_package_dir("tool-quectel")
    uploader = join(uploader_dir, "windows", "bg96", "QWinExplorer"),
    print uploader
    _exec_command(uploader)
    return
    #return upload_app(env.BoardConfig().get("build.core"), join(env.get("BUILD_DIR"), "program.bin"), env.get("UPLOAD_PORT")) 

def dev_header(target, source, env):
    d = source[0].path 
    print d
    f = open(d.replace("program.bin", "oem_app_path.ini"), "wb")
    f.write("/datatx/program.bin")
    f.close()

def dev_create_template(env):
    return
                
def dev_compiler(env):
    env.Replace(
        BUILD_DIR = env.subst("$BUILD_DIR").replace("\\", "/"),
        AR="arm-none-eabi-ar",
        AS="arm-none-eabi-as",
        CC="arm-none-eabi-gcc",
        GDB="arm-none-eabi-gdb",
        CXX="arm-none-eabi-g++",
        OBJCOPY="arm-none-eabi-objcopy",
        RANLIB="arm-none-eabi-ranlib",
        SIZETOOL="arm-none-eabi-size",
        ARFLAGS=["rc"],
        SIZEPROGREGEXP=r"^(?:\.text|\.data|\.bootloader)\s+(\d+).*",
        SIZEDATAREGEXP=r"^(?:\.data|\.bss|\.noinit)\s+(\d+).*",
        SIZECHECKCMD="$SIZETOOL -A -d $SOURCES",
        SIZEPRINTCMD='$SIZETOOL --mcu=$BOARD_MCU -C -d $SOURCES',
        PROGSUFFIX=".elf",  
    )

def dev_init(env, platform):
    dev_create_template(env)
    dev_compiler(env)
    framework_dir = env.PioPlatform().get_package_dir("framework-quectel")
    core = env.BoardConfig().get("build.core")    
    variant = env.BoardConfig().get("build.variant")  
    env.firmware = env.BoardConfig().get("build.firmware", "SDK2").upper()  #SDK2 #SDK3
    print "FIRMWARE", env.firmware
    env.base = env.BoardConfig().get("build.base", "0x40000000")    
    print "RO_BASE", env.base
    env.heap = env.BoardConfig().get("build.heap", "1048576") 
    env.Append(
       CPPDEFINES = [ # -D                         
            "{}=200".format(platform.upper()), 
            "CORE_" + core.upper().replace("-", "_"),
            "QAPI_TXM_MODULE", 
            "TXM_MODULE",  
            "TX_DAM_QC_CUSTOMIZATIONS",  
            "TX_ENABLE_PROFILING",  
            "TX_ENABLE_EVENT_TRACE",  
            "TX_DISABLE_NOTIFY_CALLBACKS",   
            "FX_FILEX_PRESENT",  
            "TX_ENABLE_IRQ_NESTING",   
            "TX3_CHANGES", 
            "_RO_BASE_=" + env.base, # 0x40000000 
            "HEAP=" + env.heap       # 1M                
        ],        
        CPPPATH = [ # -I
            join(framework_dir,  platform, platform),
            join(framework_dir,  platform, "cores", core),
            join(framework_dir,  platform, "variants", variant), 
            join(framework_dir, "threadx", core, env.firmware),
            join(framework_dir, "threadx", core, env.firmware, "qapi"),
            join(framework_dir, "threadx", core, env.firmware, "threadx_api"),             
            join(framework_dir, "threadx", core, env.firmware, "quectel", "include"), 
            join(framework_dir, "threadx", core, "wizio"),         
            join("$PROJECT_DIR", "lib"),
            join("$PROJECT_DIR", "include")         
        ],        
        CFLAGS = [
            "-std=c11",   
            "-Wno-pointer-sign",                                                                      
        ],  
        CXXFLAGS = [   
            "-std=c++11",                             
            "-fno-rtti",
            "-fno-exceptions", 
            "-fno-non-call-exceptions",
            "-fno-use-cxa-atexit",
            "-fno-threadsafe-statics",
        ],  
        CCFLAGS = [
            "-O1",          
            "-marm",
            "-mcpu=cortex-a7",
            "-mfloat-abi=softfp",  
            "-fdata-sections",      
            "-ffunction-sections",              
            "-fno-strict-aliasing",
            "-fno-zero-initialized-in-bss", 
            "-fsingle-precision-constant",                                                 
            "-Wall", 
            "-Wstrict-prototypes", 
            "-Wp,-w",                                                       
        ],                     
        LINKFLAGS = [  
            "-O1",
            "-g",  
            "-marm",
            "-mcpu=cortex-a7",
            "-mfloat-abi=softfp",   
            "-nostartfiles",   
            "-fno-use-cxa-atexit",     
            "-fno-zero-initialized-in-bss", 
            "-Xlinker", "--defsym=_RO_BASE_=" + env.base,                                 
            "-Xlinker", "--gc-sections",                           
            "-Wl,--gc-sections", 
        ], 
        LIBSOURCE_DIRS=[ join(framework_dir, platform, "libraries", core), ],       
        LDSCRIPT_PATH = join(framework_dir, "threadx", core, "cpp.ld"), 
        LIBS = [ "gcc", "m" ],               
        BUILDERS = dict(
            ElfToBin = Builder(
                action = env.VerboseAction(" ".join([
                    "$OBJCOPY",
                    "-O",
                    "binary",
                    "$SOURCES",
                    "$TARGET",
                ]), "Building $TARGET"),
                suffix = ".bin"
            ),    
            MakeHeader = Builder( 
                action = env.VerboseAction(dev_header, "ADD HEADER"),
                suffix = ".ini"
            )       
        ), 
        UPLOADCMD = dev_uploader
    )

    libs = [] 
    #ARDUINO  
    libs.append(
        env.BuildLibrary(
            join("$BUILD_DIR", "_" + platform),
            join(framework_dir, platform, platform),
    ))     
    libs.append(
        env.BuildLibrary(
            join("$BUILD_DIR", "_core"),
            join(framework_dir, platform, "cores", core),
    ))    
    libs.append(
        env.BuildLibrary(
            join("$BUILD_DIR", "_variant"),
            join(framework_dir, platform, "variants", variant),
    ))  
    #THREADX
    libs.append(
        env.BuildLibrary(
            join("$BUILD_DIR", "_threadx"),
            join(framework_dir, "threadx", core, env.firmware),
    ))  
    libs.append(
        env.BuildLibrary(
            join("$BUILD_DIR", "_wizio"),
            join(framework_dir, "threadx", core, "wizio"),
    ))      
    #PROJECT
    libs.append(
        env.BuildLibrary(
            join("$BUILD_DIR", "_custom"), 
            join("$PROJECT_DIR", "lib"),                       
    ))         

    env.Append(LIBS = libs)   