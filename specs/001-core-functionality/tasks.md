# DYChatBot 任务分解清单

> spec: `specs/001-core-functionality/spec.md`
> plan: `specs/001-core-functionality/plan.md`
> constitution: `.claude/constitution.md`
> 日期: 2026-02-23

**标记说明：**
- `[P]` = 可与同阶段内其他 `[P]` 任务并行执行
- `[S]` = 串行，必须等待前置任务完成
- 每个实现任务前必须先完成对应的测试任务（TDD 铁律）

---

## 阶段 0：项目脚手架 (Scaffolding)

### Task 0.1 [S] — 创建项目目录结构与 `__init__.py`

- **文件**: `core/__init__.py`, `utils/__init__.py`, `tests/__init__.py`
- **内容**: 创建三个包目录及空 `__init__.py` 文件
- **验收**: 目录存在，`import core`, `import utils` 不报错

---

## 阶段 1：基础层 (Foundation)

> 本阶段构建所有上层模块的公共依赖：异常体系、配置加载、日志、邮件通知。

### Task 1.1 [S] — 编写 `core/exceptions.py` 的测试

- **文件**: `tests/test_exceptions.py`
- **内容**:
  - 测试异常继承关系：`ConfigError`, `AuthError`, `SessionExpiredError`, `NavigationError`, `NotificationError` 均继承自 `DYChatBotError`
  - 测试 `SessionExpiredError` 继承自 `AuthError`
  - 测试异常可携带消息字符串
  - 测试 `raise ... from err` 异常链保留
- **前置**: Task 0.1

### Task 1.2 [S] — 实现 `core/exceptions.py`

- **文件**: `core/exceptions.py`
- **内容**: 定义异常层次结构
  ```
  DYChatBotError (base)
  ├── ConfigError
  ├── AuthError
  │   └── SessionExpiredError
  ├── NavigationError
  └── NotificationError
  ```
- **前置**: Task 1.1
- **验收**: `tests/test_exceptions.py` 全部通过

### Task 1.3a [P] — 编写 `utils/config.py` 的测试

- **文件**: `tests/test_config.py`
- **内容**:
  - 参数化测试：正常配置加载（完整字段）
  - 参数化测试：缺少必填字段（accounts 缺失、monitor 缺失等）→ 抛出 `ConfigError`
  - 参数化测试：字段类型错误（poll_interval 为字符串等）→ 抛出 `ConfigError`
  - 测试：配置文件不存在 → 抛出 `ConfigError`
  - 测试：JSON 格式错误 → 抛出 `ConfigError`
  - 测试：accounts 为空列表 → 抛出 `ConfigError`
  - 测试：email.enabled=false 时 SMTP 字段可省略
- **前置**: Task 1.2

### Task 1.3b [P] — 编写 `utils/logger.py` 的测试

- **文件**: `tests/test_logger.py`
- **内容**:
  - 测试：初始化后返回 logger 实例
  - 测试：日志文件在指定目录下创建
  - 测试：日志级别可配置（INFO / DEBUG）
  - 测试：日志目录不存在时自动创建
- **前置**: Task 1.2

### Task 1.3c [P] — 编写 `utils/notifier.py` 的测试

- **文件**: `tests/test_notifier.py`
- **内容**:
  - 测试：`email.enabled=false` 时调用发送函数直接返回不报错
  - 测试：SMTP 连接失败 → 抛出 `NotificationError`
  - 测试：邮件内容包含账号标识、错误类型、错误详情、发生时间
  - 测试：收件人列表为空 → 抛出 `NotificationError`
- **前置**: Task 1.2

### Task 1.4a [P] — 实现 `utils/config.py`

- **文件**: `utils/config.py`
- **内容**:
  - `load_config(path: Path) -> dict` 函数：读取 JSON、校验必填字段、返回配置字典
  - 校验逻辑：accounts 非空、monitor/retry/email/logging 各节必填字段存在且类型正确
  - 所有校验失败抛出 `ConfigError`
- **前置**: Task 1.3a
- **验收**: `tests/test_config.py` 全部通过

### Task 1.4b [P] — 实现 `utils/logger.py`

- **文件**: `utils/logger.py`
- **内容**:
  - `setup_logger(name: str, level: str, log_dir: str) -> logging.Logger` 函数
  - 配置 `StreamHandler`（控制台）+ `TimedRotatingFileHandler`（按日轮转）
  - 日志格式：`%(asctime)s [%(name)s] %(levelname)s %(message)s`
  - 自动创建日志目录
- **前置**: Task 1.3b
- **验收**: `tests/test_logger.py` 全部通过

### Task 1.4c [P] — 实现 `utils/notifier.py`

- **文件**: `utils/notifier.py`
- **内容**:
  - `send_alert(email_config: dict, account_name: str, error_type: str, error_detail: str) -> None`
  - 使用 `smtplib.SMTP_SSL` 发送邮件
  - `enabled=false` 时直接返回
  - 异常包装为 `NotificationError`
- **前置**: Task 1.3c
- **验收**: `tests/test_notifier.py` 全部通过

---

## 阶段 2：核心认证模块 (Auth)

### Task 2.1 [S] — 编写 `core/auth.py` 的测试

- **文件**: `tests/test_auth.py`
- **内容**:
  - 测试：Cookie 文件存在时调用 `restore_session` 返回 True（mock Playwright context）
  - 测试：Cookie 文件不存在时 `restore_session` 返回 False
  - 测试：`login` 函数执行完整登录流程（mock 页面元素交互）
  - 测试：登录后调用 `save_cookies` 生成 Cookie JSON 文件
  - 测试：`check_session_valid` 在 URL 含 `/login` 时返回 False
  - 测试：`check_session_valid` 在页面含「登录抖音来客」文本时返回 False
  - 测试：`check_session_valid` 正常页面返回 True
  - 测试：Cookie 目录不存在时自动创建
- **前置**: Task 1.2

### Task 2.2 [S] — 实现 `core/auth.py`

- **文件**: `core/auth.py`
- **内容**:
  - `async restore_session(context, cookie_path: Path) -> bool`：尝试从文件恢复 storage_state
  - `async login(page, username: str, password: str) -> None`：填写手机号、密码、勾选协议、点击登录
  - `async save_cookies(context, cookie_path: Path) -> None`：调用 `context.storage_state(path=...)`
  - `async check_session_valid(page) -> bool`：检测 URL 和页面文本判断登录态
  - Cookie 路径：`cookies/{account_name}.json`
- **前置**: Task 2.1
- **验收**: `tests/test_auth.py` 全部通过

---

## 阶段 3：页面导航模块 (Navigator)

### Task 3.1 [S] — 编写 `core/navigator.py` 的测试

- **文件**: `tests/test_navigator.py`
- **内容**:
  - 测试：`navigate_direct` 使用 direct_url 直达成功（mock page.goto + 等待用户列表容器）
  - 测试：`navigate_direct` 直达失败时抛出 `NavigationError`
  - 测试：`navigate_step_by_step` 完整导航路径（mock 点击顾客咨询 → popup → 点击抖音私信 → 等待容器）
  - 测试：`navigate` 优先尝试 direct_url，失败后回退到 step_by_step
  - 测试：`navigate` 在 direct_url 为空时直接走 step_by_step
  - 测试：popup 事件超时 → 抛出 `NavigationError`
- **前置**: Task 1.2

### Task 3.2 [S] — 实现 `core/navigator.py`

- **文件**: `core/navigator.py`
- **内容**:
  - `async navigate(page, direct_url: str | None, timeout: int) -> Page`：编排入口
  - `async navigate_direct(page, direct_url: str, timeout: int) -> Page`：直达 URL
  - `async navigate_step_by_step(page, timeout: int) -> Page`：点击导航路径，使用 `page.expect_popup()` 捕获新标签页
  - 等待 `.rc-virtual-list-holder-inner` 容器出现
  - 返回最终操作所在的 Page 对象
- **前置**: Task 3.1
- **验收**: `tests/test_navigator.py` 全部通过

---

## 阶段 4：消息监控模块 (Monitor)

### Task 4.1 [S] — 编写 `core/monitor.py` 的测试

- **文件**: `tests/test_monitor.py`
- **内容**:
  - 测试：`scan_users` 返回前 N 个用户项元素列表
  - 测试：`has_unread` 检测到 `.byted-badge-type-danger` 返回 True
  - 测试：`has_unread` 无未读标记返回 False
  - 测试：`reply_to_user` 执行点击用户 → 等待聊天窗口 → 点击快捷回复按钮
  - 测试：`poll_once` 扫描用户列表，对有未读消息的用户逐个调用 reply
  - 测试：`poll_once` 同一轮中多个未读用户全部处理
  - 测试：元素等待超时 + URL 含 `/login` → 抛出 `SessionExpiredError`
  - 测试：元素等待超时 + 页面含「登录抖音来客」→ 抛出 `SessionExpiredError`
- **前置**: Task 1.2

### Task 4.2 [S] — 实现 `core/monitor.py`

- **文件**: `core/monitor.py`
- **内容**:
  - `async scan_users(page, count: int) -> list`：获取前 N 个 `div.conversationItem-RaXg9G`
  - `async has_unread(user_element) -> bool`：检查子元素 `.byted-badge-type-danger`
  - `async reply_to_user(page, user_element, timeout: int) -> None`：点击用户 → 等待加载 → 点击 `div[data-log-name="「售后卡片」使用"]`
  - `async poll_once(page, config: dict) -> None`：一次完整轮询（扫描 + 检测 + 回复）
  - 超时时进行登录态检测，失效则抛出 `SessionExpiredError`
- **前置**: Task 4.1
- **验收**: `tests/test_monitor.py` 全部通过

---

## 阶段 5：账号生命周期编排 (Bot)

### Task 5.1 [S] — 编写 `core/bot.py` 的测试

- **文件**: `tests/test_bot.py`
- **内容**:
  - 测试：`AccountBot.run` 正常流程（登录 → 导航 → 轮询循环）
  - 测试：登录失败重试 N 次后调用 notifier 发送邮件并停止
  - 测试：`SessionExpiredError` 触发重新登录流程
  - 测试：重新登录超过最大重试次数后发送邮件并停止
  - 测试：导航失败重试 N 次后发送邮件并停止
  - 测试：单次轮询异常不终止整个循环（继续下一轮）
- **前置**: Task 2.2, Task 3.2, Task 4.2, Task 1.4c

### Task 5.2 [S] — 实现 `core/bot.py`

- **文件**: `core/bot.py`
- **内容**:
  - `class AccountBot`：
    - `__init__(self, account_config: dict, global_config: dict)`
    - `async run(self) -> None`：主循环入口
    - `async _ensure_authenticated(self) -> None`：Cookie 恢复 / 账号密码登录
    - `async _navigate(self) -> None`：调用 navigator 模块
    - `async _monitor_loop(self) -> None`：轮询循环，捕获 `SessionExpiredError` 触发重新登录
    - `async _handle_fatal_error(self, error_type: str, detail: str) -> None`：发送邮件通知
  - 重试计数器与最大重试次数对比逻辑
- **前置**: Task 5.1
- **验收**: `tests/test_bot.py` 全部通过

---

## 阶段 6：程序入口 (Main)

### Task 6.1 [S] — 编写 `main.py` 的测试

- **文件**: `tests/test_main.py`
- **内容**:
  - 测试：`main` 函数加载配置、初始化日志、为每个账号创建 AccountBot
  - 测试：多账号通过 `asyncio.gather` 并行启动
  - 测试：单个账号异常不影响其他账号（`return_exceptions=True`）
  - 测试：配置加载失败时程序退出并输出错误信息
- **前置**: Task 5.2, Task 1.4a, Task 1.4b

### Task 6.2 [S] — 实现 `main.py`

- **文件**: `main.py`
- **内容**:
  - `async async_main() -> None`：加载配置 → 初始化日志 → 创建 Bot 列表 → `asyncio.gather`
  - `main() -> None`：`asyncio.run(async_main())`
  - `if __name__ == "__main__": main()`
- **前置**: Task 6.1
- **验收**: `tests/test_main.py` 全部通过

---

## 阶段 7：集成验证

### Task 7.1 [S] — 创建示例 `config.json`

- **文件**: `config.json`
- **内容**: 按 spec 第 4 节格式创建示例配置文件（使用占位符值）
- **前置**: Task 1.4a

### Task 7.2 [S] — 全量测试通过 & 静态检查

- **操作**: 运行 `pytest tests/`、`mypy`、`flake8`、`black --check`
- **前置**: Task 6.2
- **验收**: 所有测试通过，无类型错误，无风格警告

---

## 任务依赖关系总览

```
阶段0: [0.1]
         │
阶段1: [1.1] → [1.2] ──┬── [1.3a] → [1.4a]  ─┐
                        ├── [1.3b] → [1.4b]  ─┤  (1.3a/b/c 可并行)
                        └── [1.3c] → [1.4c]  ─┤
                                               │
阶段2: [1.2] → [2.1] → [2.2] ────────────────┤
                                               │
阶段3: [1.2] → [3.1] → [3.2] ────────────────┤  (阶段2/3/4 可并行)
                                               │
阶段4: [1.2] → [4.1] → [4.2] ────────────────┤
                                               │
阶段5: [2.2+3.2+4.2+1.4c] → [5.1] → [5.2] ──┤
                                               │
阶段6: [5.2+1.4a+1.4b] → [6.1] → [6.2] ─────┤
                                               │
阶段7: [1.4a] → [7.1]                         │
       [6.2] → [7.2] ────────────────────────┘
```

**总计**: 20 个任务（含 8 个测试任务 + 8 个实现任务 + 2 个脚手架/配置任务 + 2 个验证任务）
