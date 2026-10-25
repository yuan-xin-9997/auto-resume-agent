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


def tr(key, language="en"):
    return TRANSLATIONS.get(language, EN).get(key, EN.get(key, key))
