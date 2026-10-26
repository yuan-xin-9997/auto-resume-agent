<p align="center"><img src="src/auto_resume_agent/assets/icon.png" width="112" alt="Auto Resume Agent 图标"></p>

# Auto Resume Agent

跨平台 AI Agent 额度检测和原会话恢复工具。

[English](README.md) · [下载 Release](https://github.com/yuan-xin-9997/auto-resume-agent/releases) · [测试与兼容性](docs/TESTING.md)

**Windows、Ubuntu、macOS · 原生 GUI 和 CLI · 五种界面语言 · 本地存储 · 无遥测**

Agent 任务中途额度耗尽后，本软件检测失败轮次，查询 Codex 返回的额度窗口，在额度可用后向**同一会话 UUID**提交继续指令。不使用 `--last`，不模拟键盘向窗口输入。

首版实际接入 **Codex CLI 和本地 Codex 桌面会话**。Claude Code、Gemini CLI、纯云端会话等尚未实现适配，软件名称不代表已经支持所有 Agent。

![仪表盘示例](docs/screenshots/dashboard.zh-CN.png)

*示例会话和额度，不包含个人对话数据。*

| 功能 | 行为 |
| --- | --- |
| 额度检测 | 主、副额度窗口，剩余百分比，本地重置时间及检查时间 |
| 自动恢复 | 明确的额度、限流、连接、流中断和临时服务端错误 |
| 调度 | 通常每 5 秒检查会话，每 30 秒及恢复截止时间重新查询额度 |
| 休眠唤醒 | 下一次调度时重新计算真实时间，不因休眠继续等待旧倒计时 |
| 防重复 | 发送前保存领取状态，崩溃或超时后不盲目重发 |
| 多语言 | 英语、简体中文、繁体中文、日语、韩语，即时切换并保存 |

**重要限制：**“已排队”只表示 Codex CLI 接受了继续消息，不能证明任务已经执行。请保持原会话在 Codex 中打开；未加载的会话可能一直排队，打开后才能继续。“会话已继续”只证明出现了新轮次，不证明是本软件触发。本软件不会在后台另开不受限制的替代 Agent。

## 安装

从 [Releases](https://github.com/yuan-xin-9997/auto-resume-agent/releases) 下载对应系统和处理器的压缩包。原生包自带 Python，但仍需**单独安装 Codex CLI 并登录**。实际测试的 Codex CLI 版本为 **0.163.0**；其他版本请先运行 `doctor`，旧版本可能不支持相关实验接口。

| 系统 | 包名 | 启动方式 |
| --- | --- | --- |
| Windows 10 1809+ / 11 x64 | `*-windows-x64.zip` | 完整解压，运行 `Launch.cmd` 或 `gui/AutoResumeAgent.exe` |
| Ubuntu 24.04 / 26.04 x64 | `*-linux-x64.tar.gz` | 解压，运行 `sh install.sh`，从应用菜单打开 |
| macOS 27 Apple Silicon | `*-macos-arm64.tar.gz` | 解压，运行 `sh install.sh`，打开 `~/Applications/AutoResumeAgent.app` |
| macOS 27 Intel | `*-macos-x64.tar.gz` | 同上，选择 Intel 包 |

以上是目标平台；请以[实际测试矩阵](docs/TESTING.md)为准。程序未进行商业代码签名和苹果公证，系统可能要求按正常流程批准打开。安装脚本不会修改系统安全设置。Mac CLI 放在 `~/.local/bin`，必要时将该目录加入 PATH。

使用压缩包旁的 `.sha256` 文件校验下载：Windows 用 `Get-FileHash 文件名 -Algorithm SHA256`，Ubuntu 用 `sha256sum 文件名`，Mac 用 `shasum -a 256 文件名`。

### 从源码运行

需要 Python 3.11 或更新版本：

```sh
python -m venv .venv
# 按当前 Shell 的方式激活 .venv
python -m pip install '.[gui]'
auto-resume-agent gui
```

无桌面服务器可用 `python -m pip install .`，只安装 CLI，不需要 Qt。Ubuntu GUI 依赖：

```sh
sudo apt-get install libegl1 libgl1 libxkbcommon0 libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1 libxcb-shape0 libxcb-xinerama0
```

## 开始使用

1. 安装 [Codex CLI](https://github.com/openai/codex)，运行 `codex login`。
2. 打开本软件，在设置中选择语言；自动检测失败时填写 Codex 可执行文件路径。
3. 选中会话，点击“监控所选会话”；旧会话可通过“加载更多”查找。
4. 点击“开启自动恢复”，保持本软件和原 Codex 会话打开。
5. 在仪表盘和活动记录中查看等待、排队、投递不确定及新轮次状态。

新安装默认为“仅观察”。添加监控后，检测添加时间前一分钟内及未来的失败；不会自动恢复全部历史任务。关闭 GUI 会停止该窗口的监控，不会偷偷安装开机服务。开启/暂停设置会保留到下次启动。

### 命令行

Windows 解压包把命令替换为 `cli\auto-resume-agent.exe`，Linux 安装前使用 `./cli/auto-resume-agent`。

```sh
auto-resume-agent doctor              # 只读检查连接、额度及会话接口
auto-resume-agent usage               # JSON 额度
auto-resume-agent sessions            # 分页列出本地会话，JSON Lines
auto-resume-agent add SESSION_UUID    # 监控指定 UUID
auto-resume-agent enable              # 允许自动恢复
auto-resume-agent watch               # 前台监控，Ctrl+C 退出
auto-resume-agent status              # 已保存额度、会话及恢复记录
auto-resume-agent pause               # 暂停自动发送
auto-resume-agent remove SESSION_UUID # 取消监控及等待中的恢复
auto-resume-agent cancel RECOVERY_ID  # 取消某条等待中的恢复记录
auto-resume-agent check               # 检查一轮；已开启恢复时可能发送
```

全局选项放在子命令前，如 `auto-resume-agent --codex /path/to/codex --home /path/to/state doctor`。`--codex` 会保存；`--home` 或环境变量 `ARA_HOME` 指定本软件数据目录。启动前设置 `CODEX_HOME` 可选择 Codex 配置，监控 UUID 绑定该目录。支持原生二进制和标准 npm 启动器，后者还需 Node.js；不执行任意 Shell 包装脚本。

Linux/Mac 可通过自己的服务管理器运行 `watch`。不要让另一款自动恢复工具同时管理相同会话：本软件只对共用同一状态目录的实例加锁，无法协调其他产品或独立状态目录。

## 恢复规则与边界

- 仅处理明确选中的本地、未归档、支持来源的会话；不恢复子 Agent。
- 需要明确的结构化错误，以及新鲜的、确认可用的额度快照。未知额度继续等待。
- 同时考虑主、副额度窗口；时间戳已过但仍报告耗尽的快照不能授权发送。
- 临时故障采用有上限的退避，每个会话每小时最多提交五次，各错误类型共享上限。
- 有更新轮次时取消旧等待；不自动恢复权限、认证、策略、上下文超长、无效请求和用户取消。
- `codex queue` 前先持久化发送意图；超时、崩溃或模糊结果转为“投递不确定”，须检查原会话，不自动重发。
- 最新轮次读取与排队命令之间仍有很小的竞争窗口，Codex CLI 没有“仅当轮次未变才排队”的原子接口；其他客户端可能在此期间操作。因此不能承诺跨两个程序严格恰好执行一次。

检查间隔是调度目标，不是实时保证。休眠、网络、Codex 响应速度和监控会话数量会增加延迟。本软件不会唤醒休眠的电脑，需要在会话所在主机运行。

## 隐私和数据

无遥测、分析和自动更新网络客户端，认证和 OpenAI 请求由你安装的 Codex 处理。本软件 app-server 客户端只调用初始化、额度和会话元数据接口，不能批准工具或启动轮次；恢复通过独立的官方 `codex queue` 命令。

本地 SQLite 保存设置、监控 UUID、数值额度快照、分类恢复记录和有数量上限的事件代码，不保存提示词、对话全文、原始错误、Token 或 API Key。会话名称和工作目录只在 GUI 内存中展示，也会由 `sessions` 命令打印；重定向命令输出时请自行管理这些数据。

仅在本地排障时，可设置 `ARA_DEBUG_LOG` 为文件路径，主动保存 Codex app-server 的 stderr。该可选原始诊断文件可能包含私人路径和错误详情，分享前应检查；默认关闭，与正常状态数据库分开。

| 系统 | 默认状态目录 |
| --- | --- |
| Windows | `%LOCALAPPDATA%\AutoResumeAgent` |
| Linux | `${XDG_STATE_HOME:-~/.local/state}/auto-resume-agent` |
| macOS | `~/Library/Application Support/AutoResumeAgent` |

卸载时删除安装文件和启动入口。仅在确需丢弃设置及恢复历史时额外删除状态目录；升级时保留，避免已领取的中断被再次提交。

## 开发与发布

```sh
python -m pip install -e '.[gui,build,test]'
python -m pytest -q
python scripts/make_icons.py
python scripts/build.py
```

在目标系统及架构原生构建。GitHub Actions 测试并构建 Windows x64、Linux x64、Mac arm64 和 x64。所有构建通过后，版本标签自动发布包含校验和的 **prerelease**。详见[发布说明](docs/RELEASE_NOTES.md)与[测试证据](docs/TESTING.md)。

## 致谢与许可证

参考 [songyb111-gachon/codex-auto-resume-windows](https://github.com/songyb111-gachon/codex-auto-resume-windows) 的精确会话识别、谨慎投递和安装优先的文档组织方式。本项目是独立跨平台实现，不隶属于 OpenAI 或参考项目。

接口依据：[官方 Codex app-server 文档](https://learn.chatgpt.com/docs/app-server)。项目代码采用 MIT 许可证，打包的第三方库保留各自许可证，见[第三方声明](THIRD_PARTY_NOTICES.md)。
