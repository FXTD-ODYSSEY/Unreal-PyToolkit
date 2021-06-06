# Unreal-PyToolkit

> 请使用上述 Git 命令来克隆仓库，确保依赖的 Python 库都拉取下来。

`git clone --recurse-submodules git@github.com:FXTD-ODYSSEY/Unreal-PyToolkit.git` 

> 说明文档链接 [链接](http://wiki.l0v0.com/unreal/PyToolkit/#/)

![工具集锦](http://cdn.jsdelivr.net/gh/FXTD-ODYSSEY/CG_wiki@gh-pages/unreal/PyToolkit/_img/01.png)

> &emsp;&emsp;工具界面使用 PySide 组件库 [dayu_widgets](https://github.com/phenom-films/dayu_widgets)     
> &emsp;&emsp;插件在 4.25 & 4.26 引擎下可以运行。        
> &emsp;&emsp;兼容 Python 2.7 和 Python 3.7

> &emsp;&emsp;使用本插件需要开启下列 Unreal 官方插件    
> + Python Editor Script Plugin     
> + Editor Scripting Utilities    
> + Sequencer Scripting    

> &emsp;&emsp;由于 Unreal Python 的官方插件是基于蓝图节点转换到 Python 调用的    
> &emsp;&emsp;所以不开启插件会导致相关的蓝图模块缺失，官方 Python 文档里面所提到的一些模块也将无法使用。    

## Python 库依赖

Content 目录下的 Python 目录默认会添加到 Python sys.path 里面   
Python 目录里面添加的依赖库如下:    
+ [tk-framework-unrealqt](https://github.com/ue4plugins/tk-framework-unrealqt) 
+ [keyboard](https://github.com/boppreh/keyboard) 
+ [fbx_python_bindings](https://github.com/FXTD-ODYSSEY/fbx_python_bindings)
+ [dayu_widgets](https://github.com/phenom-films/dayu_widgets)
+ [dayu_widgets_overlay](https://github.com/FXTD-ODYSSEY/dayu_widgets_overlay)
+ [QBinder](https://github.com/FXTD-ODYSSEY/QBinder)
+ [dayu_path](https://github.com/phenom-films/dayu_path)
+ [singledispatch](https://pypi.org/project/singledispatch/)
+ [Qt.py](https://github.com/mottosso/Qt.py)

> 附注： PySide 包整个有近 100M 大小，我全部上传到了 master 分支了，所以仓库会比较大，我预留了 码云 的仓库备份，方便用来加速。 [码云链接](https://gitee.com/ZSD_tim/Unreal-PyToolkit)    

