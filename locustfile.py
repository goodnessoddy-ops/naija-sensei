"""
locustfile.py — load test for NaijaSensei, simulating real student,
teacher, parent, and admin sessions rather than hammering one endpoint
in isolation.

READ THIS BEFORE RUNNING

1. COST WARNING, UNLESS YOU USE MOCK_AI: /chat, /exam/start,
   /exam/submit, and /career/guidance all call real AI providers (see
   ai_providers.py + api_costs.py — you're already tracking these
   costs). Running this with a lot of simulated users will generate
   real Mistral/ElevenLabs spend and can get you rate-limited by those
   providers, which will make your results look like a NaijaSensei
   problem when it's actually a "too many bots hit Mistral at once"
   problem.

   To test pure app/DB/event-loop throughput WITHOUT any real AI cost,
   set MOCK_AI=true in the SERVER's environment before starting it —
   every AI call then returns a canned response instantly instead of
   calling a real provider (see ai_providers.py's MOCK_AI short-circuit,
   near the top of the file). This lets you push hundreds of simulated
   users through the exam/chat flows to stress-test the Postgres pool
   without touching a real provider at all. If you're testing real
   answer quality or latency, leave MOCK_AI off and start SMALL
   (5-20 users) instead, watching /admin/api-costs while it runs.

2. RUN THIS AGAINST STAGING, NOT PRODUCTION. Every simulated user really
   registers an account, really starts and submits exams, really
   creates student/child accounts (teacher/parent flows), and writes
   real rows into whatever database DATABASE_URL points at.

3. WHAT THIS TESTS:
   - NaijaSenseiStudent (weight 20 — most of the simulated traffic,
     matching real usage): register, login, chat, exam start/submit,
     heartbeat, history, streak, broadcasts, career guidance, and
     billing (status/plans checks, checkout, redemption — see the
     TEST_REDEMPTION_CODES note near the top of this file for testing
     the successful-redemption path specifically).
   - TeacherUser (weight 2): register-with-role, create a class, create
     students, view class overview/classroom activity, send a broadcast.
   - ParentUser (weight 2): register-with-role, create a child account,
     view linked students and pending requests.
   - AdminUser (weight 1): read-heavy admin dashboard views (stats,
     users, exams, provider health, api costs) plus an occasional
     broadcast. admin.py uses a completely different auth scheme from
     everything else — a single shared X-Admin-Password header, not a
     JWT login — see its class docstring below.

INSTALL & RUN
    pip install locust --break-system-packages
    locust -f locustfile.py --host=https://your-staging-url.com

Then open http://localhost:8089, set the number of users and spawn
rate, and watch requests/sec, response times, and failure rate live.
For a quick headless run without the web UI:
    locust -f locustfile.py --host=https://your-staging-url.com \
        --users 20 --spawn-rate 2 --run-time 3m --headless

To include AdminUser sessions, set ADMIN_PASSWORD in the environment
Locust itself runs in (it needs to match the server's own
ADMIN_PASSWORD to actually authenticate) before starting Locust:
    export ADMIN_PASSWORD=yourpassword
    locust -f locustfile.py --host=https://your-staging-url.com
Without it, simulated admins skip every task for the whole run —
harmless, but wastes a few simulated user slots, so set it if you want
that traffic actually exercised.
"""

import os
import random
import uuid

from locust import HttpUser, task, between, events

SUBJECTS = ["Mathematics", "English Language", "Physics", "Chemistry", "Biology"]

SAMPLE_QUESTIONS = [
    "Can you explain photosynthesis in simple terms?",
    "What's the difference between mitosis and meiosis?",
    "How do I solve a quadratic equation?",
    "Explain Newton's second law of motion.",
    "What caused the Nigerian Civil War?",
    "How does compound interest work?",
]

# Optional pool of real, pre-generated redemption codes for testing the
# successful-redemption path under load (see redeem_code() below). Without
# this set, every redemption attempt uses a random fake code and only
# exercises the "code isn't valid" rejection path — still useful, just
# incomplete. Generate real ones first:
#   POST /billing/admin/generate-codes (with a real X-Admin-Password)
# then:
#   export TEST_REDEMPTION_CODES=NSAI-AAAA-1111,NSAI-BBBB-2222
TEST_REDEMPTION_CODES = [c.strip() for c in os.environ.get("TEST_REDEMPTION_CODES", "").split(",") if c.strip()]


def _rand_suffix(n=10):
    return uuid.uuid4().hex[:n]


# ─────────────────────────────────────────────────────────────────────────
# STUDENT
# ─────────────────────────────────────────────────────────────────────────

class NaijaSenseiStudent(HttpUser):
    """One simulated student: registers, logs in, then behaves like a
    real user for the rest of the run — asking chat questions, taking an
    exam, checking in via heartbeat."""

    weight = 20  # most of the simulated traffic, matching real usage

    # Gap between a simulated student's actions — real students don't
    # fire requests back-to-back, they read/think between them.
    wait_time = between(3, 12)

    def on_start(self):
        """Runs once per simulated user at the start of the test —
        register a brand-new throwaway account so users don't collide
        with each other or with real accounts."""
        self.uid = _rand_suffix()
        self.token = None

        resp = self.client.post(
            "/auth/register",
            json={
                "username": f"loadtest_{self.uid}",
                "email": f"loadtest_{self.uid}@example.test",
                "full_name": "Load Test Student",
                "password": "LoadTest123!",
            },
            name="/auth/register",
        )
        if resp.status_code == 201:
            self.token = resp.json()["access_token"]
        else:
            # Registration can fail on a rare username collision or if
            # the account already exists from a previous run — fall back
            # to logging in instead of aborting this simulated user.
            self._login()

    def _login(self):
        resp = self.client.post(
            "/auth/login",
            # OAuth2PasswordRequestForm expects form-encoded, not JSON
            data={"username": f"loadtest_{self.uid}", "password": "LoadTest123!"},
            name="/auth/login",
        )
        if resp.status_code == 200:
            self.token = resp.json()["access_token"]

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    # ── Cheap, frequent actions ─────────────────────────────────────────────

    @task(10)
    def heartbeat(self):
        """Fired every ~60s by the real frontend while a tab is open —
        the highest-volume authenticated endpoint in the whole app, and
        a good stress test for the activity_minutes upsert."""
        if not self.token:
            return
        self.client.post("/auth/heartbeat", headers=self._auth_headers(), name="/auth/heartbeat")

    @task(6)
    def check_history(self):
        if not self.token:
            return
        self.client.get("/history", headers=self._auth_headers(), name="/history")

    @task(4)
    def check_streak(self):
        if not self.token:
            return
        self.client.get("/streak", headers=self._auth_headers(), name="/streak")

    @task(3)
    def check_broadcasts(self):
        if not self.token:
            return
        self.client.get("/broadcasts/me", headers=self._auth_headers(), name="/broadcasts/me")

    # ── AI-calling actions — lower weight, real provider cost per call
    #    unless MOCK_AI=true is set on the server ─────────────────────────

    @task(4)
    def chat(self):
        """Streaming SSE endpoint — response is consumed to completion so
        Locust measures the full time-to-finish, not just time-to-first-byte."""
        if not self.token:
            return
        with self.client.post(
            "/chat",
            json={"message": random.choice(SAMPLE_QUESTIONS), "history": []},
            headers=self._auth_headers(),
            name="/chat",
            stream=True,
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                for _ in resp.iter_lines():
                    pass  # drain the stream so timing reflects the full reply
                resp.success()
            else:
                resp.failure(f"chat failed: {resp.status_code}")

    @task(1)
    def take_a_quick_exam(self):
        """Start and submit a short exam in one task — exercises both
        of exam.py's async DB paths end to end."""
        if not self.token:
            return
        start_resp = self.client.post(
            "/exam/start",
            json={
                "subjects": [random.choice(SUBJECTS)],
                "mode": "custom",
                "num_mcq": 5,
                "num_theory": 0,
                "duration_min": 10,
            },
            headers=self._auth_headers(),
            name="/exam/start",
        )
        if start_resp.status_code != 200:
            return
        data = start_resp.json()
        session_id = data.get("session_id")
        questions = data.get("questions", [])
        if not session_id or not questions:
            return

        # Dummy answers — correctness doesn't matter for a load test,
        # only that the submit path runs its full grading + save logic.
        answers = {q["id"]: "A" for q in questions if "id" in q}
        self.client.post(
            "/exam/submit",
            json={"session_id": session_id, "answers": answers},
            headers=self._auth_headers(),
            name="/exam/submit",
        )

    @task(1)
    def career_guidance(self):
        if not self.token:
            return
        self.client.post(
            "/career/guidance",
            json={"message": "What career should I consider based on my results?", "history": []},
            headers=self._auth_headers(),
            name="/career/guidance",
        )

    # ── Billing/premium — added after billing.py existed; the original
    # version of this file predated it and had zero coverage here. ────────

    @task(4)
    def check_billing_status(self):
        """Cheap, frequent — matches how a real frontend would check
        premium status on load (e.g. rendering the Premium screen)."""
        if not self.token:
            return
        self.client.get("/billing/status", headers=self._auth_headers(), name="/billing/status")

    @task(2)
    def view_billing_plans(self):
        """Public endpoint, no auth needed — still worth hitting under
        load since it's what the Premium screen's plan cards render from."""
        self.client.get("/billing/plans", name="/billing/plans")

    @task(1)
    def start_checkout(self):
        """Real-world weight: a student upgrades rarely, not every
        session. IMPORTANT — security.py's RateLimitMiddleware limits
        /billing/checkout and /billing/redeem together to 15 requests
        per 5 minutes PER IP, not per simulated user. Locust normally
        runs all simulated users from one machine (one IP), so under
        any real concurrency most of these calls will correctly get
        429'd almost immediately — that's the rate limiter working as
        designed, not a bug in the app. Don't be alarmed by a high
        failure rate on this specific task; watch /auth/heartbeat or
        /history instead for the app's general throughput health.
        Also: if PAYSTACK_SECRET_KEY is genuinely configured on the
        server, this creates a real pending Paystack transaction (no
        money moves until someone actually completes checkout on
        Paystack's page, which this task never does) — harmless, but
        worth knowing it's not a total no-op against a live-configured
        server."""
        if not self.token:
            return
        plan = random.choice(["monthly", "termly", "annual"])
        self.client.post(
            "/billing/checkout",
            json={"plan": plan},
            headers=self._auth_headers(),
            name="/billing/checkout",
        )

    @task(1)
    def redeem_code(self):
        """Without TEST_REDEMPTION_CODES set, every attempt hits the
        "code isn't valid" 400 path — still useful for exercising the
        lookup query and the shared rate limit under load, just doesn't
        cover the successful-redemption path. To test that path too,
        pre-generate real codes against a real admin password
        (POST /billing/admin/generate-codes) and pass them in:
            export TEST_REDEMPTION_CODES=NSAI-AAAA-1111,NSAI-BBBB-2222
        Each code is single-use, so with N simulated users sharing a
        small code pool, only the first successful redeemer per code
        gets premium — everyone else correctly gets "already used"
        (also a legitimate thing to load-test, not a bug)."""
        if not self.token:
            return
        pool = TEST_REDEMPTION_CODES
        code = random.choice(pool) if pool else f"NSAI-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"
        self.client.post(
            "/billing/redeem",
            json={"code": code},
            headers=self._auth_headers(),
            name="/billing/redeem",
        )


# ─────────────────────────────────────────────────────────────────────────
# TEACHER
# ─────────────────────────────────────────────────────────────────────────

class TeacherUser(HttpUser):
    """One simulated teacher: registers with role=teacher, creates a
    class, then repeatedly creates students, checks the class overview,
    and occasionally sends a broadcast — dashboard.py's teacher flows,
    which are write-heavier than the student flows above."""

    weight = 2
    wait_time = between(5, 15)

    def on_start(self):
        self.uid = _rand_suffix()
        self.token = None
        self.class_id = None
        self._student_count = 0

        resp = self.client.post(
            "/dashboard/register-with-role",
            json={
                "username": f"loadteacher_{self.uid}",
                "email": f"loadteacher_{self.uid}@example.test",
                "full_name": "Load Test Teacher",
                "password": "LoadTest123!",
                "role": "teacher",
            },
            name="/dashboard/register-with-role [teacher]",
        )
        if resp.status_code == 200:
            self.token = resp.json()["access_token"]
            self._create_class()

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def _create_class(self):
        resp = self.client.post(
            "/dashboard/teacher/class",
            json={"name": f"Load Test Class {self.uid}"},
            headers=self._auth_headers(),
            name="/dashboard/teacher/class",
        )
        # class_id isn't in the response (only name + invite_code), so
        # pull it back from /teacher/classes rather than guessing it.
        if resp.status_code == 200:
            classes_resp = self.client.get(
                "/dashboard/teacher/classes",
                headers=self._auth_headers(),
                name="/dashboard/teacher/classes [setup]",
            )
            if classes_resp.status_code == 200:
                classes = classes_resp.json().get("classes", [])
                if classes:
                    self.class_id = classes[0].get("id")

    @task(5)
    def view_overview(self):
        if not self.token:
            return
        self.client.get("/dashboard/teacher/overview", headers=self._auth_headers(), name="/dashboard/teacher/overview")

    @task(3)
    def view_classes(self):
        if not self.token:
            return
        self.client.get("/dashboard/teacher/classes", headers=self._auth_headers(), name="/dashboard/teacher/classes")

    @task(3)
    def view_classroom_activity(self):
        if not self.token:
            return
        self.client.get(
            "/dashboard/teacher/classroom-activity",
            headers=self._auth_headers(),
            name="/dashboard/teacher/classroom-activity",
        )

    @task(2)
    def create_student(self):
        """Teacher-created student accounts — a real, frequently-used
        flow for schools onboarding students in bulk, and a good test
        of dashboard.py's password-encryption-at-rest path."""
        if not self.token:
            return
        self._student_count += 1
        self.client.post(
            "/dashboard/teacher/create-student",
            json={
                "username": f"loadstudent_{self.uid}_{self._student_count}",
                "full_name": "Load Test Created Student",
                "password": "LoadTest123!",
                "class_id": self.class_id,
            },
            headers=self._auth_headers(),
            name="/dashboard/teacher/create-student",
        )

    @task(1)
    def send_broadcast(self):
        if not self.token:
            return
        self.client.post(
            "/dashboard/teacher/broadcast",
            json={"message": "[Load test] Reminder: check your exam schedule.", "class_id": self.class_id},
            headers=self._auth_headers(),
            name="/dashboard/teacher/broadcast",
        )


# ─────────────────────────────────────────────────────────────────────────
# PARENT
# ─────────────────────────────────────────────────────────────────────────

class ParentUser(HttpUser):
    """One simulated parent: registers with role=parent, creates a
    child account, then repeatedly checks on linked students and
    pending link requests — dashboard.py's parent flows."""

    weight = 2
    wait_time = between(5, 15)

    def on_start(self):
        self.uid = _rand_suffix()
        self.token = None
        self._child_count = 0

        resp = self.client.post(
            "/dashboard/register-with-role",
            json={
                "username": f"loadparent_{self.uid}",
                "email": f"loadparent_{self.uid}@example.test",
                "full_name": "Load Test Parent",
                "password": "LoadTest123!",
                "role": "parent",
            },
            name="/dashboard/register-with-role [parent]",
        )
        if resp.status_code == 200:
            self.token = resp.json()["access_token"]
            self._create_child()

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def _create_child(self):
        self._child_count += 1
        self.client.post(
            "/dashboard/parent/create-child",
            json={
                "username": f"loadchild_{self.uid}_{self._child_count}",
                "full_name": "Load Test Child",
                "password": "LoadTest123!",
            },
            headers=self._auth_headers(),
            name="/dashboard/parent/create-child [setup]",
        )

    @task(5)
    def view_students(self):
        if not self.token:
            return
        self.client.get("/dashboard/parent/students", headers=self._auth_headers(), name="/dashboard/parent/students")

    @task(3)
    def view_pending_requests(self):
        if not self.token:
            return
        self.client.get(
            "/dashboard/parent/pending-requests",
            headers=self._auth_headers(),
            name="/dashboard/parent/pending-requests",
        )

    @task(1)
    def create_another_child(self):
        if not self.token:
            return
        self._create_child()


# ─────────────────────────────────────────────────────────────────────────
# ADMIN
# ─────────────────────────────────────────────────────────────────────────

class AdminUser(HttpUser):
    """One simulated admin session, hitting the read-heavy dashboard
    views in admin.py plus an occasional broadcast.

    admin.py's auth is NOT the JWT login every other route uses — it's a
    single shared password checked via the X-Admin-Password header
    against ADMIN_PASSWORD in the server's .env (see admin.py's
    _require_admin). So this class reads ADMIN_PASSWORD from Locust's
    own environment and sends it as a header on every request — there's
    no login call, no token, and no per-admin identity at all. If
    ADMIN_PASSWORD isn't set, every task below no-ops for the whole run."""

    weight = 1
    wait_time = between(8, 20)

    def on_start(self):
        self.admin_password = os.environ.get("ADMIN_PASSWORD")

    def _admin_headers(self):
        return {"X-Admin-Password": self.admin_password} if self.admin_password else {}

    @task(5)
    def view_stats(self):
        if not self.admin_password:
            return
        self.client.get("/admin/stats", headers=self._admin_headers(), name="/admin/stats")

    @task(4)
    def view_users(self):
        if not self.admin_password:
            return
        self.client.get("/admin/users", headers=self._admin_headers(), name="/admin/users")

    @task(3)
    def view_exams(self):
        if not self.admin_password:
            return
        self.client.get("/admin/exams", headers=self._admin_headers(), name="/admin/exams")

    @task(3)
    def view_provider_health(self):
        if not self.admin_password:
            return
        self.client.get("/admin/provider-health", headers=self._admin_headers(), name="/admin/provider-health")

    @task(3)
    def view_api_costs(self):
        if not self.admin_password:
            return
        self.client.get("/admin/api-costs", headers=self._admin_headers(), name="/admin/api-costs")

    @task(2)
    def view_classroom(self):
        if not self.admin_password:
            return
        self.client.get("/admin/classroom", headers=self._admin_headers(), name="/admin/classroom")

    @task(1)
    def send_admin_broadcast(self):
        if not self.admin_password:
            return
        self.client.post(
            "/admin/broadcast",
            json={"message": "[Load test] Platform-wide announcement.", "target": "all"},
            headers=self._admin_headers(),
            name="/admin/broadcast",
        )


@events.quitting.add_listener
def _summary(environment, **kwargs):
    stats = environment.stats.total
    print(
        f"\n[locust] {stats.num_requests} requests, "
        f"{stats.num_failures} failures, "
        f"median {stats.median_response_time}ms, "
        f"95th pct {stats.get_response_time_percentile(0.95)}ms"
    )