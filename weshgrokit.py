import os
import platform
import subprocess
import sys
import time

from utils import create_dir, check_java_installed, download, extract_file, find_java_home, find_catalina_home, \
    index_source, update_opengrok_config_xml

NAME = "weshgrokit"

TOMCAT_VERSION = "9.0.37"
OPENGROK_VERSION = "1.3.16"
OPENJDK_VERSION = "14.0.2"
CONFIGURATION_XML = "configuration.xml"

DOWNLOAD_DIR = "downloads"
INSTALLED_DIR = "installed"
OPENGROK_DATA_DIR = "data"


def usage(args):
    print("Usage: " + os.path.basename(sys.argv[0]) + ' [command]')
    print()
    print("Command:")
    print("    help       : Show help")
    print("    install    : Download and install required files for running OpenGrok")
    print("    index      : Index/Update the source directory")
    print("    run        : Run OpenGrok")
    print("")
    print("Options:")
    print("    -source, -s: Set source directory to index")
    sys.exit(0)


def install(options):
    create_dir(DOWNLOAD_DIR)

    download(
        "https://download.java.net/java/GA/jdk14.0.2/205943a0976c4ed48cb16f1043c5c647/12/GPL/openjdk-%s_windows"
        "-x64_bin.zip" % OPENJDK_VERSION,
        where=DOWNLOAD_DIR)
    download("http://apache.40b.nl/tomcat/tomcat-9/v%s/bin/apache-tomcat-%s-windows-x64.zip" % (
        TOMCAT_VERSION, TOMCAT_VERSION),
             where=DOWNLOAD_DIR)
    download("https://github.com/oracle/opengrok/releases/download/%s/opengrok-%s.tar.gz" % (
        OPENGROK_VERSION, OPENGROK_VERSION),
             where=DOWNLOAD_DIR)
    download(
        "https://github.com/universal-ctags/ctags-win32/releases/download/2020-07-22%2F631690ad/ctags-2020-07"
        "-22_631690ad-x64.zip",
        where=DOWNLOAD_DIR)

    create_dir(INSTALLED_DIR)

    extract_file(os.path.join(DOWNLOAD_DIR, "openjdk-%s_windows-x64_bin.zip" % OPENJDK_VERSION), where=INSTALLED_DIR)
    extract_file(os.path.join(DOWNLOAD_DIR, "apache-tomcat-%s-windows-x64.zip" % TOMCAT_VERSION), where=INSTALLED_DIR)
    extract_file(os.path.join(DOWNLOAD_DIR, "opengrok-%s.tar.gz" % OPENGROK_VERSION), where=INSTALLED_DIR)
    extract_file(os.path.join(DOWNLOAD_DIR, "ctags-2020-07-22_631690ad-x64.zip"), where=INSTALLED_DIR)

    cataline_home = find_catalina_home()
    create_dir(os.path.join(cataline_home, "webapps", NAME))
    extract_file(os.path.join(INSTALLED_DIR, "opengrok-%s" % OPENGROK_VERSION, "lib", "source.war"),
                 where=os.path.join(cataline_home, "webapps", NAME))

    check_java_installed()

    print("[+] Ready to index the source directory!")


def index(options):
    if "source" in options:
        if os.path.isdir(options["source"]):
            opengrok_jar = os.path.join(INSTALLED_DIR, "opengrok-%s" % OPENGROK_VERSION, "lib", "opengrok.jar")
            ctags_exe = os.path.join(INSTALLED_DIR, "ctags.exe")
            create_dir(OPENGROK_DATA_DIR)
            index_source(options["source"], opengrok_jar, CONFIGURATION_XML, ctags_exe, OPENGROK_DATA_DIR)
        else:
            print("[!] Source directory: %s not found!" % options["source"])
    else:
        print("[!] Option \"source\" is required for index!")
        usage(sys.argv)


def run(options):
    os.environ["JAVA_HOME"] = find_java_home()
    os.environ["CATALINA_HOME"] = find_catalina_home()

    update_opengrok_config_xml(
        os.path.join(INSTALLED_DIR, "apache-tomcat-%s" % TOMCAT_VERSION, "webapps", NAME, "WEB-INF", "web.xml"),
        CONFIGURATION_XML)

    print("[+] Running Tomcat server ...")
    subprocess.call(os.path.join(find_catalina_home(), "bin", "startup.bat"), shell=False, stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT)
    print("[+] Check on http://localhost:8080/weshgrokit/")


def check_windows_x64():
    import platform
    if platform.architecture()[0] != "64bit":
        print("[!] This program was tested only for x64 Windows.")
        sys.exit(2)


def main():
    print("Starting %s at %s (%s version)\n" % (
        os.path.basename(sys.argv[0]), time.asctime(time.localtime(time.time())), platform.architecture()[0]))

    check_windows_x64()

    COMMAND = usage
    OPTIONS = { }
    for argi in range(len(sys.argv))[1:]:
        if sys.argv[argi] in ["install"]:
            COMMAND = install
        elif sys.argv[argi] in ["run"]:
            COMMAND = run
        elif sys.argv[argi] in ["index"]:
            COMMAND = index
        elif sys.argv[argi] in ["help", "-h", "--help", "/?"]:
            COMMAND = usage
        elif sys.argv[argi] in ["--source", "-s"]:
            OPTIONS["source"] = sys.argv[argi + 1]
            argi += 1

    COMMAND(OPTIONS)


if __name__ == "__main__":
    main()
