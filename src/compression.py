import tarfile
import io
import os

class TarFile(tarfile.TarFile):
    def __init__(self, *args, **kwargs):
        super(TarFile, self).__init__(*args, **kwargs)

    def extractall_progress(path, on_progress):
        members = self.getmembers()
        total_members = len(members)
        for member in members:
            self.extract(member, path)
            processed += 1
            on_progress((processed * 100 / total_members), member)

