#!/usr/bin/python3

import os
import io
import re
import json
import glob
import gzip
import time
import pathlib
import subprocess
import lxml.html
import urllib.request
import robust_layer


def update_linux_vanilla():
    myName = "linux/vanilla"
    selfDir = os.path.dirname(os.path.realpath(__file__))

    # get latest kernel version from internet
    kernelVersion = None
    if True:
        root = util.fetchAndParseHtmlPage(myName, "https://www.kernel.org")
        td = root.xpath(".//td[text()='%s:']" % ("stable"))[0]
        td = td.getnext()
        while len(td) > 0:
            td = td[0]
        kernelVersion = td.text

    # get remote file
    remoteFile = None
    while True:
        kernelUrl = "https://www.kernel.org/pub/linux/kernel"
        kernelFile = "linux-%s.tar.xz" % (kernelVersion)
        signFile = "linux-%s.tar.sign" % (kernelVersion)

        # try mirror file structure 1: all files placed under / (a simple structure suitable for local mirrors)
        good = True
        for fn in [kernelFile, signFile]:
            if not util.cmdCallTestSuccess("wget", "--spider", "%s/%s" % (kernelUrl, fn)):
                good = False
                break
        if good:
            remoteFile = os.path.join(kernelUrl, kernelFile)
            break

        # try mirror file structure 2: /{v3.x,v4.x,...}/* (an overly complicated structure used by official kernel mirrors)
        subdir = None
        for i in range(3, 9):
            if kernelVersion.startswith(str(i)):
                subdir = "v%d.x" % (i)
        assert subdir is not None

        good = True
        for fn in [kernelFile, signFile]:
            if not util.cmdCallTestSuccess("wget", "--spider", "%s/%s/%s" % (kernelUrl, subdir, fn)):
                good = False
                break
        if good:
            remoteFile = os.path.join(kernelUrl, subdir, kernelFile)
            break

        # invalid
        print("%s: Can not find remote file." % myName)
        return

    # rename bbki file
    targetFile = os.path.join(myName, "%s.bbki" % (kernelVersion))
    util.renameTo(os.path.join(selfDir, targetFile))

    # change SRC_URI
    util.sed(targetFile, "SRC_URI=.*", "SRC_URI=\"%s\"" % (remoteFile))

    # print result
    print("%s: %s updated." % (myName, targetFile))


def update_linux_addon_linux_firmware():
    myName = "linux-addon/linux-firmware"
    selfDir = os.path.dirname(os.path.realpath(__file__))
    firmwareUrl = "https://www.kernel.org/pub/linux/kernel/firmware"

    # get firmware version version from internet
    firmwareVersion = None
    remoteFile = None
    if True:
        root = util.fetchAndParseHtmlPage(myName, firmwareUrl)
        for atag in root.xpath(".//a"):
            m = re.fullmatch("linux-firmware-(.*)\\.tar\\.xz", atag.text)
            if m is not None:
                if firmwareVersion is None or firmwareVersion < m.group(1):
                    firmwareVersion = m.group(1)
                    remoteFile = os.path.join(firmwareUrl, atag.get("href"))
        assert firmwareVersion is not None

    # rename bbki file
    targetFile = os.path.join(myName, "%s.bbki" % (firmwareVersion))
    util.renameTo(os.path.join(selfDir, targetFile))

    # change SRC_URI
    util.sed(targetFile, "SRC_URI=.*", "SRC_URI=\"%s\"" % (remoteFile))

    # print result
    print("%s: %s updated." % (myName, targetFile))


def update_linux_addon_wireless_regdb():
    myName = "linux-addon/wireless-regdb"
    selfDir = os.path.dirname(os.path.realpath(__file__))
    wirelessRegDbDirUrl = "https://www.kernel.org/pub/software/network/wireless-regdb"

    # get wireless-regdb from internet
    firmwareVersion = None
    remoteFile = None
    if True:
        out = util.fetchHtmlBinaryData(myName, wirelessRegDbDirUrl).decode("iso8859-1")
        for m in re.finditer("wireless-regdb-([0-9]+\\.[0-9]+\\.[0-9]+)\\.tar\\.xz", out, re.M):
            if firmwareVersion is None or m.group(1) > firmwareVersion:
                firmwareVersion = m.group(1)
                remoteFile = os.path.join(wirelessRegDbDirUrl, "wireless-regdb-%s.tar.xz" % firmwareVersion)
        assert firmwareVersion is not None

    # rename bbki file
    targetFile = os.path.join(myName, "%s.bbki" % (firmwareVersion))
    util.renameTo(os.path.join(selfDir, targetFile))

    # change SRC_URI
    util.sed(targetFile, "SRC_URI=.*", "SRC_URI=\"%s\"" % (remoteFile))

    # print result
    print("%s: %s updated." % (myName, targetFile))


def update_linux_addon_virtualbox_modules():
    myName = "linux-addon/virtualbox-modules"
    selfDir = os.path.dirname(os.path.realpath(__file__))
    url = "https://dev.gentoo.org/~polynomial-c/virtualbox"

    # get version from internet
    ver = None
    remoteFile = None
    if True:
        root = util.fetchAndParseHtmlPage(myName, url)
        for atag in root.xpath(".//a"):
            m = re.fullmatch("vbox-kernel-module-src-([0-9\.]+)\.tar\.xz", atag.text)
            if m is not None:
                if ver is None or util.compareVersion(ver, m.group(1)) < 0:
                    ver = m.group(1)
                    remoteFile = os.path.join(url, atag.get("href"))
        assert ver is not None

    # rename bbki file
    targetFile = os.path.join(myName, "%s.bbki" % (ver))
    util.renameTo(os.path.join(selfDir, targetFile))

    # change SRC_URI
    util.sed(targetFile, "SRC_URI=.*", "SRC_URI=\"%s\"" % (remoteFile))

    # print result
    print("%s: %s updated." % (myName, targetFile))


def update_linux_addon_broadcom_bt_firmware():
    myName = "linux-addon/broadcom-bt-firmware"
    selfDir = os.path.dirname(os.path.realpath(__file__))

    # get version from internet
    ver = None
    if True:
        data = util.fetchJsonData(myName, "https://api.github.com/repos/winterheart/broadcom-bt-firmware/releases")[0]
        assert data["name"].startswith("v")
        ver = data["name"][1:]

    # rename bbki file
    targetFile = os.path.join(myName, "%s.bbki" % (ver))
    util.renameTo(os.path.join(selfDir, targetFile))

    # print result
    print("%s: %s updated." % (myName, targetFile))


def update_linux_addon_bluez_firmware():
    myName = "linux-addon/bluez-firmware"
    selfDir = os.path.dirname(os.path.realpath(__file__))
    url = "http://www.bluez.org/download"

    # get version from internet
    ver = None
    if True:
        root = util.fetchAndParseHtmlPage(myName, url)
        for atag in root.xpath(".//a"):
            m = re.fullmatch("bluez-firmware-([0-9\.]+)\.tar\.gz", atag.text)
            if m is not None:
                if ver is None or util.compareVersion(ver, m.group(1)) < 0:
                    ver = m.group(1)
        assert ver is not None

    # rename bbki file
    targetFile = os.path.join(myName, "%s.bbki" % (ver))
    util.renameTo(os.path.join(selfDir, targetFile))

    # print result
    print("%s: %s updated." % (myName, targetFile))


def update_linux_addon_ipw2200_firmware():
    myName = "linux-addon/ipw2200-firmware"
    selfDir = os.path.dirname(os.path.realpath(__file__))
    url = "http://ipw2200.sourceforge.net/firmware.php"

    # get version from internet
    ver = None
    if True:
        root = util.fetchAndParseHtmlPage(myName, url)
        for atag in root.xpath(".//a"):
            if atag.text is None:           # it's really strange that a.text can be None
                continue
            m = re.fullmatch("firmware v([0-9\.]+)", atag.text.strip())
            if m is not None:
                if ver is None or util.compareVersion(ver, m.group(1)) < 0:
                    ver = m.group(1)
        assert ver is not None

    # rename bbki file
    targetFile = os.path.join(myName, "%s.bbki" % (ver))
    util.renameTo(os.path.join(selfDir, targetFile))

    # print result
    print("%s: %s updated." % (myName, targetFile))



class util:

    @staticmethod
    def fetchJsonData(myName, url):
        try:
            with urllib.request.urlopen(url, timeout=robust_layer.TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except OSError as e:
            print("%s: Failed to acces %s, %s" % (myName, url, e))
            time.sleep(robust_layer.RETRY_WAIT)

    @staticmethod
    def fetchHtmlBinaryData(myName, url):
        try:
            with urllib.request.urlopen(url, timeout=robust_layer.TIMEOUT) as resp:
                return resp.read()
        except OSError as e:
            print("%s: Failed to acces %s, %s" % (myName, url, e))
            time.sleep(robust_layer.RETRY_WAIT)

    @staticmethod
    def fetchAndParseHtmlPage(myName, url):
        while True:
            try:
                with urllib.request.urlopen(url, timeout=robust_layer.TIMEOUT) as resp:
                    if resp.info().get('Content-Encoding') is None:
                        fakef = resp
                    elif resp.info().get('Content-Encoding') == 'gzip':
                        fakef = io.BytesIO(resp.read())
                        fakef = gzip.GzipFile(fileobj=fakef)
                    else:
                        assert False
                    return lxml.html.parse(fakef)
            except OSError as e:
                print("%s: Failed to acces %s, %s" % (myName, url, e))
                time.sleep(robust_layer.RETRY_WAIT)

    @staticmethod
    def renameTo(targetFile):
        bFound = False
        for fullfn in glob.glob(os.path.join(os.path.dirname(targetFile), "*.bbki")):
            bFound = True
            if fullfn != targetFile:
                os.rename(fullfn, targetFile)
                return True
        assert bFound
        return False

    @staticmethod
    def cmdCallTestSuccess(cmd, *kargs):
        ret = subprocess.run([cmd] + list(kargs),
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             universal_newlines=True)
        if ret.returncode > 128:
            time.sleep(1.0)
        return (ret.returncode == 0)

    @staticmethod
    def sed(fn, pattern, repl):
        buf = pathlib.Path(fn).read_text()
        buf = re.sub(pattern, repl, buf)
        with open(fn, "w") as f:
            f.write(buf)

    @staticmethod
    def compareVersion(verstr1, verstr2):
        """eg: 3.9.11-gentoo-r1 or 3.10.7-gentoo"""

        partList1 = verstr1.split("-")
        partList2 = verstr2.split("-")

        verList1 = partList1[0].split(".")
        verList2 = partList2[0].split(".")

        if len(verList1) == 3 and len(verList2) == 3:
            ver1 = int(verList1[0]) * 10000 + int(verList1[1]) * 100 + int(verList1[2])
            ver2 = int(verList2[0]) * 10000 + int(verList2[1]) * 100 + int(verList2[2])
        elif len(verList1) == 2 and len(verList2) == 2:
            ver1 = int(verList1[0]) * 100 + int(verList1[1])
            ver2 = int(verList2[0]) * 100 + int(verList2[1])
        elif len(verList1) == 1 and len(verList2) == 1:
            ver1 = int(verList1[0])
            ver2 = int(verList2[0])
        else:
            assert False

        if ver1 > ver2:
            return 1
        elif ver1 < ver2:
            return -1

        if len(partList1) >= 2 and len(partList2) == 1:
            return 1
        elif len(partList1) == 1 and len(partList2) >= 2:
            return -1

        p1 = "-".join(partList1[1:])
        p2 = "-".join(partList2[1:])
        if p1 > p2:
            return 1
        elif p1 < p2:
            return -1

        return 0


if __name__ == "__main__":
    update_linux_vanilla()
    update_linux_addon_linux_firmware()
    update_linux_addon_virtualbox_modules()
    update_linux_addon_wireless_regdb()
    update_linux_addon_broadcom_bt_firmware()
    update_linux_addon_bluez_firmware()
    update_linux_addon_ipw2200_firmware()
