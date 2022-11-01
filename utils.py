import os
import subprocess
import sys
import tarfile
from zipfile import ZipFile

import dicttoxml as dicttoxml
import untangle
import requests
import xmltodict as xmltodict


def index_source(directory, opengrok_jar, configuration_xml, ctags_exe, opengrok_data):
    print("[+] Indexing: %s" % directory)
    cmd = '%s -jar "%s" -W "%s" -c "%s" -P -S -v -s "%s" -d "%s"' % (
        get_java_path(),
        opengrok_jar,
        configuration_xml,
        ctags_exe,
        directory,
        opengrok_data
    )
    try:
        state = 0
        for line in subprocess.check_output(cmd, stderr=subprocess.STDOUT).split(b"\n"):
            if line.startswith(b"WARNING: "):
                state = 1
                print("[!] Warning: " + line[9:].decode().strip())
        print("[+] Done")
        if state == 0:
            print("[+] Ready to run!")
        elif state == 1:
            print("[+] Maybe ready to run! Check warning(s).")
    except subprocess.CalledProcessError as e:
        print("[!] Error indexing source directory!")
        sys.exit(1)


def update_opengrok_config_xml(xml_file, config_path):
    if os.path.isfile(xml_file):
        with open(xml_file, "rb") as f:
            root = xmltodict.parse(f)

        context = root["web-app"]["context-param"]
        if context["param-name"] == "CONFIGURATION":
            context["param-value"] = os.path.abspath(config_path)

        with open(xml_file, "w") as f:
            xml = xmltodict.unparse(root, pretty=True)
            f.write(xml)
    else:
        print("[!] Configuration file: %s not found!" % xml_file)
        sys.exit(1)


def extract_file(file, where="."):
    print("[+] Extracting", file)
    if file.lower().endswith(".tar.gz"):
        with tarfile.open(file) as z:
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(z, path=where)
    elif file.lower().endswith(".zip"):
        with ZipFile(file, "r") as z:
            z.extractall(path=where)
    elif file.lower().endswith(".war"):
        with ZipFile(file, "r") as z:
            z.extractall(path=where)


def create_dir(d):
    os.makedirs(d, exist_ok=True)


def download(url, where="."):
    create_dir(where)
    file = os.path.join(where, os.path.basename(url))
    if not os.path.isfile(file):
        print("[+] Downloading", os.path.basename(url))
        with open(file, 'wb') as f:
            response = requests.get(url, stream=True)
            total = response.headers.get('content-length')
            if total is None:
                f.write(response.content)
            else:
                downloaded = 0
                total = int(total)
                for data in response.iter_content(chunk_size=max(int(total / 1000), 1024 * 1024)):
                    downloaded += len(data)
                    f.write(data)
                    done = int(50 * downloaded / total)
                    sys.stdout.write('\r    [{}{}]'.format('*' * done, ' ' * (50 - done)))
                    sys.stdout.flush()
        sys.stdout.write('\n')
    else:
        print("[+] Required file found:", os.path.basename(url))


def get_java_path():
    jre_home = find_java_home()
    return os.path.join(jre_home, "bin", "java")


def check_java_installed():
    java_path = get_java_path()
    java = subprocess.check_output("%s --version" % java_path)
    if java.find(b"OpenJDK Runtime Environment") == -1:
        print("[!] Unable to run Java from OpenJDK!")
        sys.exit(1)


def find_java_home():
    for f in os.listdir("installed"):
        if f.startswith("jdk"):
            return os.path.join("installed", f)
    else:
        print("[!] JAVA_HOME not found!")
        sys.exit(1)


def find_catalina_home():
    for f in os.listdir("installed"):
        if f.startswith("apache-tomcat"):
            return os.path.join("installed", f)
    print("[!] CATALINA_HOME not found!")
    sys.exit(1)
