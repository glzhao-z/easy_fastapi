# easy_fastapi

一个面向中小型异步 API 服务的、模块化且易扩展的 FastAPI 项目模板。

> [!IMPORTANT]
> Phase 1 最小可用架构已经完成，项目可以安装、启动和测试。数据库、缓存与认证仍在规划中，暂不建议直接用于生产环境。

## 项目介绍

`easy_fastapi` 旨在减少 FastAPI 项目中重复的基础设施建设工作，为 Python 开发者提供一套结构清晰、默认配置合理、可以按需扩展的后端项目起点。

项目将围绕配置管理、应用生命周期、异常处理、日志、数据库、缓存和身份认证等常见能力提供统一实现，同时尽量避免业务代码与具体基础设施强耦合。

它不是一个功能庞杂的全栈框架，也不试图替代 FastAPI。项目更关注如何以简单、可维护的方式组织一个实际的 FastAPI 后端服务。

## 适用场景

`easy_fastapi` 计划适用于：

- 中小型 REST API 服务；
- 需要异步数据库访问的 Python 后端项目；
- 希望统一团队项目结构和工程规范的场景；
- 需要逐步接入数据库、Redis、JWT 等组件的项目；
- 希望从最小应用开始，并按业务规模扩展的项目。

以下场景可能并不适合直接使用本项目：

- 只有少量接口的一次性脚本或原型；
- 需要完整前端、后台管理系统或微服务治理平台的项目；
- 已经形成成熟内部框架和工程规范的团队。

## 设计目标

- **最小配置即可运行**：基础应用不依赖数据库、Redis 等可选组件也能启动。
- **按需启用基础设施**：数据库、缓存和认证能力可以独立安装与配置。
- **模块化组织业务**：优先按业务领域聚合代码，减少跨目录跳转。
- **统一公共能力**：集中管理配置、日志、异常和应用生命周期。
- **异步优先**：围绕 FastAPI 和 SQLAlchemy 的异步能力进行设计。
- **保持透明**：不过度封装 FastAPI、Pydantic 和 SQLAlchemy 的原生接口。
- **易于测试和维护**：从项目早期建立测试、类型检查和代码质量约束。

## 功能状态

当前已经实现：

- 应用工厂与异步生命周期管理；
- 基于环境变量和 `.env` 文件的配置管理与校验；
- `/api/v1` 路由组织与模块化示例；
- 统一异常体系和结构化错误响应；
- JSON 结构化日志、请求 ID 与访问日志；
- 健康检查；
- pytest、Ruff、mypy 和 GitHub Actions CI。

后续规划：

- SQLAlchemy 2.x 异步数据库访问；
- Alembic 数据库迁移；
- Redis 缓存访问接口；
- JWT 身份认证与 RBAC 权限控制基础能力；
- 指标、链路追踪等可观测性能力；
- Docker 容器化部署。

## 技术栈

| 技术 | 用途 | 状态 |
| --- | --- | --- |
| Python 3.11+ | 核心开发语言 | 已集成 |
| FastAPI | Web API 框架 | 已集成 |
| Pydantic v2 | 数据校验与序列化 | 已集成 |
| Pydantic Settings | 配置管理 | 已集成 |
| SQLAlchemy 2.x | ORM 与异步数据库访问 | 规划 |
| Alembic | 数据库迁移 | 规划 |
| PostgreSQL / MySQL | 可选关系型数据库 | 规划 |
| Redis | 可选缓存与数据存储 | 规划 |
| PyJWT | JWT 身份认证 | 规划 |
| Uvicorn | ASGI 服务运行 | 已集成 |
| pytest / httpx2 | 自动化测试 | 已集成 |
| Ruff / mypy | 格式化、代码检查与类型检查 | 已集成 |
| Docker | 容器化部署 | 规划 |

具体版本约束见 `pyproject.toml`，可复现依赖版本见 `uv.lock`。

## 目录结构

项目采用“业务模块优先、基础设施分层”的组织方式：

```text
easy_fastapi/
├── app/
│   ├── api/                    # API 路由入口与版本管理
│   ├── core/                   # 配置、日志、异常和生命周期
│   ├── dependencies/           # 跨模块公共依赖
│   ├── middleware/             # 请求上下文等中间件
│   ├── modules/                # 按业务领域组织的功能模块
│   │   └── example/
│   │       └── router.py       # 参考模块路由
│   ├── schemas/                # 公共请求与响应模型
│   └── main.py                 # 应用入口
├── tests/                      # 自动化测试
├── .github/workflows/ci.yml    # 持续集成
├── .env.example                # 环境变量示例
├── .gitignore
├── pyproject.toml              # 依赖和工具配置
├── uv.lock                     # 依赖锁文件
└── README.md
```

数据库、缓存等基础设施将在 Phase 2 加入，当前不会为了预留结构而创建空目录。

## 快速开始

### 环境要求

- Python 3.11 或更高版本；
- 推荐使用 [uv](https://docs.astral.sh/uv/) 管理 Python 环境和依赖。

### 安装与启动

```bash
# 1. 克隆项目
git clone https://github.com/glzhao-z/easy_fastapi.git
cd easy_fastapi

# 2. 根据锁文件安装运行与开发依赖
uv sync

# 3. 创建本地配置（Windows PowerShell 使用 Copy-Item）
cp .env.example .env

# 4. 启动开发服务
uv run uvicorn app.main:app --reload
```

服务启动后可访问：

- API 文档：`http://127.0.0.1:8000/docs`
- OpenAPI 文档：`http://127.0.0.1:8000/openapi.json`
- 健康检查：`http://127.0.0.1:8000/health`
- 示例接口：`http://127.0.0.1:8000/api/v1/examples/ping`

### 配置

所有环境变量使用 `EASY_FASTAPI_` 前缀，常用配置如下：

| 环境变量 | 默认值 | 说明 |
| --- | --- | --- |
| `EASY_FASTAPI_APP_NAME` | `easy_fastapi` | 应用名称 |
| `EASY_FASTAPI_ENVIRONMENT` | `development` | 运行环境 |
| `EASY_FASTAPI_DEBUG` | `false` | 调试模式 |
| `EASY_FASTAPI_HOST` | `127.0.0.1` | 服务监听地址 |
| `EASY_FASTAPI_PORT` | `8000` | 服务端口 |
| `EASY_FASTAPI_LOG_LEVEL` | `INFO` | 日志级别 |
| `EASY_FASTAPI_DOCS_ENABLED` | `true` | 是否启用 API 文档 |
| `EASY_FASTAPI_API_V1_PREFIX` | `/api/v1` | v1 API 前缀 |
| `EASY_FASTAPI_REQUEST_ID_HEADER` | `X-Request-ID` | 请求追踪响应头 |

完整示例见 `.env.example`。

### 代码质量与测试

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy app tests
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=85
```

GitHub Actions 会在推送到 `main` 或创建 Pull Request 时对 Python 3.11 和 3.13 执行相同检查。

## 核心约定

### 可选组件不阻塞基础应用

未启用数据库或 Redis 时，基础应用仍应能够正常启动。可选能力将通过独立依赖和配置显式开启，避免无关依赖成为运行前提。

### 业务模块优先

同一业务领域的路由、模型、服务和数据访问代码尽量放在同一模块内。只有确实被多个模块复用的能力才会提升到公共层。

### 尊重 HTTP 与框架语义

项目统一错误响应和异常处理，但不会强制包装成功响应。状态码、响应头、流式响应和 OpenAPI 描述保持 FastAPI 的原生行为。

### 显式优于隐式

自动注册、依赖注入和生命周期管理应当便于理解与调试。只有能够明显减少重复代码、且不会隐藏关键行为时，才引入自动化机制。

## Roadmap

### Phase 1：最小可用架构

- [x] 初始化项目与依赖管理；
- [x] 确定模块化目录结构；
- [x] 实现应用工厂与生命周期管理；
- [x] 实现配置管理；
- [x] 建立 API 版本与路由组织方式；
- [x] 实现统一异常和错误响应；
- [x] 实现基础日志与请求追踪；
- [x] 建立 pytest、Ruff 和类型检查；
- [x] 建立基础 CI。

### Phase 2：数据访问

- [ ] 集成 SQLAlchemy 异步会话；
- [ ] 支持 PostgreSQL；
- [ ] 评估并支持 MySQL；
- [ ] 集成 Alembic 数据库迁移；
- [ ] 集成 Redis；
- [ ] 提供健康检查和连接生命周期管理。

### Phase 3：安全认证

- [ ] 实现 JWT 签发与校验；
- [ ] 实现用户身份管理基础能力；
- [ ] 提供认证依赖；
- [ ] 实现 RBAC 权限控制基础能力；
- [ ] 增加认证与权限测试。

### Phase 4：部署与发布

- [ ] 提供 Dockerfile；
- [ ] 提供本地开发用 Compose 配置；
- [ ] 完善 CI/CD；
- [ ] 建立版本与变更记录规范；
- [ ] 完善部署文档。

### Phase 5：可选扩展

- [ ] 异步任务；
- [ ] 定时任务；
- [ ] 文件存储；
- [ ] 指标、链路追踪与其他可观测性能力。

扩展能力将根据实际需求推进，不作为基础模板启动的强制依赖。

## 项目状态

Phase 1 已完成并验证：

1. 最小配置可以启动；
2. 未安装数据库和 Redis 也可以运行；
3. 业务路由可以按模块接入 `/api/v1`；
4. 错误响应、请求追踪和结构化日志具有统一契约；
5. 格式化、静态检查、类型检查和自动化测试可重复执行。

下一阶段将进入 SQLAlchemy、Alembic 和 Redis 数据访问能力建设。在首个稳定版本发布前，项目结构和接口仍可能发生不兼容调整。

## 参与贡献

欢迎通过 Issue 提交建议、使用场景和问题反馈。提交 Pull Request 前，请确保 Ruff、mypy 和 pytest 检查全部通过。

提交功能建议时，建议同时说明：

- 需要解决的实际问题；
- 预期使用方式；
- 是否应作为基础能力或可选扩展；
- 可能引入的依赖和维护成本。

## 文档

架构决策、配置说明、模块开发指南和部署文档将随项目迭代逐步补充。

## License

许可证尚未确定。在正式选择并添加许可证文件前，请勿默认本项目代码可以用于商业或再分发用途。
