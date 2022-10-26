""" archive.py contains modules and functions to help with the processing of historical
Twitter data from https://archive.org/details/twitterstream.
"""

import bz2
import glob
import logging
import json
import os
import shutil
import tarfile
import zipfile

import requests
from clint.textui import progress
from user import Tweet


class ArchiveNotFound(Exception):
    """ Error raised when we can't find the remote archive for a particular date. """

class ArchiveNotDownloaded(Exception):
    """ Error raised when try to fetch archive but it hasn't been downloaded yet. """

class CouldNotExtract(Exception):
    """ Error raised when we failed to extract a particular archive. """

class TweetArchive:
    """
    Object to handle downloading and processing archived historical Twitter data from
    https://archive.org/details/twitterstream
    """

    def __init__(self, year, month, date, subdir="."):
        self.year = year
        self.month = month
        self.date = date
        self._url = None
        self._local_filepath = None
        self._downloaded = False
        self._subdir = os.path.join(subdir, f"{year}_{month:02d}_{date:02d}")

    def desc(self):
        """
        Returns a printable description of this archive for logging messages.
        """
        return f"{self._subdir} archive"

    def _get_remote_urls(self):
        year = self.year
        month = f"{self.month:02d}"
        date= f"{self.date:02d}"
        return (f"https://archive.org/download/archiveteam-twitter-stream-{year}-{month}/twitter_stream_{year}_{month}_{date}.tar",
                f"https://archive.org/download/archiveteam-twitter-stream-{year}-{month}/twitter-stream-{year}-{month}-{date}.zip")

    def fetch(self, progress_bar=False):
        """
        Attempts to fetch and extract remote archive into local directory.
        """
        if self._downloaded or os.path.exists(self._subdir):
            self._downloaded = True
            logging.info("Already downloaded this archive.")
            return
        os.makedirs(self._subdir)

        # Fetch remote resource by trying all possible URLs
        for url in self._get_remote_urls():
            with requests.get(url, stream=True) as resp:
                if resp.status_code != 200:
                    continue
                self._url = url
                filename = os.path.basename(url)
                logging.info("Downloading %s...", filename)
                self._local_filepath = os.path.join(self._subdir, filename)
                total_length = int(resp.headers.get('content-length'))
                with open(self._local_filepath, "wb+") as file:
                    if progress_bar:
                        for chunk in progress.bar(resp.iter_content(chunk_size=1024),
                                                  expected_size=(total_length/1024)+1):
                            if chunk:
                                file.write(chunk)
                                file.flush()
                    else:
                        shutil.copyfileobj(resp.raw, file)
                break

        # If we could not find the remote resource anyways...
        if self._local_filepath is None:
            # logging.error("Could not find remote archive for %s", self.desc())
            self.cleanup()
            raise ArchiveNotFound(f"Could not find remote archive for {self.desc()}")

        # Extracting archive
        logging.info("Extracting %s...", self._local_filepath)
        if self._local_filepath.endswith("tar"):
            with tarfile.open(self._local_filepath) as file:
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
                    
                
                safe_extract(file, self._subdir)
        elif self._local_filepath.endswith("zip"):
            with zipfile.ZipFile(self._local_filepath) as file:
                file.extractall(self._subdir)
        else:
            self.cleanup()
            raise CouldNotExtract(f"Don't know how to extract archive {self._local_filepath}")

        # Removing downloaded archive after extraction
        logging.info("Removing %s...", self._local_filepath)
        os.remove(self._local_filepath)
        self._downloaded = True

    def cleanup(self):
        """
        Cleans up local directory containing full archive data.
        """
        shutil.rmtree(self._subdir, ignore_errors=True)
        self._downloaded = False

    def tweets(self):
        """
        Generator providing each line in contained archive.
        """
        if not self._downloaded:
            raise ArchiveNotDownloaded(f"Tried to fetch tweets in undownloaded {self.desc()}")
        filepaths = glob.glob(self._subdir + "/**/*.json.bz2", recursive=True)
        for i, filepath in enumerate(filepaths):
            if i % 100 == 0:
                logging.info("...%d/%d files processed for %s", i, len(filepaths), self.desc())
            with bz2.open(filepath, "r") as file:
                for line in file:
                    try:
                        data = json.loads(line.strip())
                    except json.decoder.JSONDecodeError as e:
                        logging.warning(f"{filepath} has JSONDecodeError, skipping line")
                        continue

                    if "user" not in data:
                        continue
                    yield Tweet.from_dict(data)
