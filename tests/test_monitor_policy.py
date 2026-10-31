import copy
import uuid

from auto_resume_agent.engine import Engine
from auto_resume_agent.store import Store
from auto_resume_agent import window_keeper as keeper
from auto_resume_agent.backends import selected_store
from auto_resume_agent.cli import main
from auto_resume_agent.model import wait_for_check

NOW = 1_800_000_000

class Backend:
    def __init__(self, count=0):
        self.rows = [{'id':str(uuid.uuid4()), 'source':'cli', 'updatedAt':NOW} for _ in range(count)]
        self.turns = {r['id']:{'id':str(uuid.uuid4()),'status':'inProgress'} for r in self.rows}
        self.used, self.week, self.reads, self.closed = 10, 20, 0, 0
        self.sent, self.helpers = [], []
    def usage(self):
        self.reads += 1
        return {'rateLimits': {'primary':{'usedPercent':self.used,'windowDurationMins':300,'resetsAt':NOW+100},
                               'secondary':{'usedPercent':self.week,'windowDurationMins':10080,'resetsAt':NOW+200}}}
    def threads(self,cursor=None):return {'data':copy.deepcopy(self.rows),'nextCursor':None}
    def latest(self,tid):return copy.deepcopy(self.turns[tid])
    def thread(self,tid):return next(r for r in self.rows if r['id']==tid)
    def submit(self,tid,message):self.sent.append(tid);return 'queued'
    def close(self):self.closed += 1
    def activate_window(self,created,can_send):
        assert can_send()
        tid=str(uuid.uuid4());created(tid);self.helpers.append(tid);return 'completed'


def test_idle_available_never_starts_helper(tmp_path):
    store=Store(tmp_path);keeper.set_enabled(store,True)
    b=Backend();engine=Engine(store,b,lambda:NOW)
    assert engine.tick()['delay']==30
    engine.clock=lambda:NOW+102
    engine.tick()
    assert not b.sent and not b.helpers


def test_running_sessions_are_watched_and_all_quota_failures_resume_after_week(tmp_path):
    store=Store(tmp_path);store.set('enabled',True);keeper.set_enabled(store,True)
    b=Backend(3);engine=Engine(store,b,lambda:NOW)
    engine.tick()
    assert len(store.watched())==3 and not b.sent
    b.used=b.week=100
    for t in b.turns.values():
        t.update(status='failed',completedAt=NOW+10,error={'codexErrorInfo':'usageLimitExceeded'})
    engine.clock=lambda:NOW+30;engine.tick()
    assert len(store.records())==3 and not b.sent
    b.used=0
    engine.clock=lambda:NOW+102;engine.tick()
    assert not b.sent and not b.helpers
    b.week=0
    engine.clock=lambda:NOW+202;engine.tick()
    assert set(b.sent)==set(b.turns) and len(b.sent)==3 and not b.helpers
    engine.tick()
    assert len(b.sent)==3


def test_depleted_idle_arms_helper_and_sleep_wake_refreshes_once(tmp_path):
    store=Store(tmp_path);keeper.set_enabled(store,True)
    b=Backend();b.used=100
    engine=Engine(store,b,lambda:NOW)
    engine.tick();assert not b.helpers
    b.used=0
    engine.clock=lambda:NOW+102
    engine.tick()
    assert len(b.helpers)==1 and b.closed==1 and b.reads==2
    engine.tick();assert len(b.helpers)==1


def test_blocked_quota_limits_upstream_polls(tmp_path):
    store=Store(tmp_path);b=Backend();b.used=100;b.week=100
    engine=Engine(store,b,lambda:NOW);engine.tick()
    engine.clock=lambda:NOW+30;engine.tick()
    engine.clock=lambda:NOW+60;engine.tick()
    assert b.reads==1
    engine.clock=lambda:NOW+202;engine.tick()
    assert b.reads==2


def test_independent_intervals_cli_and_restart(tmp_path,capsys):
    args=['--home',str(tmp_path)]
    assert main(args+['interval','45'])==0
    assert main(args+['--agent','opencode','interval','90'])==0
    s=Store(tmp_path)
    assert s.interval()==45 and selected_store(s,'opencode').interval()==90
    assert main(args+['interval'])==0
    assert '45' in capsys.readouterr().out


def test_wall_clock_wait_returns_on_wake_without_remaining_sleep():
    class Stop:
        now=NOW
        waits=[]
        def is_set(self):return False
        def wait(self,seconds):
            self.waits.append(seconds);self.now+=7200;return False
    stop=Stop()
    wait_for_check(stop,3600,clock=lambda:stop.now)
    assert stop.waits==[1]


def test_new_codex_default_enabled_but_saved_pause_survives(tmp_path):
    store=Store(tmp_path)
    assert store.get('enabled') is True
    store.set('enabled',False)
    assert Store(tmp_path).get('enabled') is False
    assert not keeper.enabled(store)


def test_pending_quota_recovery_suppresses_armed_helper(tmp_path):
    store=Store(tmp_path);keeper.set_enabled(store,True)
    b=Backend();b.used=100
    engine=Engine(store,b,lambda:NOW);engine.tick()
    from auto_resume_agent.model import usage
    b.used=0
    keeper.tick(store,b,usage(b.usage()),NOW+102,has_pending=True)
    assert not b.helpers
