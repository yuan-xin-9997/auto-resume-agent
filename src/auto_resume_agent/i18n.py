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
    "codex_interval": ("Codex check interval (seconds, saved immediately)", "Codex 检查间隔（秒，立即保存）", "Codex 檢查間隔（秒，立即儲存）", "Codex 確認間隔（秒、即時保存）", "Codex 확인 간격 (초, 즉시 저장)"),
    "opencode_interval": ("OpenCode check interval (seconds, saved immediately)", "OpenCode 检查间隔（秒，立即保存）", "OpenCode 檢查間隔（秒，立即儲存）", "OpenCode 確認間隔（秒、即時保存）", "OpenCode 확인 간격 (초, 즉시 저장)"),
    "auto_running": ("Running session added to monitoring", "运行中会话已加入监控", "執行中對話已加入監控", "実行中のセッションを監視に追加", "실행 중인 세션을 감시에 추가함"),
    "keeper_recovery_first": ("Interrupted sessions take priority; no helper request", "优先恢复额度中断会话，不新建辅助会话", "優先恢復額度中斷對話，不建立輔助對話", "中断セッションの再開を優先", "중단된 세션 복구 우선"),
    "keeper_not_exhausted": ("Quota was not exhausted; no helper needed", "额度未耗尽，无需新建辅助会话", "額度未耗盡，無需建立輔助對話", "残量があるため補助セッションは不要", "한도가 남아 있어 보조 세션 불필요"),

    "search_sessions": ("Search name, UUID or workspace", "搜索名称、UUID 或工作目录", "搜尋名稱、UUID 或工作目錄", "名前・UUID・作業フォルダーで検索", "이름, UUID 또는 작업 폴더 검색"),
    "auto_watch_hint": ('Running and quota-interrupted Codex sessions are watched automatically. Enable recovery and keep original sessions open.', '运行中或因额度耗尽中断的 Codex 会话会自动加入监控。请开启自动恢复并保持原会话打开。', '執行中或額度耗盡中斷的 Codex 對話會自動監控。請啟用恢復並保持原對話開啟。', '実行中・残量不足の Codex セッションを自動監視します。再開を有効にし元のセッションを開いてください。', '실행 중 또는 한도 소진으로 중단된 Codex 세션 자동 감시. 복구를 켜고 원래 세션을 열어 두세요.'),
    "auto_watch_toggle": ('Automatically watch running / quota-exhausted Codex sessions (default on)', '自动监控运行中或因额度耗尽中断的 Codex 会话（默认开启）', '自動監控執行中或額度耗盡中斷的 Codex 對話（預設開啟）', '実行中・残量不足の Codex セッションを自動監視（既定 ON）', '실행 중 / 한도 소진 Codex 세션 자동 감시 (기본 켜짐)'),
    "auto_watched": ("Automatically watched after quota exhaustion", "额度耗尽，已自动加入监控", "額度耗盡，已自動加入監控", "残量不足のため自動監視に追加", "한도 소진으로 자동 감시에 추가됨"),
    "auto_unwatched": ("Stopped watching a finished session", "会话已完成，已停止监控", "對話已完成，已停止監控", "完了したセッションの監視を停止しました", "완료된 세션 감시를 중지했습니다"),
    "codex_proxy": ("Codex HTTP(S) proxy (optional; e.g. http://127.0.0.1:7890)", "Codex HTTP(S) 代理（可选，如 http://127.0.0.1:7890）", "Codex HTTP(S) 代理（選填，如 http://127.0.0.1:7890）", "Codex HTTP(S) プロキシ（任意、例 http://127.0.0.1:7890）", "Codex HTTP(S) 프록시 (선택, 예: http://127.0.0.1:7890)"),
    "codex_invalid_proxy": ("Enter an HTTP(S) proxy origin with a port, without credentials, path or query.", "请输入带端口的 HTTP(S) 代理地址，不含凭据、路径和查询参数。", "請輸入含連接埠的 HTTP(S) 代理位址，不含憑證、路徑及查詢參數。", "ポート付きの HTTP(S) URL を入力してください。認証情報・パス・クエリは含めないでください。", "포트가 있는 HTTP(S) 주소를 입력하세요. 인증 정보, 경로, 쿼리는 제외하세요."),
    "five_hours": ("5 hours", "5 小时", "5 小時", "5時間", "5시간"),
    "one_week": ("1 week", "一周", "一週", "1週間", "1주"),
    "one_month": ("1 month", "一个月", "一個月", "1か月", "1개월"),
    "select": ("Select", "选择", "選取", "選択", "선택"),
    "select_all": ("Select all", "全选", "全選", "すべて選択", "모두 선택"),
    "hint": ("Tick sessions, click Watch selected, then enable recovery. Keep the original session open.", "勾选会话并点击监控，再开启自动恢复。请保持原会话打开。", "勾選對話並點擊監控，再開啟自動恢復。請保持原對話開啟。", "セッションにチェックして監視し、自動再開を有効にします。元のセッションを開いておいてください。", "세션을 체크해 감시한 뒤 자동 재개를 켜세요. 원래 세션을 열어 두세요."),
    "opencode_hint": ("Tick sessions, click Watch selected, then enable recovery. Keep the OpenCode server running.", "勾选会话并点击监控，再开启自动恢复。请保持 OpenCode 服务运行。", "勾選對話並點擊監控，再開啟自動恢復。請保持 OpenCode 服務執行。", "セッションにチェックして監視し、自動再開を有効にします。OpenCode サーバーを起動したままにしてください。", "세션을 체크해 감시한 뒤 자동 재개를 켜세요. OpenCode 서버를 실행 상태로 두세요."),
    "keeper_toggle": ('Start next exhausted Codex window when no recovery is pending (default off)', 'Codex 五小时额度耗尽且无待恢复任务时，启动下一窗口（默认关闭）', 'Codex 五小時額度耗盡且無待恢復任務時啟動下一視窗（預設關閉）', 'Codex 残量不足で再開待ちがない場合に次枠を開始（既定 OFF）', 'Codex 한도 소진 후 복구 대기가 없으면 다음 창 시작 (기본 꺼짐)'),
    "keeper_off": ("Off. No automatic window-start requests.", "已关闭，不会自动发送窗口启动请求。", "已關閉，不會自動傳送視窗啟動請求。", "OFF：枠開始の自動リクエストは送信しません。", "꺼짐: 창 시작 요청을 자동으로 보내지 않습니다."),
    "keeper_independent": ('Only after five-hour quota exhaustion, with no pending quota recovery. Uses one normal request; never forces a server reset.', '仅五小时额度耗尽且无额度中断任务待恢复时，使用一次正常请求启动新窗口；不能强制服务端重置。', '僅五小時額度耗盡且無中斷任務待恢復時，使用一次正常請求啟動新視窗；不能強制重設。', '5 時間枠が枯渇し再開待ちがない場合のみ通常リクエストを送信。強制リセットはできません。', '5시간 한도 소진 및 복구 대기 없음일 때만 일반 요청 사용. 서버 초기화 강제 불가.'),
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
    "connecting": ("Connecting…", "连接中…", "連線中…", "接続中…", "연결 중…"),
    "quota_pending": ("Pending", "待获取", "待取得", "取得待ち", "대기 중"),
    "refreshing": ("Refreshing…", "正在刷新…", "正在重新整理…", "更新中…", "새로 고치는 중…"),
    "refreshed": ("Refreshed", "刷新完成", "重新整理完成", "更新しました", "새로 고침 완료"),
    "refresh_slow": ("Refresh is slow; the background check is still running.", "刷新较慢，后台仍在检查，请稍候。", "重新整理較慢，背景仍在檢查，請稍候。", "更新に時間がかかっています。バックグラウンドで確認中です。", "새로 고침이 지연되고 있습니다. 백그라운드 확인이 계속됩니다."),
    "refresh_timeout": ("Refresh is still waiting for the background monitor. Try again later.", "刷新仍在等待后台监控完成，请稍后再试。", "重新整理仍在等待背景監控完成，請稍後再試。", "更新はバックグラウンド監視の完了待ちです。後でもう一度お試しください。", "새로 고침이 백그라운드 감시 완료를 기다리고 있습니다. 나중에 다시 시도하세요."),
    "refresh_unavailable": ("Background monitor is not running; refresh is unavailable.", "后台监控未运行，暂时无法刷新。", "背景監控未執行，暫時無法重新整理。", "バックグラウンド監視が動作していないため更新できません。", "백그라운드 감시가 실행 중이 아니어서 새로 고칠 수 없습니다."),
    "accepted": ("Accepted · execution not confirmed", "已接受 · 尚未确认执行", "已接受 · 尚未確認執行", "受付済み · 実行未確認", "접수됨 · 실행 미확인"),
    "opencode_invalid_url": ("Enter an HTTP(S) server origin without credentials, path or query.", "请输入不含凭据、路径和查询参数的 HTTP(S) 服务地址。", "請輸入不含憑證、路徑及查詢參數的 HTTP(S) 服務位址。", "認証情報・パス・クエリを含まない HTTP(S) URL を入力してください。", "인증 정보, 경로, 쿼리가 없는 HTTP(S) URL을 입력하세요."),
    "opencode_remote_requires_https": ("Remote OpenCode servers require HTTPS; HTTP is allowed on loopback only.", "远程 OpenCode 服务需使用 HTTPS；HTTP 仅限本机回环地址。", "遠端 OpenCode 服務需使用 HTTPS；HTTP 僅限本機回環位址。", "リモートは HTTPS が必要です。HTTP はループバックのみ使用できます。", "원격 서버에는 HTTPS가 필요합니다. HTTP는 루프백에서만 허용됩니다."),
    "opencode_connection_failed": ("Cannot reach the OpenCode server at the configured URL. Start OpenCode or check the address and port; recovery will wait.", "无法连接配置的 OpenCode 服务。请启动 OpenCode 或检查地址和端口；恢复将等待。", "無法連線設定的 OpenCode 服務。請啟動 OpenCode 或檢查位址與連接埠；恢復將等待。", "設定された OpenCode サーバーに接続できません。OpenCode を起動するか URL とポートを確認してください。再開は待機します。", "설정한 OpenCode 서버에 연결할 수 없습니다. OpenCode를 실행하거나 주소와 포트를 확인하세요. 복구는 대기합니다."),
    "opencode_auth_required": ("OpenCode server requires Basic authentication. Set OPENCODE_SERVER_PASSWORD to the server password; recovery will wait.", "OpenCode 服务需要 Basic 认证。请将 OPENCODE_SERVER_PASSWORD 设为服务密码；恢复将等待。", "OpenCode 服務需要 Basic 認證。請將 OPENCODE_SERVER_PASSWORD 設為服務密碼；恢復將等待。", "OpenCode サーバーは Basic 認証が必要です。OPENCODE_SERVER_PASSWORD にサーバーのパスワードを設定してください。再開は待機します。", "OpenCode 서버에 Basic 인증이 필요합니다. OPENCODE_SERVER_PASSWORD에 서버 비밀번호를 설정하세요. 복구는 대기합니다."),
    "compatibility_error": ("Agent interface is incompatible or changed. Automatic sending is blocked; run doctor and update the adapter or agent.", "Agent 接口不兼容或已变化，已停止自动发送；请运行 doctor 并更新适配器或 Agent。", "Agent 介面不相容或已變更，已停止自動傳送；請執行 doctor 並更新轉接器或 Agent。", "Agent インターフェースが非互換または変更されました。自動送信を停止しました。doctor を実行し、アダプターまたは Agent を更新してください。", "Agent 인터페이스가 호환되지 않거나 변경되었습니다. 자동 전송을 중단했습니다. doctor를 실행하고 어댑터 또는 Agent를 업데이트하세요."),
    "opencode_help": ("Start OpenCode on a known port (opencode serve --hostname 127.0.0.1 --port 4096), or use a running TUI's server port. For the 2.x desktop service, enter its URL (usually http://127.0.0.1:28894) and set OPENCODE_SERVER_PASSWORD to the password in ~/.config/opencode/service.json. Set the workspace directory, select OpenCode, watch sessions and enable recovery.\n\nOpenCode 1.19.x does not expose provider quota; 2.x exposes OpenCode Go/Go Plus rolling, weekly and monthly allowance and reset times. Only retryable API errors (429, 408/425, 5xx or transport failures) are retried, plus Go allowance errors scheduled to the reported reset. Retry-After is respected. Busy/retrying sessions, permissions and forms require waiting or user action. Accepted is not execution confirmation.",
        "用固定端口启动 OpenCode（opencode serve --hostname 127.0.0.1 --port 4096），或使用已运行 TUI 的服务端口。使用 2.x 桌面服务时填写其地址（通常为 http://127.0.0.1:28894），并将 OPENCODE_SERVER_PASSWORD 设为 ~/.config/opencode/service.json 中的密码。填写工作目录，切换到 OpenCode，选择会话并开启恢复。\n\nOpenCode 1.19.x 不暴露供应商额度；2.x 会返回 OpenCode Go/Go Plus 的滚动、每周和每月额度及重置时间。仅重试明确可重试的 API 错误（429、408/425、5xx 或连接故障），Go 额度错误会等到报告的重置时间。遵守 Retry-After。运行中、自身重试中、权限及表单等待状态不会被打断。已接受不代表已执行。",
        "使用固定連接埠啟動 OpenCode（opencode serve --hostname 127.0.0.1 --port 4096），或使用已執行 TUI 的伺服器連接埠。使用 2.x 桌面服務時填入其位址（通常為 http://127.0.0.1:28894），並將 OPENCODE_SERVER_PASSWORD 設為 ~/.config/opencode/service.json 中的密碼。填寫工作目錄，切換至 OpenCode，選取對話並啟用恢復。\n\nOpenCode 1.19.x 不暴露供應商額度；2.x 會回傳 OpenCode Go/Go Plus 的滾動、每週與每月額度及重設時間。僅重試明確可重試的 API 錯誤（429、408/425、5xx 或連線故障），Go 額度錯誤會等到回報的重設時間。遵守 Retry-After。執行中、自身重試中、權限與表單等待狀態不會被打斷。已接受不代表已執行。",
        "OpenCode を固定ポートで起動（opencode serve --hostname 127.0.0.1 --port 4096）、または既存 TUI のポートを使用します。2.x デスクトップサービスでは URL（通常 http://127.0.0.1:28894）を入力し、OPENCODE_SERVER_PASSWORD に ~/.config/opencode/service.json のパスワードを設定します。作業ディレクトリを指定し、OpenCode を選択して監視と再開を有効にします。\n\nOpenCode 1.19.x は残量を公開しません。2.x は OpenCode Go/Go Plus のローリング・週次・月次残量とリセット時刻を返します。再試行可能な 429、408/425、5xx、接続エラーのみを対象とし、Go の残量エラーは報告されたリセット時刻まで待機します。Retry-After を尊重します。実行中・再試行中・権限やフォームの待機中は介入しません。受付は実行確認ではありません。",
        "OpenCode를 고정 포트로 실행하거나(opencode serve --hostname 127.0.0.1 --port 4096) 기존 TUI의 서버 포트를 사용하세요. 2.x 데스크톱 서비스는 URL(보통 http://127.0.0.1:28894)을 입력하고 OPENCODE_SERVER_PASSWORD에 ~/.config/opencode/service.json의 비밀번호를 설정하세요. 작업 폴더를 지정하고 OpenCode를 선택해 감시와 복구를 켜세요.\n\nOpenCode 1.19.x는 잔여 한도를 공개하지 않습니다. 2.x는 OpenCode Go/Go Plus의 롤링·주간·월간 한도와 초기화 시간을 반환합니다. 재시도 가능한 429, 408/425, 5xx 및 연결 오류만 처리하며 Go 한도 오류는 보고된 초기화 시간까지 대기합니다. Retry-After를 따릅니다. 실행 중, 자체 재시도 중, 권한 또는 양식 대기 상태에는 개입하지 않습니다. 접수는 실행 확인이 아닙니다."),
}
EXTRA.update({
    "all": ("All", "全部", "全部", "すべて", "전체"),
    "filter_watching": ("Watching", "监控中", "監控中", "監視中", "감시 중"),
    "filter_pending": ("Pending", "待恢复", "待恢復", "再開待ち", "재개 대기"),
    "filter_attention": ("Needs attention", "需要处理", "需要處理", "要対応", "확인 필요"),
    "healthy": ("Healthy", "额度充足", "額度充足", "残量あり", "한도 충분"),
    "low": ("Low", "额度偏低", "額度偏低", "残量少", "한도 부족"),
    "exhausted": ("Exhausted", "额度耗尽", "額度耗盡", "残量なし", "한도 소진"),
    "used": ("used", "已用", "已用", "使用済み", "사용됨"),
    "last_checked": ("Last checked", "上次检查", "上次檢查", "最終確認", "마지막 확인"),
    "theme": ("Appearance", "外观", "外觀", "外観", "화면"),
    "theme_system": ("System", "跟随系统", "跟隨系統", "システム", "시스템"),
    "theme_light": ("Light", "浅色", "淺色", "ライト", "라이트"),
    "theme_dark": ("Dark", "深色", "深色", "ダーク", "다크"),
    "general": ("General", "常规", "一般", "一般", "일반"),
    "advanced": ("Advanced", "高级", "進階", "詳細設定", "고급"),
    "connection": ("Connection", "连接", "連線", "接続", "연결"),
    "recovery": ("Recovery", "恢复", "恢復", "再開", "복구"),
    "dirty": ("Unsaved changes", "有未保存的更改", "有未儲存的變更", "未保存の変更", "저장되지 않은 변경"),
    "settings_saved_toast": ("Settings saved", "设置已保存", "設定已儲存", "設定を保存しました", "설정이 저장됨"),
    "no_sessions_title": ("No sessions to show", "没有可显示的会话", "沒有可顯示的對話", "表示できるセッションがありません", "표시할 세션이 없습니다"),
    "no_sessions_body": ("Change the search or filter, or refresh the session list.", "调整搜索或筛选条件，或刷新会话列表。", "調整搜尋或篩選條件，或重新整理對話清單。", "検索またはフィルターを変更するか、セッション一覧を更新してください。", "검색 또는 필터를 변경하거나 세션 목록을 새로 고치세요."),
    "no_watched_title": ("No watched sessions", "暂无监控会话", "暫無監控對話", "監視中のセッションはありません", "감시 중인 세션이 없습니다"),
    "no_watched_body": ("Switch to All to choose a session. Running sessions are adopted automatically.", "切换到“全部”选择会话；运行中的会话会自动加入。", "切換至「全部」選擇對話；執行中的對話會自動加入。", "「すべて」に切り替えてセッションを選択してください。実行中のセッションは自動的に監視されます。", "전체로 전환해 세션을 선택하세요. 실행 중인 세션은 자동으로 감시됩니다."),
    "no_activity_title": ("No activity yet", "还没有活动记录", "尚無活動紀錄", "履歴はまだありません", "아직 활동 기록이 없습니다"),
    "no_activity_body": ("Recovery events will appear here after you watch a session.", "监控会话后，恢复过程会显示在这里。", "監控對話後，恢復過程會顯示在這裡。", "セッションを監視すると、再開の履歴がここに表示されます。", "세션을 감시하면 복구 과정이 여기에 표시됩니다."),
    "watched_toast": ("Added to monitoring", "已加入监控", "已加入監控", "監視に追加しました", "감시에 추가됨"),
    "unwatched_toast": ("Removed from monitoring", "已取消监控", "已取消監控", "監視から外しました", "감시에서 제거됨"),
    "auto_watch_title": ("Automatically watch interrupted sessions", "自动监控中断会话", "自動監控中斷對話", "中断したセッションを自動監視", "중단된 세션 자동 감시"),
    "keeper_title": ("Start the next window when quota is exhausted", "额度用尽时启动新窗口", "額度用盡時啟動新視窗", "上限到達時に次の枠を開始", "한도 소진 시 다음 창 시작"),
    "codex_path_hint": ("Leave blank to detect automatically.", "留空则自动检测。", "留空則自動偵測。", "空欄の場合は自動検出します。", "비우면 자동으로 감지합니다."),
    "codex_proxy_hint": ("Optional HTTP(S) proxy for the Codex process.", "Codex 进程可选的 HTTP(S) 代理。", "Codex 程序可選的 HTTP(S) 代理。", "Codex プロセス用の任意の HTTP(S) プロキシ。", "Codex 프로세스용 선택 HTTP(S) 프록시."),
    "opencode_url_hint": ("The server origin, for example http://127.0.0.1:4096 (1.19.x) or http://127.0.0.1:28894 (2.x desktop).", "服务地址，例如 http://127.0.0.1:4096（1.19.x）或 http://127.0.0.1:28894（2.x 桌面版）。", "服務位址，例如 http://127.0.0.1:4096（1.19.x）或 http://127.0.0.1:28894（2.x 桌面版）。", "サーバーの URL（例 http://127.0.0.1:4096（1.19.x）、http://127.0.0.1:28894（2.x デスクトップ））。", "서버 주소(예: http://127.0.0.1:4096(1.19.x), http://127.0.0.1:28894(2.x 데스크톱))."),
    "opencode_directory_hint": ("Absolute workspace path on the server.", "服务端的绝对工作目录。", "伺服器上的絕對工作目錄。", "サーバー上の絶対作業パス。", "서버의 절대 작업 폴더."),
    "save_hint": ("Connection changes are applied when you save.", "连接信息在保存后生效。", "連線資訊儲存後生效。", "接続設定は保存後に反映されます。", "연결 설정은 저장 후 적용됩니다."),
    "resets_in": ("Resets in {time}", "重置 · {time}后", "重設 · {time}後", "{time}後にリセット", "{time} 후 초기화"),
    "resetting_soon": ("Resetting soon", "即将重置", "即將重設", "まもなくリセット", "곧 초기화"),
    "hours_short": ("h", "小时", "小時", "時間", "시간"),
    "days_short": ("d", "天", "天", "日", "일"),
    "loading_sessions": ("Loading sessions…", "正在加载会话…", "正在載入對話…", "セッションを読み込み中…", "세션 불러오는 중…"),
    "codex_path_label": ("Executable", "可执行文件", "執行檔", "実行ファイル", "실행 파일"),
    "codex_proxy_label": ("HTTP(S) proxy", "HTTP(S) 代理", "HTTP(S) 代理", "HTTP(S) プロキシ", "HTTP(S) 프록시"),
    "opencode_url_label": ("Server URL", "服务地址", "服務位址", "サーバー URL", "서버 URL"),
    "opencode_directory_label": ("Workspace directory", "工作目录", "工作目錄", "作業ディレクトリ", "작업 폴더"),
    "codex_interval_label": ("Codex interval", "Codex 间隔", "Codex 間隔", "Codex 間隔", "Codex 간격"),
    "opencode_interval_label": ("OpenCode interval", "OpenCode 间隔", "OpenCode 間隔", "OpenCode 間隔", "OpenCode 간격"),
    "interval_hint": ("Seconds; saved immediately.", "秒；修改后立即保存。", "秒；修改後立即儲存。", "秒。変更は即時保存されます。", "초. 변경 즉시 저장됩니다."),
    "codex_section": ("Codex", "Codex", "Codex", "Codex", "Codex"),
    "opencode_section": ("OpenCode", "OpenCode", "OpenCode", "OpenCode", "OpenCode"),
    "auto_watch_desc": ("Watches running and quota-interrupted sessions. Default on.", "自动监控运行中和因额度耗尽中断的会话，默认开启。", "自動監控執行中和因額度耗盡中斷的對話，預設開啟。", "実行中・残量不足のセッションを監視します。既定 ON。", "실행 중 및 한도 소진 세션을 감시합니다. 기본 켜짐."),
    "keeper_desc": ("Starts the next Codex window when no recovery is pending. Default off.", "无待恢复任务时启动下一个 Codex 窗口，默认关闭。", "無待恢復任務時啟動下一個 Codex 視窗，預設關閉。", "再開待ちがない場合に次の Codex 枠を開始します。既定 OFF。", "복구 대기가 없으면 다음 Codex 창을 시작합니다. 기본 꺼짐."),
})
for _key, _texts in EXTRA.items():
    EN[_key] = _texts[0]
    for _language, _text in zip(list(LANGUAGES)[1:], _texts[1:]):
        TRANSLATIONS[_language][_key] = _text


def tr(key, language="en"):
    return TRANSLATIONS.get(language, EN).get(key, EN.get(key, key))


def duration_label(minutes, language="en"):
    if minutes == 300:
        return tr("five_hours", language)
    if minutes == 10080:
        return tr("one_week", language)
    if minutes == 43200:
        return tr("one_month", language)
    return f"{minutes or '?'} {tr('minutes', language)}"
