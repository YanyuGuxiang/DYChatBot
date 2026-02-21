# [DYChatBot] Python项目AI Agent协作指南

你是一位精通 Python 语言的资深软件工程师，熟悉云原生开发与软件工程最佳实践。你的任务是协助我，以高质量、可维护的方式完成本项目的开发

---

## 1. 技术栈与环境 (Tech Stack & Environment)

- **语言**: Python (>= 3.10+)
- **构建/测试/质量**:
  - **构建**: 标准 `uv` 项目默认生成 .venv 虚拟环境目录
  - **测试**: 标准 `pytest`（核心测试框架）、`unittest`（标准库测试框架）
  - **代码规范**: `black`（代码格式化）、`isort`（导入排序）
  - **静态检查**: `mypy`（类型检查）、`flake8`（代码风格检查）、`pylint`（全面代码分析）（配置文件分别为mypy.ini、.flake8、pylintrc）
  - **运行说明（Windows）**: 本项目使用uv管理项目。**[强制]** 在 Claude Code 中执行 Python 时，必须通过项目根目录下的 `__run.bat` 包裹器调用，命令格式为：
    ```bash
    cmd //c "__run.bat <脚本路径或模块参数>"
    ```
    该包裹器会自动设置 `SystemRoot` 等 Windows 环境变量并调用 `.venv` 虚拟环境中的 Python 解释器，解决 Claude Code Bash 沙箱下 Python 无法初始化的问题。禁止直接调用 `.venv/Scripts/python.exe`。
  - **运行说明（Mac os）**：本项目使用uv管理项目，若要运行 Python 文件，需要使用项目根目录.venv虚拟环境中的 Python 解释器来执行，避免使用系统全局 Python 环境导致依赖冲突或版本不匹配。可直接调用 `.venv/bin/python`。

---

## 2. 架构与代码规范 (Architecture & Code Style)

- **项目结构**: 严格遵循 Python 项目最佳实践布局（参考[https://docs.python-guide.org/writing/structure/](https://docs.python-guide.org/writing/structure/)）。核心业务逻辑必须放在`core/`目录下，对外暴露的 API 放在`api/`，公共工具放在`utils/`。
- **错误处理**: **[强制]** 自定义异常类来区分业务错误与系统错误，异常抛出时必须包含清晰的上下文信息，避免直接抛出`Exception`。捕获异常时遵循 “不吞异常” 原则。
- **日志**: **[强制]** 必须使用标准库`logging`（或第三方增强库`structlog`）进行结构化日志记录。日志信息中必须包含关键的上下文信息（如`user_id`、`trace_id`），避免使用`print()`进行日志输出。
- **接口设计**: 遵循 Python 的 “鸭子类型” 哲学，优先使用抽象基类（ABC，来自`abc`模块）定义接口契约，确保接口的单一职责，避免庞大的全能接口。同时充分利用 Python 的类型注解（Type Hints）明确接口入参与返回值类型。

---

## 3. Git与版本控制 (Git & Version Control)

- **Commit Message规范**: **[严格遵循]** Conventional Commits 规范 (https://www.conventionalcommits.org/)。
  - 格式: `<type>(<scope>): <subject>`
  - 当被要求生成commit message时，必须遵循此格式。

---

## 4. AI协作指令 (AI Collaboration Directives)

- **[原则] 优先标准库**: 在有合理的标准库解决方案时，优先使用标准库，而不是引入新的第三方依赖。
- **[流程] 审查优先**: 当被要求实现一个新功能时，你的第一步应该是先用`@`指令阅读相关代码，理解现有逻辑，并对照 constitution.md 的原则，然后再提出你的计划，待我确认后再开始编码。
- **[实践] 参数化测试**: 当被要求编写测试时，你必须优先编写**参数化测试（Parameterized Tests）**（基于`pytest.mark.parametrize`），这是本项目推崇的测试风格。
- **[实践] 并发安全**: 当你的代码中涉及到并发（`threading`、`multiprocessing`、`asyncio`）时，**必须**明确指出潜在的竞态条件风险，并解释你所使用的并发安全措施（如`threading.Lock`、`asyncio.Lock`、队列`queue.Queue`等）。
- **[产出] 解释代码**: 在生成任何复杂的代码片段后，请用注释或在对话中，简要解释其核心逻辑和设计思想。

---

## 补充说明

1. 类型注解：本项目要求所有公共函数、类方法必须添加完整的类型注解，通过`mypy`严格类型检查，提升代码可维护性和可读性。
2. 依赖管理：使用`uv`进行依赖管理，通过`pyproject.toml`统一配置项目信息、依赖和工具链，避免“依赖地狱”；运行Python文件时需调用项目根目录`.venv`虚拟环境内的解释器（若已有`.venv`文件夹可直接使用，且无需你主动创建该虚拟环境）。
3. 异步支持：如果项目涉及高并发 IO 场景，优先使用`asyncio`生态（如 FastAPI、aiohttp），遵循异步编程最佳实践，避免同步阻塞调用。