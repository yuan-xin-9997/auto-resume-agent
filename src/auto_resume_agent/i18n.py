LANGUAGES = {"en": "English", "zh-CN": "简体中文", "zh-TW": "繁體中文", "ja": "日本語", "ko": "한국어"}

EN = {
    "dashboard": "Dashboard", "settings": "Settings", "activity": "Activity", "subtitle": "Pick up where your agent left off.",
    "start": "Enable recovery", "pause": "Pause recovery", "refresh": "Refresh", "monitoring": "Recovery enabled",
    "paused": "Observe only", "quota": "Usage limits", "remaining": "remaining", "unknown": "Unknown",
    "reset": "Resets", "sessions": "Sessions", "watch": "Watch selected", "unwatch": "Unwatch selected",
    "more": "Load more", "thread": "Session / UUID", "project": "Workspace", "status": "Recovery status",
    "watching": "Watching", "unwatched": "Not watched", "waiting": "Waiting", "queued": "Queued · open original session",
    "sending": "Submitting", "uncertain": "Delivery uncertain · check original session", "progressed": "Session progressed",
    "superseded": "Newer turn exists", "cancelled": "Cancelled", "attention": "Needs attention", "language": "Language",
    "codex_path": "Codex executable (blank = auto-detect)", "save": "Save settings", "saved": "Settings saved",
    "privacy": "Local state only. Authentication stays in Codex.", "scope": "Codex · exact session UUID · no telemetry",
    "hint": "Select a session, click Watch selected, then enable recovery. Keep the original session open.",
    "empty": "No activity yet", "time": "Time", "event": "Event", "ready": "Connected to Codex",
    "error": "Connection needs attention", "detected": "Recoverable interruption detected", "retry_budget": "Hourly retry budget reached",
    "open_session": "Open the original session to consume its queued message", "delivery_unknown": "Check original session; no automatic resend",
    "quota_unknown": "Waiting for a known available quota", "waiting_reset": "Waiting for quota reset",
    "another_monitor": "Another monitor is checking sessions", "thread_read_failed": "One or more sessions could not be read",
    "codex_missing": "Codex not found. Install Codex CLI or set its executable in Settings.",
    "generic_error": "Codex connection failed. Check login, executable and network; recovery will wait.",
    "confirm_close": "Closing this window stops this monitor. CLI watch can run in the background.",
    "about": "Auto Resume Agent 0.1.0 · Codex adapter", "usage_age": "Last checked", "minutes": "min", "details": "Details",
    "help": "Quick start", "help_text": "1. Install Codex CLI and run codex login.\n2. Select the sessions to watch.\n3. Enable recovery and leave this app running.\n\nOnly known quota and transient errors are recovered.\nQueued means accepted by the CLI, not confirmed execution.\nPermissions and user cancellations always require you.\nUp to five submissions per session per hour.",
}

TRANSLATIONS = {
"zh-CN": ["仪表盘", "设置", "活动记录", "让 Agent 从中断处继续工作。", "开启自动恢复", "暂停自动恢复", "刷新", "自动恢复已开启", "仅观察", "额度使用情况", "剩余", "未知", "重置时间", "会话", "监控所选会话", "取消监控", "加载更多", "会话 / UUID", "工作目录", "恢复状态", "监控中", "未监控", "等待中", "已排队 · 请打开原会话", "正在提交", "投递不确定 · 请检查原会话", "会话已继续", "已有更新的轮次", "已取消", "需要处理", "界面语言", "Codex 可执行文件（留空自动检测）", "保存设置", "设置已保存", "数据仅存本地，认证由 Codex 管理。", "Codex · 精确会话 UUID · 无遥测", "选中会话并点击监控，再开启自动恢复。请保持原会话打开。", "暂无活动", "时间", "事件", "已连接 Codex", "连接需要处理", "检测到可恢复的中断", "已达到每小时重试上限", "请打开原会话以接收已排队的消息", "请检查原会话，不会自动重复发送", "等待确认额度可用", "等待额度重置", "另一个监控进程正在检查会话", "部分会话读取失败", "未找到 Codex，请安装 CLI 或在设置中指定路径。", "Codex 连接失败，请检查登录、路径和网络；恢复将等待。", "关闭窗口将停止此监控，可用 CLI watch 在后台运行。", "Auto Resume Agent 0.1.0 · Codex 适配器", "上次检查", "分钟", "详情", "快速开始", "1. 安装 Codex CLI 并运行 codex login。\n2. 选择需要监控的会话。\n3. 开启自动恢复并保持本软件运行。\n\n仅恢复明确的额度或临时故障。\n已排队表示 CLI 已接受，尚未确认执行。\n权限请求和用户取消始终需要人工处理。\n每个会话每小时最多提交五次。"],
"zh-TW": ["儀表板", "設定", "活動紀錄", "讓 Agent 從中斷處繼續工作。", "開啟自動恢復", "暫停自動恢復", "重新整理", "自動恢復已開啟", "僅觀察", "額度使用情況", "剩餘", "未知", "重設時間", "對話", "監控所選對話", "取消監控", "載入更多", "對話 / UUID", "工作目錄", "恢復狀態", "監控中", "未監控", "等待中", "已排入佇列 · 請開啟原對話", "正在提交", "投遞不確定 · 請檢查原對話", "對話已繼續", "已有更新的回合", "已取消", "需要處理", "介面語言", "Codex 執行檔（留空自動偵測）", "儲存設定", "設定已儲存", "資料僅存本機，驗證由 Codex 管理。", "Codex · 精確對話 UUID · 無遙測", "選取對話並點擊監控，再開啟自動恢復。請保持原對話開啟。", "尚無活動", "時間", "事件", "已連接 Codex", "連線需要處理", "偵測到可恢復的中斷", "已達每小時重試上限", "請開啟原對話以接收佇列訊息", "請檢查原對話，不會自動重複傳送", "等待確認額度可用", "等待額度重設", "另一個監控程序正在檢查對話", "部分對話讀取失敗", "找不到 Codex，請安裝 CLI 或在設定中指定路徑。", "Codex 連線失敗，請檢查登入、路徑與網路；恢復將等待。", "關閉視窗會停止此監控，可使用 CLI watch 在背景執行。", "Auto Resume Agent 0.1.0 · Codex 配接器", "上次檢查", "分鐘", "詳情", "快速開始", "1. 安裝 Codex CLI 並執行 codex login。\n2. 選取需要監控的對話。\n3. 開啟自動恢復並保持本軟體執行。\n\n僅恢復明確的額度或暫時故障。\n已排入佇列表示 CLI 已接受，尚未確認執行。\n權限要求與使用者取消始終需要人工處理。\n每個對話每小時最多提交五次。"],
"ja": ["ダッシュボード", "設定", "履歴", "エージェントの作業を、中断した場所から。", "自動再開を有効化", "自動再開を一時停止", "更新", "自動再開が有効", "監視のみ", "使用量の上限", "残り", "不明", "リセット", "セッション", "選択したセッションを監視", "監視を解除", "さらに読み込む", "セッション / UUID", "作業フォルダー", "再開の状態", "監視中", "未監視", "待機中", "キュー済み · 元のセッションを開く", "送信中", "配信不明 · 元のセッションを確認", "セッションが進行", "新しいターンあり", "キャンセル済み", "確認が必要", "表示言語", "Codex 実行ファイル（空欄で自動検出）", "設定を保存", "設定を保存しました", "データはローカルのみ。認証は Codex が管理します。", "Codex · 正確な UUID · テレメトリなし", "セッションを選択して監視を開始し、自動再開を有効にします。元のセッションを開いておいてください。", "履歴はありません", "時刻", "イベント", "Codex に接続済み", "接続の確認が必要", "再開可能な中断を検出", "1 時間の再試行上限に到達", "元のセッションを開いてキューのメッセージを受信してください", "元のセッションを確認してください。自動再送はしません", "利用可能な使用量を確認中", "上限のリセットを待機中", "別の監視プロセスが確認中", "一部のセッションを読み取れません", "Codex がありません。CLI をインストールするか設定で指定してください。", "Codex 接続に失敗。ログイン、パス、ネットワークを確認してください。", "ウィンドウを閉じると監視が停止します。CLI watch でバックグラウンド実行できます。", "Auto Resume Agent 0.1.0 · Codex アダプター", "最終確認", "分", "詳細", "クイックスタート", "1. Codex CLI をインストールして codex login を実行。\n2. 監視するセッションを選択。\n3. 自動再開を有効にして、このアプリを起動したままにします。\n\n明確な上限・一時エラーのみ再開します。\nキュー済みは実行確認ではありません。\n承認やキャンセルは手動で対応してください。\nセッションごとに 1 時間あたり最大 5 回送信。"],
"ko": ["대시보드", "설정", "활동 기록", "에이전트가 멈춘 곳에서 작업을 이어갑니다.", "자동 재개 켜기", "자동 재개 일시 중지", "새로 고침", "자동 재개 사용 중", "관찰만", "사용량 한도", "남음", "알 수 없음", "초기화", "세션", "선택한 세션 감시", "감시 해제", "더 불러오기", "세션 / UUID", "작업 폴더", "재개 상태", "감시 중", "감시 안 함", "대기 중", "대기열 등록 · 원래 세션 열기", "제출 중", "전달 불확실 · 원래 세션 확인", "세션 진행됨", "새 턴이 있음", "취소됨", "확인 필요", "표시 언어", "Codex 실행 파일 (비우면 자동 검색)", "설정 저장", "설정이 저장됨", "데이터는 로컬에만 저장. 인증은 Codex가 관리합니다.", "Codex · 정확한 세션 UUID · 원격 측정 없음", "세션을 선택해 감시한 뒤 자동 재개를 켜세요. 원래 세션을 열어 두세요.", "활동 기록 없음", "시간", "이벤트", "Codex 연결됨", "연결 확인 필요", "복구 가능한 중단 감지", "시간당 재시도 한도 도달", "대기열 메시지를 받으려면 원래 세션을 여세요", "원래 세션을 확인하세요. 자동 재전송하지 않습니다", "사용 가능한 한도 확인 대기", "한도 초기화 대기", "다른 감시 프로세스가 확인 중", "일부 세션을 읽을 수 없음", "Codex를 찾을 수 없습니다. CLI를 설치하거나 설정에서 경로를 지정하세요.", "Codex 연결 실패. 로그인, 경로, 네트워크를 확인하세요.", "창을 닫으면 감시가 중지됩니다. CLI watch로 백그라운드 실행할 수 있습니다.", "Auto Resume Agent 0.1.0 · Codex 어댑터", "마지막 확인", "분", "세부 정보", "빠른 시작", "1. Codex CLI 설치 후 codex login 실행.\n2. 감시할 세션을 선택하세요.\n3. 자동 재개를 켜고 앱을 실행 상태로 두세요.\n\n명확한 한도 및 일시적 오류만 복구합니다.\n대기열 등록은 실행 확인을 의미하지 않습니다.\n권한 요청과 사용자 취소는 직접 처리하세요.\n세션당 시간당 최대 5회 제출합니다."],
}

for _locale, _values in TRANSLATIONS.items():
    if len(_values) != len(EN):
        raise RuntimeError("Incomplete locale: " + _locale)
TRANSLATIONS = {key: dict(zip(EN, values)) for key, values in TRANSLATIONS.items()}

EXTRA = {
    "keeper_toggle": ("Start each Codex 5-hour window with a new ‘回复 OK’ session (default off)", "每个 Codex 5 小时窗口新建会话发送“回复 OK”（默认关闭）", "每個 Codex 5 小時視窗建立對話傳送「回复 OK」（預設關閉）", "Codex の各 5 時間枠で新規セッションに「回复 OK」を送信（既定 OFF）", "Codex의 각 5시간 창에서 새 세션에 ‘回复 OK’ 전송 (기본 꺼짐)"),
    "keeper_off": ("Off. No automatic window-start requests.", "已关闭，不会自动发送窗口启动请求。", "已關閉，不會自動傳送視窗啟動請求。", "OFF：枠開始の自動リクエストは送信しません。", "꺼짐: 창 시작 요청을 자동으로 보내지 않습니다."),
    "keeper_independent": ("Independent of recovery; uses one normal request after the reported reset, even with unused quota.", "独立于会话恢复；即使额度未用完，也在服务端重置时间后消耗一次正常请求。", "獨立於對話恢復；即使額度未用完，也在伺服器重設時間後使用一次正常請求。", "再開機能とは独立。残量があってもサーバーのリセット後に通常リクエストを 1 回使用します。", "복구와 별개로 동작합니다. 잔여 한도가 있어도 서버 초기화 후 일반 요청 1회를 사용합니다."),
    "keeper_next": ("Next boundary", "下一窗口", "下一視窗", "次の枠", "다음 창"),
    "keeper_last": ("Last attempt", "上次尝试", "上次嘗試", "前回", "최근 시도"),
    "keeper_completed": ("Replied OK", "已回复 OK", "已回覆 OK", "OK 応答済み", "OK 응답 완료"),
    "keeper_accepted": ("Accepted; completion unconfirmed", "已接受，未确认完成", "已接受，未確認完成", "受付済み・完了未確認", "접수됨 · 완료 미확인"),
    "keeper_uncertain": ("Delivery uncertain; no resend", "投递不确定，不重发", "投遞不確定，不重送", "送信不明・再送なし", "전달 불확실 · 재전송 안 함"),
    "keeper_sending": ("Starting helper session", "正在启动专用会话", "正在啟動專用對話", "専用セッションを開始中", "전용 세션 시작 중"),
    "keeper_failed": ("Helper turn failed; no resend", "专用轮次失败，不重发", "專用回合失敗，不重送", "専用ターン失敗・再送なし", "전용 턴 실패 · 재전송 안 함"),
    "keeper_cancelled": ("Cancelled before submission", "发送前已取消", "傳送前已取消", "送信前にキャンセル", "전송 전 취소됨"),
    "keeper_waiting": ("Waiting for the next boundary", "等待下一窗口", "等待下一視窗", "次の枠を待機", "다음 창 대기 중"),
    "keeper_waiting_update": ("Waiting for an updated server window", "等待服务端更新窗口时间", "等待伺服器更新視窗時間", "サーバーの枠更新を待機", "서버 창 시간 갱신 대기 중"),
    "keeper_waiting_quota": ("Waiting for confirmed available quota", "等待确认额度可用", "等待確認額度可用", "利用可能な残量の確認待ち", "사용 가능한 한도 확인 대기 중"),
    "keeper_no_window": ("Waiting for a reported 300-minute primary window", "等待服务端返回 300 分钟主窗口", "等待伺服器回傳 300 分鐘主視窗", "300 分の主枠情報を待機", "300분 기본 창 정보 대기 중"),
    "opencode_url": ("OpenCode server URL", "OpenCode 服务地址", "OpenCode 服務位址", "OpenCode サーバー URL", "OpenCode 서버 URL"),
    "opencode_directory": ("OpenCode workspace directory (on the server)", "OpenCode 工作目录（服务端路径）", "OpenCode 工作目錄（伺服器路徑）", "OpenCode 作業ディレクトリ（サーバー上）", "OpenCode 작업 폴더 (서버 경로)"),
    "quota_not_exposed": ("Provider quota is not exposed; bounded retries follow known transient errors.", "供应商未提供统一额度查询；仅对明确的临时故障有限重试。", "供應商未提供統一額度查詢；僅對明確的暫時故障有限重試。", "残量 API はありません。明確な一時エラーのみ回数制限付きで再試行します。", "통합 잔여 한도 API가 없습니다. 명확한 일시적 오류만 제한적으로 재시도합니다."),
    "accepted": ("Accepted · execution not confirmed", "已接受 · 尚未确认执行", "已接受 · 尚未確認執行", "受付済み · 実行未確認", "접수됨 · 실행 미확인"),
    "opencode_invalid_url": ("Enter an HTTP(S) server origin without credentials, path or query.", "请输入不含凭据、路径和查询参数的 HTTP(S) 服务地址。", "請輸入不含憑證、路徑及查詢參數的 HTTP(S) 服務位址。", "認証情報・パス・クエリを含まない HTTP(S) URL を入力してください。", "인증 정보, 경로, 쿼리가 없는 HTTP(S) URL을 입력하세요."),
    "opencode_remote_requires_https": ("Remote OpenCode servers require HTTPS; HTTP is allowed on loopback only.", "远程 OpenCode 服务需使用 HTTPS；HTTP 仅限本机回环地址。", "遠端 OpenCode 服務需使用 HTTPS；HTTP 僅限本機回環位址。", "リモートは HTTPS が必要です。HTTP はループバックのみ使用できます。", "원격 서버에는 HTTPS가 필요합니다. HTTP는 루프백에서만 허용됩니다."),
    "opencode_help": ("Start OpenCode on a known port (opencode serve --hostname 127.0.0.1 --port 4096), or use a running TUI's server port. Set its URL and workspace directory in Settings, select OpenCode, watch sessions and enable recovery.\n\nRemaining provider quota is unknown. Only retryable API errors (429, 408/425, 5xx or transport failures) are retried. Retry-After is respected. Busy/retrying sessions, permissions and questions require waiting or user action. Accepted is not execution confirmation.",
        "用固定端口启动 OpenCode（opencode serve --hostname 127.0.0.1 --port 4096），或使用已运行 TUI 的服务端口。在设置中填写地址和工作目录，切换到 OpenCode，选择会话并开启恢复。\n\n供应商剩余额度未知。仅重试明确可重试的 API 错误（429、408/425、5xx 或连接故障），并遵守 Retry-After。运行中、自身重试中、权限及提问等待状态不会被打断。已接受不代表已执行。",
        "使用固定連接埠啟動 OpenCode（opencode serve --hostname 127.0.0.1 --port 4096），或使用已執行 TUI 的伺服器連接埠。在設定中填入位址與工作目錄，切換至 OpenCode，選取對話並啟用恢復。\n\n供應商剩餘額度未知。僅重試明確可重試的 API 錯誤（429、408/425、5xx 或連線故障），並遵守 Retry-After。執行中、自身重試中、權限與提問等待狀態不會被打斷。已接受不代表已執行。",
        "OpenCode を固定ポートで起動（opencode serve --hostname 127.0.0.1 --port 4096）、または既存 TUI のポートを使用します。設定で URL と作業ディレクトリを指定し、OpenCode を選択して監視と再開を有効にします。\n\n残量は不明です。再試行可能な 429、408/425、5xx、接続エラーのみを対象とし、Retry-After を尊重します。実行中・再試行中・権限や質問の待機中は介入しません。受付は実行確認ではありません。",
        "OpenCode를 고정 포트로 실행하거나(opencode serve --hostname 127.0.0.1 --port 4096) 기존 TUI의 서버 포트를 사용하세요. 설정에서 URL과 작업 폴더를 지정하고 OpenCode를 선택해 감시와 복구를 켜세요.\n\n잔여 한도는 알 수 없습니다. 재시도 가능한 429, 408/425, 5xx 및 연결 오류만 처리하며 Retry-After를 따릅니다. 실행 중, 자체 재시도 중, 권한 또는 질문 대기 상태에는 개입하지 않습니다. 접수는 실행 확인이 아닙니다."),
}
for _key, _texts in EXTRA.items():
    EN[_key] = _texts[0]
    for _language, _text in zip(list(LANGUAGES)[1:], _texts[1:]):
        TRANSLATIONS[_language][_key] = _text


def tr(key, language="en"):
    return TRANSLATIONS.get(language, EN).get(key, EN.get(key, key))
