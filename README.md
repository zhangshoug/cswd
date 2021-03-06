
# CSWD

A股网络数据工具。
+ 解析提取网络数据
+ 本地化存储
+ 数据刷新

## 安装

+ 克隆到本地
+ 进入安装环境，转移至安目录后执行

`>>> python setup.py install


## 测试

+ 转至测试目录执行

`>>> pytest -v`

## 初始化

1. 进入目标环境
2. 执行初始化

`>>> init-stock-data`

+ 警告：如果输入`yes`,保留原文件数据，否则将删除原文件数据。
+ 用时：整个过程预计耗时24小时，根据个人网络环境及计算机配置，用时有较大差异。
+ 建议：使用任务计划程序后台执行。
+ 如果初始化时提取网页速度变慢，使用"Ctrl+C"中断后，再次执行，此时只需要选择保留原数据即可。

## 日常刷新

1. 刷新股票代码集，标识暂停上市、退市状态
2. 添加新增指数和股票日线数据
3. 添加融资融券数据
4. 根据公告解析当日发布财报的股票代码，添加相关代码的财务报告及财务指标数据

`>>> daily-refresh`

+ 用时：整个过程预计耗时20分钟，根据个人网络环境及计算机配置，用时有较大差异。
+ 建议：使用任务计划程序后台执行。

## 设置后台任务(Ubuntu)

1. 转移至”bg_tasks.cron“所在路径

`$cd <path><to><crontabfile>`

2. 运行

`$crontab bg_tasks.cron`

## 设置后台任务(Win10)

1. 执行路径
	+ ![自动刷新](https://github.com/liudengfeng/cswd/blob/master/images/后台刷新.PNG)

	+ 选项`起始于`路径为："<安装环境目录>/Scripts"

	+ ![参考](https://github.com/liudengfeng/cswd/blob/master/images/文件路径.PNG)

2. 后台执行
	+ ![隐藏执行](https://github.com/liudengfeng/cswd/blob/master/images/隐藏执行.PNG)

	+ 需要系统管理权限

	+ 输入登陆密码

	+ 如果不需要观察运行结果，请使用此选项