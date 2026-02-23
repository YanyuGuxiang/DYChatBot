# DYChatBot 产品需求规格说明书

## 1. 产品概述

DYChatBot 是一个基于 Playwright 的抖音来客（生意经）自动回复工具。程序自动登录抖音来客 Web 端，实时监控用户私信列表，当检测到新消息时，自动进入对话窗口并点击预设的快捷回复按钮，实现秒级自动回复。

支持多账号（多店铺）并行运行，每个账号独立一个浏览器实例。最终交付为 Windows 可执行文件（.exe）。

---

## 2. 核心功能

### 2.1 自动登录

- **登录地址**: `https://life.douyin.com/p/login`
- **登录方式**: 账号密码登录（通过配置文件提供）
- **登录步骤**:
  1. 在用户名输入框输入手机号码
  2. 在密码输入框输入密码
  3. 勾选用户协议复选框
  4. 点击登录按钮
- **登录态持久化**: 首次登录后保存 cookie/session 到本地，后续启动自动恢复登录态，免去重复登录
- **登录失效处理**: 运行过程中若检测到登录态失效，自动重新登录
  - 最大重试次数：可配置（默认 3 次）
  - 超过最大重试次数后，发送邮件通知并停止该账号的任务
- **Cookie 存储**: 每个账号独立存储在可执行文件所在目录下的 `cookies/` 目录中（如 `cookies/{account_name}.json`），该目录不存在时自动创建

### 2.2 页面导航

登录成功后，程序自动执行以下导航路径：

1. 登录成功 → 进入首页
2. 点击「顾客咨询」按钮 → 该操作会打开新标签页，程序需通过 Playwright 监听 `popup` 事件捕获新标签页并切换到该标签页继续操作
3. 在左侧菜单点击「抖音私信」 → 该页面为异步加载，需等待用户列表容器（`.rc-virtual-list-holder-inner`）出现后再进行后续操作

**页面布局说明**：「抖音私信」页面结构为——最左侧是垂直菜单栏，右侧内容区分为左半部分（用户列表）和右半部分（聊天窗口）

> 备用直达 URL（每个账号不同，在配置文件中单独配置）:
> `https://life.douyin.com/cs/web/clue_private_message/chat/session?accountId={accountId}&conGroupId={conGroupId}&groupId={groupId}&lifeAccountId={lifeAccountId}`
> 优先尝试直达 URL，若失败则回退到导航路径。

### 2.3 消息监控

- **监控范围**: 用户列表前 N 个用户（N 可配置，默认 10）
- **监控频率**: 秒级轮询（轮询间隔可配置，默认 1 秒）
- **新消息判定**: 用户列表中出现未读标记（小红点/未读数字 > 0）即视为有新消息
- **消息类型**: 不区分消息类型（文本、图片、视频、表情包等），只要有新消息就触发回复

### 2.4 自动回复

- **触发条件**: 检测到某用户有新消息（未读标记）
- **操作流程**:
  1. 点击用户列表中该用户
  2. 等待右侧聊天窗口加载完成
  3. 点击聊天窗口中的「快捷回复」按钮（页面已有的功能按钮）
  4. 确认回复发送成功
- **去重逻辑**: 同一用户一次性发送多条消息（未读数 > 1），只执行一次回复操作。若该用户后续再次发送新消息（重新出现未读标记），则再次触发回复
- **多用户处理**: 若同时有多个用户有新消息，逐个依次处理

### 2.5 多账号并行

- 支持 4~5 个账号同时运行
- 每个账号独立一个浏览器实例（非 headless，可见界面）
- 各账号任务互相独立，互不影响
- 单个账号异常不影响其他账号运行

---

## 3. 异常处理与健壮性

### 3.1 页面加载等待

- 所有页面操作前必须等待目标元素加载完成
- 设置最大等待超时（可配置，默认 30 秒）
- 超时后进行重试（重试次数可配置，默认 3 次）
- 超过最大重试次数后，发送邮件通知并停止该账号任务

### 3.2 登录态失效

- **检测方式**: 被动触发检测（非定期轮询），在以下任一情况发生时判定登录态失效：
  - 页面操作时目标元素等待超时
  - 页面 URL 跳转到登录页
  - 页面中出现"登录抖音来客"文本（XPath: `//div[text()="登录抖音来客"]`）
- 失效后自动重新登录（重试机制同 2.1）

### 3.3 邮件通知

- **方式**: SMTP 邮件发送
- **触发场景**:
  - 登录重试超过最大次数
  - 页面元素加载/操作重试超过最大次数
- **通知内容**: 包含账号标识、错误类型、错误详情、发生时间
- **配置项**: SMTP 服务器、端口、发件人邮箱、授权码、收件人邮箱列表

---

## 4. 配置文件设计

配置文件: `config.json`，位于程序同级目录。

```json
{
  "accounts": [
    {
      "name": "店铺A",
      "username": "account1",
      "password": "password1",
      "direct_url": "https://life.douyin.com/cs/web/clue_private_message/chat/session?accountId=xxx&conGroupId=xxx&groupId=xxx&lifeAccountId=xxx"
    }
  ],
  "monitor": {
    "user_list_size": 10,
    "poll_interval_seconds": 1
  },
  "retry": {
    "login_max_retries": 3,
    "element_wait_timeout_seconds": 30,
    "element_max_retries": 3
  },
  "email": {
    "enabled": true,
    "smtp_host": "smtp.qq.com",
    "smtp_port": 465,
    "sender": "your_email@qq.com",
    "auth_code": "smtp授权码",
    "receivers": ["receiver@example.com"]
  },
  "logging": {
    "level": "INFO",
    "log_dir": "logs"
  }
}
```

---

## 5. 技术方案

### 5.1 技术栈

| 组件 | 选型 | 说明 |
|------|------|------|
| 浏览器自动化 | Playwright (Python) | 支持 Chromium，API 丰富，稳定性好 |
| 并发模型 | asyncio + 多浏览器实例 | 每个账号一个 BrowserContext，异步并行 |
| 配置管理 | JSON 配置文件 | config.json |
| 日志 | logging（标准库） | 控制台输出 + 文件落盘，按日期轮转 |
| 邮件通知 | smtplib + email（标准库） | 异常告警，无需第三方依赖 |
| 打包 | PyInstaller | 打包为单个 .exe |

### 5.2 项目结构

```
DYChatBot/
├── core/                    # 核心业务逻辑
│   ├── __init__.py
│   ├── bot.py               # AccountBot 类：单账号生命周期编排
│   ├── auth.py              # 登录、Cookie 持久化、登录态检测
│   ├── navigator.py         # 页面导航（首页→顾客咨询→抖音私信）
│   ├── monitor.py           # 消息监控轮询逻辑
│   └── exceptions.py        # 自定义异常定义
├── utils/                   # 公共工具
│   ├── __init__.py
│   ├── config.py            # 配置文件加载与校验
│   ├── notifier.py          # SMTP 邮件通知
│   └── logger.py            # 日志初始化配置
├── tests/                   # 测试目录
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_notifier.py
│   ├── test_auth.py
│   ├── test_navigator.py
│   └── test_monitor.py
├── config.json              # 运行时配置
├── main.py                  # 程序入口，启动多账号并行任务
├── pyproject.toml
└── CLAUDE.md
```

### 5.3 核心流程

```
程序启动
  │
  ├─ 加载 config.json
  ├─ 初始化日志
  │
  └─ 对每个账号并行启动 ──┐
                          │
                    启动浏览器实例（可见模式）
                          │
                    尝试恢复 cookie 登录
                          │
                   ┌──成功──┴──失败──┐
                   │                 │
              直接进入首页      账号密码登录
                   │                 │
                   └───────┬─────────┘
                           │
                    导航到「抖音私信」页面
                           │
                    ┌──> 轮询用户列表（每 N 秒）
                    │      │
                    │   检测未读消息用户
                    │      │
                    │   ┌─ 无 ─┐
                    │   │      │
                    │   │  ┌─ 有 ─┐
                    │   │  │      │
                    │   │  逐个处理：
                    │   │  点击用户 → 等待加载 → 点击快捷回复
                    │   │      │
                    └───┴──────┘
```

---

## 6. 运行环境与交付

- **操作系统**: Windows
- **运行方式**: 双击 .exe 启动，控制台窗口显示实时日志
- **日志**: 同时输出到控制台和日志文件（`logs/` 目录，按日期轮转）
- **浏览器**: 可见模式（非 headless），每个账号一个独立窗口
- **Cookie 存储**: 每个账号独立存储在可执行文件所在目录下的 `cookies/` 目录中（如 `cookies/{account_name}.json`），该目录不存在时自动创建

---

## 7. 页面元素选择器

以下为各页面关键元素的实际选择器：

| 序号 | 元素 | 选择器 | 说明 |
|------|------|--------|------|
| 1 | 用户名输入框 | `input[placeholder="手机号码"]` | |
| 2 | 密码输入框 | `input[type="password"]` | |
| 3 | 用户协议复选框 | `input.life-core-check-wrapper` | 登录前必须勾选 |
| 4 | 登录按钮 | `button[type="submit"]` | |
| 5 | 顾客咨询 | XPath `//span[text()="顾客咨询"]`，兜底 `//div[./span[text()="顾客咨询"]]` | 点击后开新标签页 |
| 6 | 抖音私信 | XPath `//a[.//div[text()="抖音私信"]]` | 异步加载，需等待 |
| 7 | 用户列表容器 | `.rc-virtual-list-holder-inner` | |
| 8 | 单个用户项 | `div.conversationItem-RaXg9G` | conversationItem 为核心标识 |
| 9 | 未读标记 | `.conversationItem-RaXg9G .byted-badge-type-danger` | |
| 10 | 快捷回复按钮 | `div[data-log-name="「售后卡片」使用"]` | |
| 11 | 登录态失效标志 | XPath `//div[text()="登录抖音来客"]` | 被动检测用 |
