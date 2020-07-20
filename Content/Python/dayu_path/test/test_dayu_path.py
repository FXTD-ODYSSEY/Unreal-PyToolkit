#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Import built-in modules
from uuid import uuid4

# Import third-party modules
import pytest

# Import local modules
from dayu_path import DayuPath


@pytest.fixture(scope='module')
def mock_path():
    dayu_path = DayuPath('~').expand_user().child(uuid4().hex)
    content_list = ['first_depth_0010.1001.dpx',
                    'first_depth_0010.1002.dpx',
                    'cam_test/A001C001_180212_RG8C.9876521.exr',
                    'cam_test/A001C001_180212_RG8C.9876522.exr',
                    'cam_test/A001C001_180212_RG8C.9876523.exr',
                    'vfx_test/pl_0010_plt_v0001.1001.exr',
                    'vfx_test/pl_0010_plt_v0001.1002.exr',
                    'vfx_test/pl_0010_plt_v0001.1003.exr',
                    'not_a_sequence/abc.exr',
                    'single_media_test/pl_0010_plt_v0001.1003.mov',
                    'single_media_test/MVI1022.MP4',
                    u'single_media_test/测试中文.MP4',
                    'missing_test/dd_0090_ani_1001.jpg',
                    'missing_test/dd_0090_ani_1003.jpg',
                    'missing_test/dd_0090_ani_1005.jpg',
                    'ignore_test/._DS_store',
                    'ignore_test/..sdf',
                    'recursive_test/a_001.exr',
                    'recursive_test/a_002.exr',
                    'recursive_test/inside/b_100.exr',
                    'recursive_test/inside/b_101.exr',
                    'recursive_test/inside/b_102.exr',
                    ]
    for x in content_list:
        file_path = DayuPath(u'{}/{}'.format(dayu_path, x))
        file_path.parent.mkdir(parents=True)
        with open(file_path, 'w') as f:
            f.write('1')

    dayu_path.child('empty_folder', 'inside').mkdir(parents=True)
    return dayu_path


@pytest.mark.parametrize('test_data', [
    {
        'case': '',
        'result': None,
    },
    {
        'case': [],
        'result': None,
    },
    {
        'case': tuple(),
        'result': None,
    },
    {
        'case': set(),
        'result': None,
    },
    {
        'case': dict(),
        'result': None,
    },
    {
        'case': 'any_string',
        'result': 'any_string',
    },
    {
        'case': '/Users/andyguo/Desktop/111111111.jpg',
        'result': '/Users/andyguo/Desktop/111111111.jpg',
    },
    {
        'case': u'/Users/andyguo/Desktop/中文路径 测试.jpg',
        'result': u'/Users/andyguo/Desktop/中文路径 测试.jpg',
    },
    {
        'case': 'D:/data/test.jpg',
        'result': 'd:/data/test.jpg',
    },
    {
        'case': 'd:\\data\\test.jpg',
        'result': 'd:/data/test.jpg',
    },
    {
        'case': 'D:\\data\\test.jpg',
        'result': 'd:/data/test.jpg',
    },
    {
        'case': 'test_object',
        'result': 'd:/data/test.jpg',
    }
])
def test___new__(test_data):
    if test_data['case'] == 'test_object':
        obj = DayuPath('/Users/andyguo/Desktop/111111111.jpg')
        assert DayuPath(obj) == obj
    else:
        assert DayuPath(test_data['case']) == test_data['result']


@pytest.mark.parametrize('test_data', [
    {
        'case': '/Users/andyguo/Desktop/1.jpg',
        'result': -1,
    },
    {
        'case': '/Users/andyguo/Desktop/12.jpg',
        'result': 12,
    },
    {
        'case': '/Users/andyguo/Desktop/1001.jpg',
        'result': 1001,
    },
    {
        'case': '/Users/andyguo/Desktop/0024.jpg',
        'result': 24,
    },
    {
        'case': '/Users/andyguo/Desktop/1.mov',
        'result': -1,
    },
    {
        'case': '/Users/andyguo/Desktop/14.mov',
        'result': -1,
    },
    {
        'case': '/Users/andyguo/Desktop/v002_999.jpg',
        'result': 999,
    },
    {
        'case': '/Users/andyguo/Desktop/aaa_test.1.jpg',
        'result': -1,
    },
    {
        'case': '/Users/andyguo/Desktop/aaa_test.12.jpg',
        'result': 12,
    },
    {
        'case': '/Users/andyguo/Desktop/aaa_test.123.jpg',
        'result': 123,
    },
    {
        'case': '/Users/andyguo/Desktop/aa_v001.jpg',
        'result': -1,
    },
    {
        'case': u'/Users/andyguo/Desktop/中文 1001.jpg',
        'result': 1001,
    },
    {
        'case': u'/Users/andyguo/Desktop/pl_0010_plt_v0023.012.jpg',
        'result': 12,
    },
    {
        'case': u'/Users/andyguo/Desktop/中文 1001.jpg',
        'result': 1001,
    },
    {
        'case': u'/Users/andyguo/Desktop/中文 1001.jpg',
        'result': 1001,
    },
    {
        'case': u'/Users/andyguo/Desktop/中文 1001.jpg',
        'result': 1001,
    },
    {
        'case': u'/Users/andyguo/Desktop/中文 1001.jpg',
        'result': 1001,
    },
    {
        'case': u'/Users/andyguo/Desktop/ttt/asdfasdf/pl_0010.1012.tiff',
        'result': 1012,
    },

])
def test_frame(test_data):
    assert DayuPath(test_data['case']).frame == test_data['result']


@pytest.mark.parametrize(
    'test_data', [
        'state',
        'lstate',
        'exists',
        'lexists',
        'isfile',
        'isdir',
        'islink',
        'ismount',
        'atime',
        'ctime',
        'mtime',
        'size'
    ]
)
def test_os_functions(test_data, mock_path):
    path = DayuPath(mock_path).child('cam_test',
                                     'A001C001_180212_RG8C.9876521.exr')
    assert getattr(path, test_data) is not None


@pytest.mark.parametrize('test_data', [
    {
        'case': '/Users/andyguo/Desktop/pl_0010_plt_v0023.jpg',
        'result': None,
    },
    {
        'case': '/Users/andyguo/Desktop/pl_0010_plt_%d.jpg',
        'result': '%d',
    },
    {
        'case': '/Users/andyguo/Desktop/pl_0010_plt_%02d.jpg',
        'result': '%02d',
    },
    {
        'case': '/Users/andyguo/Desktop/pl_0010_plt_%03d.jpg',
        'result': '%03d',
    },
    {
        'case': '/Users/andyguo/Desktop/pl_0010_plt_%04d.jpg',
        'result': '%04d',
    },
    {
        'case': '/Users/andyguo/Desktop/pl_0010_plt_#.jpg',
        'result': '#',
    },
    {
        'case': '/Users/andyguo/Desktop/pl_0010_plt_##.jpg',
        'result': '##',
    },
    {
        'case': '/Users/andyguo/Desktop/pl_0010_plt_###.jpg',
        'result': '###',
    },
    {
        'case': '/Users/andyguo/Desktop/pl_0010_plt_####.jpg',
        'result': '####',
    },
    {
        'case': '/Users/andyguo/Desktop/pl_0010_plt_$F.jpg',
        'result': '$F',
    },
    {
        'case': '/Users/andyguo/Desktop/pl_0010_plt_$F2.jpg',
        'result': '$F2',
    },
    {
        'case': u'/Users/andyguo/Desktop/pl_0010_plt_$F3.jpg',
        'result': '$F3',
    },
    {
        'case': u'/Users/andyguo/Desktop/pl_0010_plt_$F4.jpg',
        'result': '$F4',
    },
    {
        'case': u'/Users/andyguo/Desktop/中文的测试$F4.jpg',
        'result': '$F4',
    },
    {
        'case': '/Users/andyguo/Desktop/pl_%04d_ani_$F4.jpg',
        'result': '%04d',
    },
    {
        'case': '/Users/andyguo/Desktop/ani_$F4.mov',
        'result': '$F4',
    },
    {
        'case': '/Users/andyguo/Desktop/abc.mov',
        'result': None,
    },
])
def test_pattern(test_data):
    assert DayuPath(test_data['case']).pattern == test_data['result']


@pytest.mark.parametrize('test_data', [
    {
        'path': '/Users/andyguo/Desktop/1.jpg',
        'pattern': None,
        'result': '/Users/andyguo/Desktop/1.jpg'
    },
    {
        'path': '/Users/andyguo/Desktop/11.jpg',
        'pattern': None,
        'result': '/Users/andyguo/Desktop/%02d.jpg'
    },
    {
        'path': '/Users/andyguo/Desktop/11.jpg',
        'pattern': '#',
        'result': '/Users/andyguo/Desktop/##.jpg'
    },
    {
        'path': '/Users/andyguo/Desktop/11.jpg',
        'pattern': '$',
        'result': '/Users/andyguo/Desktop/$F2.jpg'
    },
    {
        'path': '/Users/andyguo/Desktop/123.jpg',
        'pattern': None,
        'result': '/Users/andyguo/Desktop/%03d.jpg'
    },
    {
        'path': '/Users/andyguo/Desktop/123.jpg',
        'pattern': '#',
        'result': '/Users/andyguo/Desktop/###.jpg'
    },
    {
        'path': '/Users/andyguo/Desktop/123.jpg',
        'pattern': '$',
        'result': '/Users/andyguo/Desktop/$F3.jpg'
    },
    {
        'path': '/Users/andyguo/Desktop/1234.jpg',
        'pattern': '#',
        'result': '/Users/andyguo/Desktop/####.jpg'
    },
    {
        'path': '/Users/andyguo/Desktop/1234.jpg',
        'pattern': None,
        'result': '/Users/andyguo/Desktop/%04d.jpg'
    },
    {
        'path': '/Users/andyguo/Desktop/1234.jpg',
        'pattern': '$',
        'result': '/Users/andyguo/Desktop/$F4.jpg'
    },
    {
        'path': '/Users/andyguo/Desktop/a1234.jpg',
        'pattern': 'ss',
        'result': '/Users/andyguo/Desktop/a%04d.jpg'
    },
    {
        'path': '/Users/andyguo/Desktop/%02d.jpg',
        'pattern': '%',
        'result': '/Users/andyguo/Desktop/%02d.jpg'
    },
    {
        'path': '/Users/andyguo/Desktop/%02d.jpg',
        'pattern': '%',
        'result': '/Users/andyguo/Desktop/%02d.jpg'
    },
    {
        'path': '/Users/andyguo/Desktop/%02d.jpg',
        'pattern': '$',
        'result': '/Users/andyguo/Desktop/$F2.jpg'
    },
    {
        'path': '/Users/andyguo/Desktop/%02d.jpg',
        'pattern': '#',
        'result': '/Users/andyguo/Desktop/##.jpg'
    },
    {
        'path': '/Users/andyguo/Desktop/%03d.jpg',
        'pattern': '#',
        'result': '/Users/andyguo/Desktop/###.jpg'
    },
    {
        'path': '/Users/andyguo/Desktop/%02d.jpg',
        'pattern': '1',
        'result': '/Users/andyguo/Desktop/%02d.jpg'
    },
    {
        'path': '/Users/andyguo/Desktop/##.jpg',
        'pattern': '1',
        'result': '/Users/andyguo/Desktop/%02d.jpg'
    },
    {
        'path': '/Users/andyguo/Desktop/###.jpg',
        'pattern': '1',
        'result': '/Users/andyguo/Desktop/%03d.jpg'
    },
    {
        'path': '/Users/andyguo/Desktop/###.jpg',
        'pattern': '$',
        'result': '/Users/andyguo/Desktop/$F3.jpg'
    },
    {
        'path': '/Users/andyguo/Desktop\\$F2.jpg',
        'pattern': '%',
        'result': '/Users/andyguo/Desktop/%02d.jpg'
    },
    {
        'path': u'/Users/andyguo/Desktop\\$F3.jpg',
        'pattern': '#',
        'result': '/Users/andyguo/Desktop/###.jpg'
    },
    {
        'path': u'/Users/andyguo/Desktop\\$F3.jpg',
        'pattern': 'dd',
        'result': '/Users/andyguo/Desktop/%03d.jpg'
    },
    {
        'path': u'/Users/andyguo/Desktop/MVI1001.mov',
        'pattern': '%',
        'result': '/Users/andyguo/Desktop/MVI1001.mov'
    },
    {
        'path': u'/Users/andyguo/Desktop/MVI1001.mov',
        'pattern': '#',
        'result': '/Users/andyguo/Desktop/MVI1001.mov'
    },
])
def test_to_pattern(test_data):
    dayu_path = DayuPath(test_data['path']).to_pattern(test_data['pattern'])
    assert dayu_path == test_data['result']


@pytest.mark.parametrize(
    'test_data', [
        {
            'path': '/Users/andyguo/Desktop/sd_0010_plt_v0002.$F.jpg',
            'pattern': 12,
            'result': '/Users/andyguo/Desktop/sd_0010_plt_v0002.12.jpg'
        },
        {
            'path': '/Users/andyguo/Desktop/sd_0010_plt_v0002.$F2.jpg',
            'pattern': 12,
            'result': '/Users/andyguo/Desktop/sd_0010_plt_v0002.12.jpg'
        },
        {
            'path': '/Users/andyguo/Desktop/sd_0010_plt_v0002.$F3.jpg',
            'pattern': 12,
            'result': '/Users/andyguo/Desktop/sd_0010_plt_v0002.012.jpg'
        },
        {
            'path': '/Users/andyguo/Desktop/sd_0010_plt_v0002.$F4.jpg',
            'pattern': 1920,
            'result': '/Users/andyguo/Desktop/sd_0010_plt_v0002.1920.jpg'
        },
        {
            'path': '/Users/andyguo/Desktop/sd_0010_plt_v0002.1920.jpg',
            'pattern': None,
            'result': '/Users/andyguo/Desktop/sd_0010_plt_v0002.1920.jpg'
        }

    ]
)
def test_restore_pattern(test_data):
    path = DayuPath(test_data['path']).restore_pattern(test_data['pattern'])
    assert path == test_data['result']


def test_scan(mock_path):
    result = list(mock_path.scan())
    assert result[0] == mock_path.child('first_depth_0010.%04d.dpx')
    assert result[0].frames == [1001, 1002]
    assert result[0].missing == []

    for x in mock_path.child(u'single_media_test', u'测试中文.MP4').scan():
        assert x == mock_path.child(u'single_media_test', u'测试中文.MP4')
        assert x.frames == []
        assert x.missing == []

    for x in mock_path.child('not_a_sequence', 'abc.exr').scan():
        assert x == mock_path.child('not_a_sequence', 'abc.exr')
        assert x.frames == []
        assert x.missing == []

    assert list(mock_path.child('vfx_test', 'pl_0010_plt_v0002.1001.exr').scan()) == []
    assert list(mock_path.child('vfx_test', 'pl_0010_plt_v0002.1001.exr').scan(recursive=True)) == []
    assert list(mock_path.child('empty_folder').scan(recursive=True)) == []
    files = [x for x in mock_path.scan(recursive=True)]
    assert mock_path.child('ignore_test', '._DS_store') not in files
    assert mock_path.child('ignore_test', '..sdf') not in files
    assert mock_path.child('ignore_test', 'Thumbnail') not in files
    assert mock_path.child('ignore_test', 'temp.tmp') not in files


@pytest.mark.parametrize(
    'test_data', [
        {
            'path': '/Users/andyguo/Desktop/111.mov',
            'result': '/Users/andyguo/Desktop/111.mov'
        },
        {
            'path': '/Users/andyguo/Desktop/some words with space.mov',
            'result': '/Users/andyguo/Desktop/some\ words\ with\ space.mov'
        },
        {
            'path': 'The$!cat#&ran\"\'up()a|<>tree`;',
            'result': r'The\$\!cat\#\&ran\"\'up\(\)a\|\<\>tree\`\;'
        },
        {
            'path': u'/Users/andyguo/Desktop/中文 和 空格12234 rer.jpg',
            'result': u'/Users/andyguo/Desktop/中文\ 和\ 空格12234\ rer.jpg'
        }
    ]
)
def test_escape(test_data):
    path = DayuPath(test_data['path'])
    assert path.escape() == test_data['result']


@pytest.mark.parametrize('test_data', [
    {
        'case': '/Users/andyguo/Desktop/v001/111.mov',
        'result': 'v001',
    },
    {
        'case': '/Users/andyguo/Desktop/v001/A001C001_180212_DF3X.mov',
        'result': 'v001',
    },
    {
        'case': u'/Users/andyguo/Desktop/dd/pl_0010_plt_bga.1001.mov',
        'result': None,
    },
    {
        'case': u'/Users/andyguo/Desktop/v003/pl_0010_plt_bga_v0002.1001.mov',
        'result': 'v0002',
    },
    {
        'case': u'not a path',
        'result': None,
    },
])
def test_version(test_data):
    assert DayuPath(test_data['case']).version == test_data['result']


@pytest.mark.skip(reason='only for mac local test')
def test_root():
    assert DayuPath('/Users/andyguo/Desktop/abc.jpg').root == '/'
    assert DayuPath(
        '/Volumes/filedata/td/finder.lnk').root == '/Volumes/filedata'
    assert isinstance(DayuPath('/Volumes/filedata/td/finder.lnk').root,
                      DayuPath)


@pytest.mark.skip(reason='only for mac local test')
def test_is_network():
    assert DayuPath('/Volumes/filedata/td/finder.lnk').is_network
    assert not DayuPath('/Users/andyguo/Desktop/log.txt').is_network


@pytest.mark.skip(reason='only for mac local test')
def test_is_local():
    assert not DayuPath('/Volumes/filedata/td/finder.lnk').is_local
    assert not DayuPath('/Users/andyguo/Desktop/log.txt').is_local
