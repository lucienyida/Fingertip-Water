指尖水务接入homeassistant

# 简介
抓取指尖水务app的信息，目前只抓取余额，账单还没研究明白


# 安装
## 手动安装
1. 下载本集成的代码。
2. 将 `water_meter` 文件夹复制到 Home Assistant 的 `custom_components` 目录下。
3. 重启 Home Assistant。


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


