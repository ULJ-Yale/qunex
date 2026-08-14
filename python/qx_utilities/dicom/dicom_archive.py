#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``dicom_archive.py``

Packing and unpacking of DICOM packets.

Holds the gzip, tar and zip compression of sorted acquisition folders, the
recursive unpacking used by the conversion commands, and the streaming
member iterators that let ``sort_dicom`` and ``import_dicom`` read a packet
without extracting it to disk first.
"""

# Copyright (c) Grega Repovs. All rights reserved.

import glob
import io
import os
import re
import shutil
import subprocess
import sys
import tarfile
import traceback
import zipfile
import gzip as gz
from concurrent.futures import ProcessPoolExecutor, as_completed

import qx_utilities.general.exceptions as ge
import qx_utilities.general.log as gl
from qx_utilities.dicom.dicom_utils import _safe_rmtree


# regexes identifying compressed package types for the member-source iterator
_RE_ZIP = re.compile(r"\.zip$", re.IGNORECASE)
_RE_TAR = re.compile(r"(\.tar$|\.tar\.gz$|\.tar\.bz2$|\.tarz$|\.tar\.bzip2$|\.tgz$)", re.IGNORECASE)


def _zip_dicom(gzip, dicom_folder):
    """
    Compress or archive a dicom acquisition folder or file

    This function archives the dicom acquisition folder a single tar.gz file
    when gzip=folder. A hidden temporary tar.gz file will be created and will
    be renamed after the dicom acquisition folder is completely archived. If
    gzip=file is set, gzip will compress individual files in the dicom
    acquisition folder.

    This function can be called through ProcessPoolExecutor.
    """
    r = {"args": {"gzip": gzip, "dicom_folder": dicom_folder}}
    try:
        if not os.path.exists(dicom_folder):
            raise ge.CommandFailed(
                "_zip_dicom", "Unable to find acquisition folder %s" % (dicom_folder)
            )
        if not os.path.isdir(dicom_folder):
            raise ge.CommandFailed("_zip_dicom", "%s is not a folder" % (dicom_folder))

        dicom_dir, dicom_num = os.path.split(dicom_folder)
        if gzip == "folder":
            dicom_folder_zip = os.path.join(dicom_dir, "{}.tar.gz".format(dicom_num))
            dicom_folder_zip_tmp = os.path.join(
                dicom_dir, ".{}.tar.gz".format(dicom_num)
            )

            if os.path.exists(dicom_folder_zip):
                os.remove(dicom_folder_zip)
            if os.path.exists(dicom_folder_zip_tmp):
                os.remove(dicom_folder_zip_tmp)

            p = subprocess.run(
                [
                    "tar",
                    "czf",
                    os.path.abspath(dicom_folder_zip_tmp),
                    os.path.basename(dicom_folder),
                ],
                cwd=os.path.dirname(dicom_folder),
            )

            if p.returncode != 0:
                raise ge.CommandFailed(
                    "_zip_dicom",
                    "Unable to archive: tar exit code: %d" % (p.returncode),
                )

            os.rename(dicom_folder_zip_tmp, dicom_folder_zip)
            _safe_rmtree(dicom_folder)

        elif gzip == "file":
            p = subprocess.run(["gzip", "-r", dicom_folder])

            if p.returncode != 0:
                raise ge.CommandFailed(
                    "_zip_dicom",
                    "Unable to archive: gzip exit code: %d" % (p.returncode),
                )
        r["status"] = "ok"
    except Exception as e:
        r["status"] = "error"
        r["exception"] = e
        r["traceback"] = traceback.format_exc()
    return r


def _get_zip_file_content_iterator(packet_name):
    """
    Return an iterator over all the files in an zip or tar archive.

    The iterator yields the file name and a file object opened in binary mode
    """

    def zip_gen():
        try:
            z = zipfile.ZipFile(packet_name, "r")
            fobj = None
            for f in z.infolist():
                if f.is_dir():
                    continue
                fobj = z.open(f, "rb")
                yield f.filename, fobj
                fobj.close()
        except Exception:
            e = sys.exc_info()[0]
            raise ge.CommandFailed(
                "_get_zip_file_content_iterator",
                "Zip file could not be processed",
                "Opening zip [%s] returned an error [%s]!" % (packet_name, e),
                "Please check your data!",
            )
        finally:
            if fobj is not None:
                fobj.close()
            if z is not None:
                z.close()

    def tar_gen():
        try:
            tar = tarfile.open(packet_name, "r")
            fobj = None
            for tarinfo in tar:
                if tarinfo.isfile():
                    fobj = tar.extractfile(tarinfo)
                    yield tarinfo.name, fobj
                    fobj.close()
        except Exception:
            pass
        finally:
            if fobj is not None:
                fobj.close()
            if tar is not None:
                tar.close()

    if not os.path.exists(packet_name):
        raise ge.CommandFailed(
            "_get_zip_file_content_iterator",
            "Packet does not exist {}".format(packet_name),
        )

    if packet_name.endswith("zip"):
        return zip_gen()
    elif re.search(
        r"\.tar$|\.tar\.gz$|\.tar\.bz2$|\.tarz$|\.tar\.bzip2$|\.tgz$", packet_name
    ):
        return tar_gen()
    else:
        raise ge.CommandFailed("_get_zip_file_content_iterator", "Unknown packet type")


def _unzip_dicom_folder(dicom_packet, dicom_folder):
    """
    Extract archived dicom acquisition.

    The zip/tar dicom packet (dicom_packet) will be extracted into the dicom
    acquisition folder (dicom_folder).If the input packet contains gzipped
    dicom files, they will also be decompressed on-the-fly to minimize I/O
    operations.

    Archived dicom_packets generated by dicom2niix/dicom2nii will not compress
    individual dicom files as gzip in gzip=folder mode. This would allow user
    to manually archive dicom acquisition folders previously processed in
    gzip=file mode.

    This function can be called through ProcessPoolExecutor.
    """
    r = {"args": {"dicom_packet": dicom_packet, "dicom_folder": dicom_folder}}
    try:
        if not os.path.exists(dicom_folder):
            os.mkdir(dicom_folder)

        for fpath, fobj in _get_zip_file_content_iterator(dicom_packet):
            extract_path = os.path.join(dicom_folder, os.path.basename(fpath))
            if fpath.endswith(".gz"):
                extract_path, _ = extract_path.rsplit(".", 1)
            with open(extract_path, "wb") as f:
                if fpath.endswith(".gz"):
                    with gz.GzipFile(fileobj=fobj) as gzobj:
                        shutil.copyfileobj(gzobj, f)
                else:
                    shutil.copyfileobj(fobj, f)

        r["status"] = "ok"
    except Exception as e:
        r["status"] = "error"
        r["exception"] = e
        r["traceback"] = traceback.format_exc()
    return r


def _unzip_dicom_file(dicom_folder):
    """
    Decompress gzip files in a dicom acquisition folder

    This function can be called through ProcessPoolExecutor.
    """
    r = {"args": {"dicom_folder": dicom_folder}}
    try:
        p = subprocess.run(["gunzip", "-r", dicom_folder])
        if p.returncode != 0:
            raise ge.CommandError(
                "_unzip_dicom_file",
                "Unable to unzip dicom files: gunzip exit code: %d" % p.returncode,
            )
        r["status"] = "ok"
    except Exception as e:
        r["status"] = "error"
        r["exception"] = e
        r["traceback"] = traceback.format_exc()
    return r


def _unzip_dicom(dicom_root_folder, parelements, _log=None):
    """
    Find and unzip archived dicom folders and files.

    This function finds archived dicom folders created by previous import dicom
    runs
    """
    log = gl.log_or_console(_log)

    with ProcessPoolExecutor(parelements) as executor:
        pending_futures = []
        for i in os.listdir(dicom_root_folder):
            fullpath = os.path.join(dicom_root_folder, i)
            if os.path.isfile(fullpath):
                match_result = re.match(
                    r"^(?P<dcm_name>\d+)(\.zip|\.tar|\.tar\.gz|\.tar\.bz2|\.tar\.xz|\.tarz|\.tar\.bzip2|\.tgz)$",
                    i,
                )
                if match_result:
                    dcm_name = match_result.group("dcm_name")
                    log.detail("submit unzip dicom folder: {}".format(dcm_name))
                    if not dcm_name.isdigit():
                        continue
                    future = executor.submit(
                        _unzip_dicom_folder,
                        fullpath,
                        os.path.join(dicom_root_folder, dcm_name),
                    )
                    pending_futures.append(future)
        exceptions = []
        for future in as_completed(pending_futures):
            if future.exception() is not None:
                # Unhandled
                e = future.exception()
                log.error("unhandled exception")
                log.raw("\n" + traceback.format_exc())
                exceptions.append(e)
                continue
            r = future.result()
            if r["status"] == "ok":
                log.detail(
                    "unzipped {} -> {}".format(
                        r["args"]["dicom_packet"], r["args"]["dicom_folder"]
                    )
                )
            else:
                log.error(
                    "unzip failed {} -> {}".format(
                        r["args"]["dicom_packet"], r["args"]["dicom_folder"]
                    )
                )
                log.raw("\n" + r["traceback"])
                exceptions.append(r["exception"])
        # raise exception after the status of all child processes are collected
        if len(exceptions) > 0:
            raise ge.CommandError(
                "_unzip_dicom", "Unable to unzip one or more acquisition folders"
            )

        pending_futures.clear()
        for i in os.listdir(dicom_root_folder):
            fullpath = os.path.join(dicom_root_folder, i)
            if os.path.isdir(fullpath):
                glob_iter = glob.iglob(os.path.join(fullpath, "*.gz"))
                if next(glob_iter, None):
                    future = executor.submit(_unzip_dicom_file, fullpath)
                    pending_futures.append(future)

        exceptions.clear()
        for future in as_completed(pending_futures):
            if future.exception() is not None:
                # Unhandled
                e = future.exception()
                log.error("unhandled exception")
                log.raw("\n" + traceback.format_exc())
                exceptions.append(e)
                continue
            r = future.result()
            if r["status"] == "ok":
                log.detail(
                    "extract gzipped dicoms {}".format(r["args"]["dicom_folder"])
                )
            else:
                log.error(
                    "extract gzipped dicoms failed {}".format(r["args"]["dicom_folder"])
                )
                log.raw("\n" + r["traceback"])
                exceptions.append(r["exception"])
        # raise exception after the status of all child processes are collected
        if len(exceptions) > 0:
            raise ge.CommandError("_unzip_dicom", "Unable to unzip one or more files")


def _iter_stream_members(name, data):
    """
    Yield ``(name, bytes)`` for a member whose content is already in memory.

    If the member is itself a (nested) zip or tar archive it is expanded
    recursively; otherwise the member is yielded as-is. Gzipped single files
    (e.g. ``*.dcm.gz``) keep their raw gzipped bytes and ``.gz`` name — the
    reader/writer decompress as needed.
    """
    if _RE_ZIP.search(name):
        with zipfile.ZipFile(io.BytesIO(data), "r") as z:
            for info in z.infolist():
                if info.is_dir() or info.file_size == 0:
                    continue
                with z.open(info, "r") as f:
                    yield from _iter_stream_members(info.filename, f.read())
    elif _RE_TAR.search(name):
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as tar:
            for member in tar:
                if not member.isfile():
                    continue
                handle = tar.extractfile(member)
                if handle is None:
                    continue
                yield from _iter_stream_members(member.name, handle.read())
    else:
        yield name, data


def count_import_members(source):
    """
    Number of members ``iter_import_members`` will yield, or ``None`` if
    counting is not cheap.

    Used only to turn scan progress into a percentage, so it must never cost a
    second pass over the data: a zip is counted from its central directory and a
    folder from ``os.walk``, both cheap, while a tar returns ``None`` because
    counting it means decompressing the whole archive. Nested archives are not
    expanded here either, so for a package that contains them the count is a
    lower bound -- callers must treat it as approximate.
    """
    try:
        if os.path.isdir(source):
            return sum(len(files) for _, _, files in os.walk(source))
        if os.path.isfile(source):
            if _RE_ZIP.search(source):
                with zipfile.ZipFile(source, "r") as z:
                    return sum(1 for i in z.infolist() if not i.is_dir() and i.file_size)
            if _RE_TAR.search(source):
                return None
            return 1
    except Exception:
        return None
    return None


def iter_import_members(source):
    """
    Yield ``(relname, raw_bytes)`` for every file in an import ``source``.

    ``source`` is a path to a zip archive, a tar archive (``.tar``,
    ``.tar.gz``, ``.tar.bz2``, ``.tgz``, ...), a folder (walked recursively),
    or a single loose file. Members that are themselves archives are expanded
    recursively. The top-level container is streamed member-by-member so a large
    archive or folder is never slurped whole; only nested archive members are
    buffered in memory.

    This replaces the old inbox-staging copy: instead of writing every file into
    ``<session>/inbox`` before sorting, callers consume the members directly and
    write each file once to its final ``dicom`` location.

    Re-iterable: calling the function again yields a fresh pass over the source.
    """
    if os.path.isdir(source):
        for root, _, files in os.walk(source):
            for fn in sorted(files):
                path = os.path.join(root, fn)
                rel = os.path.relpath(path, source)
                with open(path, "rb") as f:
                    yield from _iter_stream_members(rel, f.read())
    elif os.path.isfile(source):
        if _RE_ZIP.search(source):
            with zipfile.ZipFile(source, "r") as z:
                for info in z.infolist():
                    if info.is_dir() or info.file_size == 0:
                        continue
                    with z.open(info, "r") as f:
                        yield from _iter_stream_members(info.filename, f.read())
        elif _RE_TAR.search(source):
            with tarfile.open(source, "r:*") as tar:
                for member in tar:
                    if not member.isfile():
                        continue
                    handle = tar.extractfile(member)
                    if handle is None:
                        continue
                    yield from _iter_stream_members(member.name, handle.read())
        else:
            with open(source, "rb") as f:
                yield from _iter_stream_members(os.path.basename(source), f.read())
