指尖水务接入homeassistant

# 简介
抓取指尖水务app的信息，目前只抓取余额，账单还没研究明白


# 安装
1 手动安装，下载并把文件按以下目录结构存放
custom_components/
└── water_meter/
    ├── __init__.py
    ├── sensor.py
    ├── config_flow.py
    ├── const.py
    └── manifest.json

# 配置

重启Home Assistant后：

* 进入 配置 → 集成 → 添加集成

* 搜索"指尖水务"并添加

* 输入最新抓包数据的所有字段：

名称（自定义）

水表编号：

水务公司ID：

Auth Token (Bearer token)

User ID：

AuthorizationT：

![集成配置说明](https://github.com/user-attachments/assets/3819af33-f1b0-46c4-ab86-9ae916185bbb)


