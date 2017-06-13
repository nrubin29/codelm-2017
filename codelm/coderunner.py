import os
import shutil
import subprocess
from abc import ABCMeta, abstractmethod


class File:
    """
    This class represents a single code file. A Runner can have multiple files.
    """

    def __init__(self, name, code=None, src_path=None):
        self.name = name

        if code is not None:
            self.code = code

        elif src_path:
            self.code = open(src_path).read()

        else:
            raise Exception('Attempted to init File without code or src_path.')

    def mkfile(self, folder_path):
        file_path = folder_path + '/' + self.name

        with open(file_path, 'w') as file:
            file.write(self.code)


class Runner:
    __metaclass__ = ABCMeta

    def __init__(self, folder_name, files):
        self.folder_name = folder_name
        self.folder_path = None
        self.files = files  # The first file in this list will be the entry point!

        self.set_up = False
        self.compile_exit_code = -1
        self.run_exit_code = -1

        self.log = []

    def mkfiles(self):
        for possible_folder in ('/var/codeeval/{}', '/Users/s010380/codeeval/{}', '/Users/nrubin29/codeeval/{}'):
            folder_path = possible_folder.format(self.folder_name)

            try:
                os.mkdir(folder_path)
                self.folder_path = folder_path
                break
            except FileExistsError:
                shutil.rmtree(folder_path)
                os.mkdir(folder_path)
                self.folder_path = folder_path
            except:
                pass

        if not self.folder_path:
            raise Exception('Could not find codeeval folder. Is this running on a new system?')

        for file in self.files:
            file.mkfile(self.folder_path)

    def cleanup(self):
        shutil.rmtree(self.folder_path)

    def setup(self):
        self.mkfiles()
        compile_data, self.compile_exit_code = self._compile()

        if self.compile_exit_code is not 0:
            self.log.append('Compilation failed with error code {}'.format(self.compile_exit_code))
            self.log.append(compile_data)

        self.set_up = True
        return self.compile_exit_code is 0, compile_data

    def start_proc(self, cmd):
        return subprocess.Popen(cmd.split(' '), cwd=self.folder_path, stdout=subprocess.PIPE,
                                stdin=subprocess.PIPE, stderr=subprocess.STDOUT)

    def run_proc(self, cmd, inp=None):
        try:
            p = self.start_proc(cmd)
            return p.communicate(input=inp.encode() if inp else None, timeout=10)[0].decode().strip(), p.returncode
        except subprocess.TimeoutExpired:
            return None, -1
        except OSError as e:
            return None, e.errno

    def go(self, inp=None):
        if not self.set_up:
            self.setup()

        if self.compile_exit_code is 0:
            run_data, self.run_exit_code = self._run(inp)

            if self.run_exit_code is not 0:
                self.log.append('Run failed with error code {}'.format(self.run_exit_code))
                self.log.append(run_data)

            return self.run_exit_code is 0, run_data

        else:
            raise Exception('Tried running while compile exit code is {}.'.format(self.compile_exit_code))

    def _compile(self):
        return '', 0

    @abstractmethod
    def _run(self, inp=None):
        raise Exception('run() not implemented.')

    @abstractmethod
    def _run_async(self):
        raise Exception('run_async() not implemented.')


class JavaRunner(Runner):
    def _compile(self):
        return self.run_proc('javac ' + ' '.join([file.name for file in self.files]))

    def _run(self, inp=None):
        return self.run_proc('java ' + self.files[0].name[:-5], inp)  # The -5 is to get rid of the .java

    def _run_async(self):
        return self.start_proc('java ' + self.files[0].name[:-5])  # The -5 is to get rid of the .java


class PythonRunner(Runner):
    def setup(self):
        self.files.append(File('__init__.py', code=''))
        return super(PythonRunner, self).setup()

    def _compile(self):
        return self.run_proc('python -m py_compile ' + ' '.join([file.name for file in self.files]))

    def _run(self, inp=None):
        return self.run_proc('python ' + self.files[0].name, inp)

    def _run_async(self):
        return self.start_proc('python ' + self.files[0].file_name)


class CppRunner(Runner):
    def _compile(self):
        return self.run_proc('g++ ' + ' '.join([file.name for file in self.files]))

    def _run(self, inp=None):
        return self.run_proc('./a.out', inp)

    def _run_async(self):
        return self.start_proc('./a.out')
