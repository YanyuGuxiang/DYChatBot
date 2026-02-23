# DYChatBot 技术实现方案

> spec: `specs/001-core-functionality/spec.md`
> constitution: `.claude/constitution.md`
> 日期: 2026-02-23

---

## 1. 技术上下文总结

### 1.1 技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| 浏览器自动化 | `playwright` (async API) | spec 指定；项目唯一第三方依赖 |
| 并发模型 | `asyncio` | 标准库；每个账号一个 `BrowserContext`，通过 `asyncio.gather` 并行 |
| 配置管理 | `json`（标准库） | spec 指定 `config.json`；无需引入 pydantic 等 |
| 日志 | `logging`（标准库） | `TimedRotatingFileHandler` 按日轮转 + `StreamHandler` 控制台 |
| 邮件通知 | `smtplib` + `email`（标准库） | 无需第三方依赖 |
| Cookie 持久化 | `json`（标准库） + Playwright `context.storage_state()` | Playwright 原生支持 |
| 打包 | `PyInstaller` | spec 指定；打包为单个 .exe |

### 1.2 关键设计决策

- **异步优先**: 全部使用 `playwright.async_api`，主循环为 `asyncio.run()`
- **无 ORM / 无数据库**: 所有状态保持在内存中，Cookie 通过 JSON 文件持久化
- **无抽象基类**: 遵循宪法第一条（简单性），模块间通过函数调用和数据类协作，不引入 ABC 接口层
- **自定义异常体系**: 遵循宪法第三条，定义业务异常与系统异常的层次结构

---

## 2. 合宪性审查

逐条对照 `constitution.md` 的原则进行审查：

### 第一条：简单性原则

| 条款 | 审查结论 | 说明 |
|------|----------|------|
| 1.1 YAGNI | ✅ 合规 | 仅实现 spec 中明确要求的 5 个核心功能（登录、导航、监控、回复、多账号），不添加额外功能 |
| 1.2 标准库优先 | ✅ 合规 | 唯一第三方依赖为 `playwright`（spec 指定）；配置用 `json`、日志用 `logging`、邮件用 `smtplib`、路径用 `pathlib` |
| 1.3 反过度工程 | ✅ 合规 | 不引入设计模式（工厂、策略等）；不使用 ABC 抽象层；模块间直接函数调用 |

### 第二条：测试先行铁律

| 条款 | 审查结论 | 说明 |
|------|----------|------|
| 2.1 TDD 循环 | ✅ 合规 | 后续 task.md 中每个任务将遵循 Red-Green-Refactor 循环 |
| 2.2 表格驱动 | ✅ 合规 | 单元测试使用 `pytest.mark.parametrize` 实现表格驱动 |
| 2.3 拒绝 Mocks | ⚠️ 部分例外 | Playwright 浏览器操作无法在 CI 中使用真实浏览器进行集成测试，此部分需使用 mock；配置加载、邮件通知等模块可编写真实集成测试 |

### 第三条：明确性原则

| 条款 | 审查结论 | 说明 |
|------|----------|------|
| 3.1 错误处理 | ✅ 合规 | 定义自定义异常层次（见 3.2 节）；所有异常使用 `raise ... from err` 保留溯源链 |
| 3.2 无全局变量 | ✅ 合规 | 配置通过参数传入各模块；Bot 状态封装在 `AccountBot` 类实例中；无模块级可变状态 |

### 第四条：单一职责原则

| 条款 | 审查结论 | 说明 |
|------|----------|------|
| 4.1 包的内聚 | ✅ 合规 | `core/` 下按职责拆分：`bot.py`（编排）、`auth.py`（登录/会话）、`navigator.py`（导航）、`monitor.py`（监控）；`utils/` 下按功能拆分 |
| 4.2 接口隔离 | ✅ 合规 | 各模块暴露小而明确的公共函数/方法，不设计"上帝类" |

---

## 3. 项目结构细化

### 3.1 目录结构

```
DYChatBot/
├── core/
│   ├── __init__.py
│   ├── bot.py              # AccountBot 类：单账号生命周期编排
│   ├── auth.py             # 登录、Cookie 持久化、登录态检测
│   ├── navigator.py        # 页面导航（首页→顾客咨询→抖音私信）
│   ├── monitor.py          # 消息监控轮询逻辑
│   └── exceptions.py       # 自定义异常定义
├── utils/
│   ├── __init__.py
│   ├── config.py           # 配置文件加载与校验
│   ├── notifier.py         # SMTP 邮件通知
│   └── logger.py           # 日志初始化配置
├── tests/                  # 测试目录
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_notifier.py
│   ├── test_auth.py
│   ├── test_navigator.py
│   └── test_monitor.py
├── config.json             # 运行时配置
├── main.py                 # 程序入口
├── pyproject.toml
└── CLAUDE.md
```

### 3.2 自定义异常体系

```
DYChatBotError (base)
├── ConfigError              # 配置文件缺失、格式错误、字段校验失败
├── AuthError                # 登录失败（凭证错误、验证码等）
│   └── SessionExpiredError  # 登录态失效
├── NavigationError          # 页面导航失败（元素未找到、超时）
└── NotificationError        # 邮件发送失败
```

所有异常继承自 `Exception`，使用 `raise ... from err` 保留异常链。

### 3.3 模块职责与依赖关系

#### `main.py` — 程序入口

- 职责：加载配置 → 初始化日志 → 为每个账号创建 `AccountBot` → `asyncio.gather` 并行启动
- 依赖：`utils.config`、`utils.logger`、`core.bot`

#### `core/bot.py` — AccountBot 类

- 职责：单账号完整生命周期编排（登录 → 导航 → 监控循环），异常重试与邮件告警的顶层协调
- 依赖：`core.auth`、`core.navigator`、`core.monitor`、`utils.notifier`
- 关键方法：
  - `async run()`: 主循环入口
  - `async _ensure_authenticated()`: 确保登录态有效（调用 auth 模块）
  - `async _handle_fatal_error()`: 超过重试次数后发送邮件并停止

#### `core/auth.py` — 登录与会话管理

- 职责：
  - 创建浏览器实例和 BrowserContext
  - Cookie 保存/恢复（`context.storage_state()` / `browser.new_context(storage_state=...)`)
  - 账号密码登录流程（填写表单、勾选协议、点击登录）
  - 登录态失效检测（URL 跳转检测 + 页面文本检测）
- 依赖：`playwright.async_api`、`core.exceptions`
- Cookie 存储路径：`cookies/{account_name}.json`（相对于可执行文件所在目录）

#### `core/navigator.py` — 页面导航

- 职责：
  - 优先尝试 `direct_url` 直达
  - 直达失败时回退：点击「顾客咨询」→ 监听 popup → 点击「抖音私信」→ 等待用户列表容器加载
- 依赖：`playwright.async_api`、`core.exceptions`

#### `core/monitor.py` — 消息监控与自动回复

- 职责：
  - 轮询用户列表前 N 个用户项
  - 检测未读标记（`.byted-badge-type-danger`）
  - 点击用户 → 等待聊天窗口 → 点击快捷回复按钮
  - 去重：已回复用户在本轮不重复处理
- 依赖：`playwright.async_api`、`core.exceptions`

#### `utils/config.py` — 配置管理

- 职责：读取 `config.json`，校验必填字段，返回类型化的配置数据（`dataclass` 或 `TypedDict`）
- 依赖：`json`（标准库）、`pathlib`（标准库）、`core.exceptions`

#### `utils/notifier.py` — 邮件通知

- 职责：通过 SMTP SSL 发送告警邮件
- 依赖：`smtplib`、`email`（标准库）、`core.exceptions`

#### `utils/logger.py` — 日志配置

- 职责：初始化 `logging`，配置控制台 + 文件双输出，文件按日期轮转
- 依赖：`logging`（标准库）、`pathlib`（标准库）

### 3.4 依赖关系图

```
main.py
  ├── utils/config.py        ← json, pathlib
  ├── utils/logger.py         ← logging, pathlib
  └── core/bot.py             ← 编排层
        ├── core/auth.py      ← playwright, pathlib, json
        ├── core/navigator.py ← playwright
        ├── core/monitor.py   ← playwright
        └── utils/notifier.py ← smtplib, email

core/exceptions.py            ← 被所有 core/ 和 utils/ 模块引用（无外部依赖）
```

依赖方向：`main` → `core/bot` → `core/*` + `utils/*`，无循环依赖。

### 3.5 并发模型

- 每个账号对应一个 `AccountBot` 实例，通过 `asyncio.gather(*tasks, return_exceptions=True)` 并行运行
- 单个账号异常不影响其他账号（`return_exceptions=True` + 各 Bot 内部 try/except）
- 各 Bot 实例之间无共享状态，无需锁机制
- 竞态条件风险：**无**。各账号独立浏览器实例、独立 Cookie 文件、独立日志 logger name，不存在共享可变状态

### 3.6 重试策略

统一的重试逻辑封装在 `core/bot.py` 的 `run()` 方法中：

- 登录重试：最多 `login_max_retries` 次（默认 3）
- 元素等待超时：`element_wait_timeout_seconds`（默认 30s）
- 元素操作重试：最多 `element_max_retries` 次（默认 3）
- 超过最大重试次数 → 调用 `utils/notifier.py` 发送邮件 → 停止该账号任务

---

## 4. 关键技术要点

### 4.1 Cookie 持久化方案

```
登录成功 → context.storage_state(path="cookies/{name}.json")
下次启动 → browser.new_context(storage_state="cookies/{name}.json")
恢复后验证 → 访问首页，检查是否跳转到登录页
验证失败 → 删除 cookie 文件，走账号密码登录流程
```

### 4.2 登录态失效被动检测

在 `monitor.py` 的每次轮询操作中，若出现以下任一情况，抛出 `SessionExpiredError`：

1. 元素等待超时（可能是页面已跳转）
2. 当前 URL 包含 `/login`
3. 页面存在 `//div[text()="登录抖音来客"]` 元素

`bot.py` 捕获 `SessionExpiredError` 后触发重新登录流程。

### 4.3 新标签页处理

点击「顾客咨询」会打开新标签页，使用 Playwright 的 `page.expect_popup()` 上下文管理器捕获：

```
async with page.expect_popup() as popup_info:
    await page.click(顾客咨询选择器)
new_page = await popup_info.value
```

后续所有操作在 `new_page` 上进行。
