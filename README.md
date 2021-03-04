# [FreeOpenWrite](https://gitee.com/msandrew/freeopenwrite) 
# 简介
- 本项目 `FreeOpenWrite` 是在 [MrDoc：https://gitee.com/zmister/MrDoc](https://gitee.com/zmister/MrDoc) 的基础上做的更新，倾向于个人使用，
感谢 [@zmister](http://gitee.com/zmister)

- 本项目侧重点在一文多发，在 `mrdoc` 的基础上进行的开发。
- 可以自己部署，也可以注册登录 `demo` 网站 [http://freeow.andrewblog.cn](http://freeow.andrewblog.cn)
- 注册的用户为普通用户,可以体验增加平台 `cookie`, 一键分发，查看分发数据，删除分发的文章
- 图床管理功能需要超级管理员权限，下一步会将图床管理放到个人中心。供用户自行配置
- 文章底部模板配置功能。配置通用的底部模板

不懂如何部署，如何使用的请查看源仓库

### To-do
- [x] 已支持平台
  - [x] CSDN
  - [x] 博客园
  - [x] 思否
  - [x] 知乎
- [ ] 待支持平台
  - [ ] 简书
  - [ ] 掘金
  - [ ] 开源中国
  - [ ] 腾讯云社区
  - [ ] 今日头条

- [x] 已支持图床
  - [x] 七牛云图床

欢迎提 `issues`

支持项目

![](http://img.andrewblog.cn/freeopenwrite/%E5%BE%AE%E4%BF%A1%E5%9B%BE%E7%89%87_20210303174504_1614764937.jpg)![](http://img.andrewblog.cn/freeopenwrite/%E5%BE%AE%E4%BF%A1%E5%9B%BE%E7%89%87_20210303174748_1614764931.jpg)


# 超级管理员新增渠道管理

- 发布平台管理
  - 目前仅支持 `CSDN` 、`博客园`、`思否`。后续会继续增加新的渠道
  - 目前需要手动复制相关平台的 cookie。思否需要复制 token
  - 新增、删除以及开关操作。后续会屏蔽掉新增以及删除操作。
  - 新增的时候名字必须和我上面的一样。

![](http://img.andrewblog.cn/mrdoc/2021-02-24_221458.png-gg)

# 超级管理员新增图床管理功能

![](http://img.andrewblog.cn/mrdoc/2021-02-24_222048.png-gg)

- 图床管理
  - 当前仅有七牛云的图床配置
  - 配置完成需要设置为默认图床，文档中才会使用。取消默认会将图片上传到服务器
  - 后续将优化这部分，增加配置读取，增加其他常用的图床等

# 个人中心新增 cookie 管理功能

![](http://img.andrewblog.cn/mrdoc/2021-02-24_222532.png-gg)

- cookie 管理
  
  - 新增 cookie   需要手动输入相关平台的 `cookie`，选择平台，点击确定即可
    
    ![](http://img.andrewblog.cn/mrdoc/2021-02-25_091904.png-gg)
    
    - CSDN 打开 CSDN，登陆，点击写文章，F12，点击刷新页面，点击第一个请求，找到 cookie，复制所有内容。也就是 `cookie：` 后的所有内容
    - `CSDN` 渠道分发会自动上传文章中的图片到 `CSDN`，避免出现图片 404。如果图片中的文章本身就是 404，则会按照原文直接上传
    
    ![](http://img.andrewblog.cn/mrdoc/2021-02-25_091904.png-gg)
    
    - 博客园（类似 CSDN，登陆后复制）
    - 思否（需要复制 Token）
      
      - 登陆打开写文章页面，打开控制台 F12，刷新页面。找到下面的链接 `https://gateway.segmentfault.com/article?query=prepare&draft_id=&freshman=1`  ，复制请求头中的 token
        ![](http://img.andrewblog.cn/mrdoc/2021-02-25_091905.png-gg)
  - 更新 `cookie` ， cookie 失效后更新。
  - 发布文章
    ![](http://img.andrewblog.cn/mrdoc/2021-02-25_092523.png-gg)
    ![](http://img.andrewblog.cn/mrdoc/2021-02-25_092624.png-gg)
    点击确定，弹出层消失，继续点击确定。就会进行分发操作。

---

# 2021-02-25 更新

## 个人中心新增文档底部通用模板配置功能

![](http://img.andrewblog.cn/mrdoc/2021-02-25_195152.png-gg)

- 文本格式为 `markdown` 格式
- 添加需要设置为默认，才会在分发的时候自动增加到文章的底部
- 该功能仅会在分发文章的时候，添加文章底部。网站保存的内容不会改变。
- 删除通用的底部模板

# 2021-03-03  更新

## cookie 管理界面增加一键发布功能

- 点击一键发布，会自动发布到当前用户下的所有平台
- 新增知乎渠道发布以及删除功能

## 新增已发布数据管理

## todo
- [x] 删除已发布数据
- [x] 修复添加不支持的平台成功的错误
- [ ] 更新发布文章的阅读数、点赞数、评论数
- [ ] 批量删除已发布数据
- [ ] 已发布数据的筛选功能

# 2021-03-04  更新

 - 更新页面显示内容
 - `cookie` 管理模型、图床管理模型更新到 `app_doc` 目录下
 - 图床配置更新到个人中心，每个人可单独配置
 - 优化代码逻辑
