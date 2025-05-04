# 指尖水务余额接入homeassistant

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

# 抓包简要说明

### 抓包app
![47247ac8751dc9924f7e169cd07aec7](https://github.com/user-attachments/assets/d710987c-af4b-49ed-8df1-2e4c571e9ad7)

### 需要填入的所对应的抓包值
![image](https://github.com/user-attachments/assets/de564252-0f4d-42c9-bc2b-549655ea7aee)

### 集成展示
  
![image](https://github.com/user-attachments/assets/40821a64-45bc-4562-8307-e8f7bf1fbaf3)


