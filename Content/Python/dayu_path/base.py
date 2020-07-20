#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Import built-in modules
import bisect
import os
import re
import shutil
import stat
import subprocess
import sys

# Import local modules
from dayu_path.constants import EXT_PATTERN
from dayu_path.constants import EXT_SINGLE_MEDIA
from dayu_path.constants import FRAME_REGEX
from dayu_path.constants import PATTERN_REGEX
from dayu_path.constants import SCAN_IGNORE
from dayu_path.constants import UNC_REGEX
from dayu_path.constants import VERSION_REGEX
from dayu_path.constants import WIN32_DRIVE_REGEX
from dayu_path.errors import DayuPathBaseError

BASE_STRING_TYPE = str  # Python 3 str (=unicode), or Python 2 bytes.

if os.path.supports_unicode_filenames:
    if sys.version_info[0] == 2:
        BASE_STRING_TYPE = unicode  # Python 2 unicode.



class DayuPath(BASE_STRING_TYPE):
    pathlib = os.path

    def __new__(cls, path, frames=None, missing=None):
        if path:
            if isinstance(path, DayuPath):
                return path

            normalize_path = re.sub(r'\\', '/', path)
            normalize_path = re.sub(r'^//', r'\\\\', normalize_path)
            match = WIN32_DRIVE_REGEX.match(normalize_path)
            if match:
                lower = match.group(1).lower()
                normalize_path = normalize_path.replace(match.group(1),
                                                        lower).rstrip('/')
            return super(DayuPath, cls).__new__(cls, normalize_path)

        return None

    def __init__(self, path, frames=None, missing=None):
        super(DayuPath, self).__init__()
        self.frames = frames if frames else []
        self.missing = missing if missing else []

    def exists(self):
        return self.pathlib.exists(self)

    def lexists(self):
        return self.pathlib.lexists(self)

    def isfile(self):
        return self.pathlib.isfile(self)

    def isdir(self):
        return self.pathlib.isdir(self)

    def islink(self):
        return self.pathlib.islink(self)

    def ismount(self):
        return self.pathlib.ismount(self)

    def atime(self):
        return self.pathlib.getatime(self)

    def ctime(self):
        return self.pathlib.getctime(self)

    def mtime(self):
        return self.pathlib.getmtime(self)

    def size(self):
        return self.pathlib.getsize(self)

    def norm(self):
        return DayuPath(self.pathlib.normpath(self))

    def expand_user(self):
        return DayuPath(self.pathlib.expanduser(self))

    def expand_var(self):
        return DayuPath(self.pathlib.expandvars(self))

    def expand(self):
        new_path = self.pathlib.expanduser(self)
        new_path = self.pathlib.expandvars(new_path)
        new_path = self.pathlib.normpath(new_path)
        return DayuPath(new_path)

    @property
    def parent(self):
        return DayuPath(self.pathlib.dirname(self))

    @property
    def name(self):
        return DayuPath(self.pathlib.basename(self))

    @property
    def stem(self):
        return DayuPath(self.pathlib.splitext(self.name)[0])

    @property
    def ext(self):
        return DayuPath(self.pathlib.splitext(self)[1])

    @property
    def root(self):
        match = WIN32_DRIVE_REGEX.match(self)
        if match:
            return DayuPath(match.group(1))
        match = UNC_REGEX.match(self)
        if match:
            return DayuPath(match.group(1))
        if self.startswith('/'):
            return DayuPath('/')
        return None

    @property
    def components(self):
        result = [self.root]
        rest_parts = self[len(self.root):].split('/')
        non_empty_parts = [c for c in rest_parts if c]
        result.extend(non_empty_parts)
        return result

    def ancestor(self, n):
        current = self
        for i in range(n):
            current = current.parent
        return current

    def child(self, *children):
        for child in children:
            if self.pathlib.sep not in child:
                continue
            if self.pathlib.pardir != child:
                continue
            if self.pathlib.curdir != child:
                continue
            if '/' not in child:
                continue
            if self.pathlib.altsep and self.pathlib.altsep in child:
                raise ValueError('unsafe string in {}'.format(child))
        new_path = self.pathlib.join(self, *children)
        return DayuPath(new_path)

    @classmethod
    def cwd(cls):
        return cls(os.getcwd())

    def absolute(self):
        return DayuPath(self.pathlib.abspath(self))

    def resolve(self):
        return DayuPath(self.pathlib.realpath(self))

    def listdir(self, regex_pattern=None, ext_filters=None, only_name=False):
        result = os.listdir(self)
        if regex_pattern:
            compiled_regex = re.compile(regex_pattern)
            result = (f for f in result if compiled_regex.match(f))
        if ext_filters:
            result = (f for f in result if f.ext.lower() in ext_filters)
        if not only_name:
            result = (self.child(f) for f in result)

        return sorted(result)

    def walk(self, topdown=True, onerror=None, followlinks=False):
        for root, sub_folders, sub_files in os.walk(self, topdown=topdown,
                                                    onerror=onerror,
                                                    followlinks=followlinks):
            yield root, sub_folders, sub_files

    def state(self):
        return os.stat(self)

    def lstate(self):
        return os.lstat(self)

    def exists(self):
        return self.pathlib.exists(self)

    def lexists(self):
        return self.pathlib.lexists(self)

    def isfile(self):
        return self.pathlib.isfile(self)

    def isdir(self):
        return self.pathlib.isdir(self)

    def islink(self):
        return self.pathlib.islink(self)

    def ismount(self):
        return self.pathlib.ismount(self)

    def atime(self):
        return self.pathlib.getatime(self)

    def ctime(self):
        return self.pathlib.getctime(self)

    def mtime(self):
        return self.pathlib.getmtime(self)

    def size(self):
        return self.pathlib.getsize(self)

    def chmod(self, mode=0o755):
        os.chmod(self, mode)

    if hasattr(os, 'chown'):
        def chown(self, uid, gid):
            os.chown(self, uid, gid)

    def mkdir(self, parents=False, mode=0o777):
        if self.exists():
            return
        if parents is True:
            os.makedirs(self, mode)
        else:
            os.mkdir(self, mode)

    def rmdir(self, parents=False):
        if not self.exists():
            return
        if parents is True:
            os.removedirs(self)
        else:
            os.rmdir(self)

    def remove(self):
        if self.lexists():
            os.remove(self)

    def rename(self, new_name, parents=False):
        if parents is True:
            os.renames(self, new_name)
        else:
            os.rename(self, new_name)

    if hasattr(os, 'link'):
        def hardlink(self, newpath):
            os.link(self, newpath)

    if hasattr(os, 'symlink'):
        def write_link(self, link_content):
            os.symlink(link_content, self)

    def copy(self, dst, times=False, permission=False):
        shutil.copyfile(self, dst)
        if times or permission:
            self.copy_stat(dst, times, permission)

    def copy_stat(self, dst, times=True, permission=True):
        st = os.stat(self)
        if hasattr(os, 'utime') and times:
            os.utime(dst, (st.st_atime, st.st_mtime))
        if hasattr(os, 'chmod') and permission:
            m = stat.S_IMODE(st.st_mode)
            os.chmod(dst, m)

    def rmtree(self, parents=False):
        if self.isfile() or self.islink():
            os.remove(self)
        elif self.isdir():
            shutil.rmtree(self)
        if not parents:
            return
        p = self.parent
        while p:
            try:
                os.rmdir(p)
            except os.error:
                break
            p = p.parent

    @property
    def frame(self):
        """
        返回解析出的帧数
        :return: int 类型。如果没有解析成功，返回-1
        """
        if self.ext.lower() in tuple(EXT_SINGLE_MEDIA.keys()):
            return -1

        match = FRAME_REGEX.match(self.stem)
        if match:
            return int(match.group(1))
        return -1

    @property
    def udim(self):
        frame = self.frame
        if not frame:
            return None
        if 1000 <= frame <= 1099:
            return frame
        else:
            return None

    @property
    def version(self):
        match = VERSION_REGEX.match(self)
        if match:
            return match.group(1)
        return None

    @property
    def pattern(self):
        """
        提取出当前路径的pattern 标识。
        支持 %0xd，####，$Fn 这三种形式
        :return: 如果匹配成功，返回匹配的pattern string；否则返回None
        """
        match = PATTERN_REGEX.match(self.stem)
        return match.group(1) or match.group(3) or match.group(4) if match else None

    def to_pattern(self, pattern='%'):
        """
        将绝对路径转换为pattern 形式的路径。
        :param pattern: '%' 表示变成%04d 类型的路径；'#' 表示变成#### 类型类型的路径；'$'表示变成$F4 类型的路径
        :return: DayuPath 对象
        """
        if self.ext and self.ext.lower() in tuple(EXT_SINGLE_MEDIA.keys()):
            return self

        pattern_match = PATTERN_REGEX.match(self.stem)
        if pattern_match:
            if pattern_match.group(1):
                return self.__convert_percentage_pattern(pattern, pattern_match)
            if pattern_match.group(3):
                return self.__convert_sharp_pattern(pattern, pattern_match)
            if pattern_match.group(4):
                return self.__convert_dollar_pattern(pattern, pattern_match)
            return self

        else:
            match = FRAME_REGEX.match(self.stem)
            if match:
                return self.__convert_normal_frame_pattern(match, pattern)
            else:
                return self

    def __convert_normal_frame_pattern(self, match, pattern):
        replace_string = self.__get_pattern(pattern, len(match.group(1)))
        new_name = self.name[:match.start(1)] + replace_string + self.name[match.end(1):]
        return DayuPath(self.parent + '/' + new_name)

    def __convert_dollar_pattern(self, pattern, pattern_match):
        match = pattern_match.group
        pattern_ = self.__get_pattern(pattern, (match(5) if match(5) else 1))
        return DayuPath(self.replace(match(4), pattern_))

    def __convert_sharp_pattern(self, pattern, pattern_match):
        match = pattern_match.group
        if pattern == '#':
            return self
        pattern_ = self.__get_pattern(pattern, len(match(3)))
        return DayuPath(self.replace(match(3), pattern_))

    @staticmethod
    def __get_pattern(pattern, value):
        match = EXT_PATTERN.get(pattern, EXT_PATTERN['%'])
        if match:
            return match.format(value)
        return '#' * int(value)

    def __convert_percentage_pattern(self, pattern, pattern_match):
        match = pattern_match.group
        mappings = {
            '#': '#' * int(match(2) if match(2) else 1),
            '$': '$F{}'.format(int(match(2) if match(2) else 1))
        }
        frame = mappings.get(pattern)
        if frame:
            return DayuPath(self.replace(match(1), frame))
        return self

    def escape(self):
        return re.sub("(!|\$|#|&|\"|\'|\(|\)| |\||<|>|`|;)", r'\\\1', self)

    def restore_pattern(self, frame):
        """
        将pattern 化的序列帧，回复成为正常的帧数据对路径
        :param frame: int，可以是任意的正整数
        :return: DayuPath 对象
        """
        if frame is None:
            return self

        if int(frame) < 0:
            return self

        match = PATTERN_REGEX.match(self.name)
        if match:
            if match.group(1):
                return DayuPath(self.replace(match.group(1),
                                             '{{:0{frame_padding}d}}'.format(
                                                     frame_padding=int(match.group(2) if match.group(2) else 1)).format(
                                                     frame)))
            elif match.group(3):
                return DayuPath(self.replace(match.group(3),
                                             '{{:0{frame_padding}d}}'.format(
                                                     frame_padding=len(match.group(3))).format(frame)))
            elif match.group(4):
                return DayuPath(self.replace(match.group(4),
                                             '{{:0{frame_padding}d}}'.format(
                                                     frame_padding=(match.group(5) if match.group(5) else 1)).format(
                                                     frame)))
        else:
            return self

    def rename_sequence(self, dst_path, start=None, step=1, parents=False,
                        keep_missing=False):
        if (not self.pattern) and (not dst_path.pattern):
            self.rename(dst_path, parents=parents)
            return

        if self.pattern and self.frames and dst_path.pattern:
            start = start if start else self.frames[0]
            prev_frame = self.frames[0]
            for i in self.frames:
                if keep_missing:
                    start += (i - prev_frame)
                    start_ = dst_path.restore_pattern(start)
                    self.restore_pattern(i).rename(start_, parents=parents)
                    prev_frame = i
                else:
                    start_ = dst_path.restore_pattern(start)
                    self.restore_pattern(i).rename(start_, parents=parents)
                    start += step
            return

        raise DayuPathBaseError('maybe one of following errors: \n'
                                '* source path without frames \n'
                                '* source path is a pattern, but dst path is '
                                'not a pattern\n')

    def copy_sequence(self, dst_path, start=None, step=1,
                      times=False, permission=False, parents=False,
                      keep_missing=False):
        if (not self.pattern) and (not dst_path.pattern):
            if parents:
                dst_path.parent.mkdir(parents=True)
            self.copy(dst_path, times=times, permission=permission)
            return

        if self.pattern and self.frames and dst_path.pattern:
            if parents:
                dst_path.parent.mkdir(parents=True)
            start = start if start else self.frames[0]
            prev_frame = self.frames[0]
            for i in self.frames:
                if keep_missing:
                    start += (i - prev_frame)
                    self.restore_pattern(i).copy(dst_path.restore_pattern(start),
                                                 times=times,
                                                 permission=permission)
                    prev_frame = i
                else:
                    self.restore_pattern(i).copy(dst_path.restore_pattern(start),
                                                 times=times,
                                                 permission=permission)
                    start += step
            return

    def scan(self, recursive=False, regex_pattern=None, ext_filters=None,
             function_filter=None, ignore_invisible=True):

        scan_path, file_flag = (self, False) if self.isdir() else (self.parent, True)
        compiled_regex = re.compile(regex_pattern) if regex_pattern else None
        for root, sub_folders, sub_files in os.walk(scan_path):
            seq_list = {}
            if ignore_invisible:
                all_files = (DayuPath(root).child(f) for f in sub_files if not f.startswith(SCAN_IGNORE['start']))
            else:
                all_files = (DayuPath(root).child(f) for f in sub_files)

            avaliable_files = all_files
            if regex_pattern:
                avaliable_files = (f for f in all_files if (compiled_regex.match(f)))
            if ext_filters:
                avaliable_files = (f for f in all_files if f.lower().endswith(ext_filters))
            if function_filter:
                avaliable_files = (f for f in all_files if function_filter(f))

            for single_file in avaliable_files:
                pattern_path = single_file.absolute().to_pattern()
                frames_list = seq_list.setdefault(pattern_path, [])
                if single_file != pattern_path:
                    bisect.insort(frames_list, single_file.frame)

            if file_flag:
                k = self.absolute().to_pattern()
                v = seq_list.get(k, None)
                if v is not None:
                    k.frames = v
                    k.missing = (sorted(set(range(v[0], v[-1] + 1)) - set(v))) if v else []
                    yield k
                raise StopIteration

            if seq_list:
                for k, v in seq_list.items():
                    k.frames = v
                    k.missing = (sorted(set(range(v[0], v[-1] + 1)) - set(v))) if v else []
                    yield k

            if not recursive:
                raise StopIteration

    def _show_in_win32(self, show_file=False):
        if show_file:
            os.startfile(self)
        else:
            os.startfile(self if self.isdir() else self.parent)

    def _show_in_darwin(self, show_file=False):
        if show_file:
            subprocess.Popen('osascript -e \'tell application "Finder" to reveal ("{}" as POSIX file)\''.format(self),
                             shell=True)
        else:
            subprocess.Popen(['open', self if self.isdir() else self.parent])

    def _show_in_linux2(self, show_file=False):
        subprocess.Popen(['xdg-open', self if self.isdir() else self.parent])

    def show(self, show_file=False):
        '''
        在不同的操作系统中直接弹出窗口，显示文件所在的路径
        :param show_file: 如果希望显示的是某个具体的文件，使用True；如果希望显示路径的上层文件夹，使用False
        :return:
        '''
        import sys
        sub_func = getattr(self, '_show_in_{}'.format(sys.platform), None)
        if sub_func:
            sub_func(show_file=show_file)
