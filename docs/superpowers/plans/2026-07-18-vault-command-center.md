# V.A.U.L.T. 指揮中心 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 project-golem 加上語音層（本地 faster-whisper 聽、Edge-TTS 說）與 V.A.U.L.T. 深色指揮中心頁面，本地大腦切為 deepseek-r1:8b。

**Architecture:** 新增獨立 Python FastAPI sidecar（`apps/voice-service/`，port 8765）處理 STT/TTS；新增 Next.js 頁面 `dashboard/vault` 走 golem 現有 `/api/chat` + socket.io 回覆流；本地模型透過 golem 既有 OllamaClient/env 設定接入。golem 現有後端程式碼零修改（僅前端加一個 nav 項與 i18n 兩行）。

**Tech Stack:** Python 3.10+、FastAPI、faster-whisper（small, zh）、edge-tts（zh-TW-HsiaoChenNeural）；Next.js App Router、Tailwind、socket.io client（golem 既有）。

## Global Constraints

- golem 後端（Node 側）程式碼一律不修改；前端只允許改 `layout.tsx`（加一個 NAV_ITEMS 項）與 `src/lib/i18n/messages.ts`（加兩個 key）
- voice-service 只綁 `127.0.0.1`，不對外
- Ollama 模型庫在 `D:\ollama\models`（OLLAMA_MODELS 已設，伺服器 http://127.0.0.1:11434）
- 本地大腦模型名：`deepseek-r1:8b`（回覆需剝除 `<think>...</think>` 再顯示/發聲）
- TTS 聲音固定 `zh-TW-HsiaoChenNeural`；斷網時只顯示文字、不報錯彈窗
- 所有既有整合點已驗證：`POST /api/chat {golemId,message}`（回覆走 socket `log` 事件，payload 含 `golemId`、`type:'agent'`、`raw`）、`GET/POST /api/system/config`（欄位 `golemBackend`、`golemOllamaBrainModel`）、`GET /api/skills`、`GET /api/calendar/events`（回 `{events:[...]}`）、Ollama `GET /api/tags`（瀏覽器可直連，OLLAMA_ORIGINS 已含 localhost:*）
- 前端工具：`apiGet/apiPost` 自 `@/lib/api-client`，`socket` 自 `@/lib/socket`，`useGolem` 自 `@/components/GolemContext`，icon 用 lucide-react

---

### Task 1: voice-service 骨架 + /health + /tts

**Files:**
- Create: `C:/Users/User/Desktop/project-golem/apps/voice-service/main.py`
- Create: `C:/Users/User/Desktop/project-golem/apps/voice-service/requirements.txt`
- Create: `C:/Users/User/Desktop/project-golem/apps/voice-service/start-voice.bat`
- Test: `C:/Users/User/Desktop/project-golem/apps/voice-service/test_voice.py`

**Interfaces:**
- Produces: `GET /health → {"ok":true,"whisper_loaded":bool}`；`POST /tts {"text":str} → audio/mpeg bytes`。Task 2 會在同一 `main.py` 加 `/stt`；Task 4 前端呼叫 `http://127.0.0.1:8765` 全部三個端點。

- [ ] **Step 1: 建立 requirements.txt**

```
fastapi
uvicorn[standard]
edge-tts
faster-whisper
python-multipart
pytest
httpx
```

- [ ] **Step 2: 寫失敗測試 test_voice.py**

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True

def test_tts_returns_mp3():
    r = client.post("/tts", json={"text": "指揮中心已上線"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("audio/mpeg")
    assert len(r.content) > 1000  # 有實際音訊資料

def test_tts_empty_text_400():
    r = client.post("/tts", json={"text": "  "})
    assert r.status_code == 400
```

- [ ] **Step 3: 確認測試失敗**

Run: `cd C:/Users/User/Desktop/project-golem/apps/voice-service && python -m venv .venv && .venv/Scripts/pip install -r requirements.txt && .venv/Scripts/python -m pytest test_voice.py -v`
Expected: FAIL（`main` 模組不存在）

- [ ] **Step 4: 寫 main.py（/health + /tts）**

```python
import io
import os
import tempfile

import edge_tts
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

app = FastAPI(title="golem-voice-service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

VOICE = "zh-TW-HsiaoChenNeural"
_whisper_model = None


@app.get("/health")
def health():
    return {"ok": True, "whisper_loaded": _whisper_model is not None}


@app.post("/tts")
async def tts(payload: dict):
    text = str(payload.get("text", "")).strip()
    if not text:
        raise HTTPException(status_code=400, detail="text required")
    # ponytail: 語音朗讀截到 600 字，超長回覆前端仍顯示全文
    communicate = edge_tts.Communicate(text[:600], VOICE)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    if buf.tell() == 0:
        raise HTTPException(status_code=502, detail="edge-tts returned no audio")
    return Response(content=buf.getvalue(), media_type="audio/mpeg")
```

- [ ] **Step 5: 跑測試確認通過**

Run: `.venv/Scripts/python -m pytest test_voice.py -v`
Expected: 3 passed（需要網路，edge-tts 連微軟服務）

- [ ] **Step 6: 寫 start-voice.bat**

```bat
@echo off
cd /d %~dp0
if not exist .venv (
    python -m venv .venv
    .venv\Scripts\pip install -r requirements.txt
)
.venv\Scripts\uvicorn main:app --host 127.0.0.1 --port 8765
```

- [ ] **Step 7: Commit**

```bash
cd C:/Users/User/Desktop/project-golem && git add apps/voice-service && git commit -m "feat(voice): voice-service sidecar with /health and /tts (Edge-TTS zh-TW)"
```

---

### Task 2: /stt（faster-whisper 本地辨識）

**Files:**
- Modify: `C:/Users/User/Desktop/project-golem/apps/voice-service/main.py`（加在 /tts 之後）
- Test: `C:/Users/User/Desktop/project-golem/apps/voice-service/test_voice.py`（追加）

**Interfaces:**
- Produces: `POST /stt`（multipart，欄位名 `audio`）`→ {"text": str}`；模型 lazy-load（首次呼叫下載 small 模型約 460MB，GPU 失敗自動退 CPU）。

- [ ] **Step 1: 追加失敗測試（TTS→STT 迴圈自證）**

```python
def test_stt_roundtrip():
    # 先用 /tts 產生一句已知中文語音，再餵給 /stt，驗證聽得懂自己說的話
    tts_r = client.post("/tts", json={"text": "今天天氣很好"})
    assert tts_r.status_code == 200
    r = client.post("/stt", files={"audio": ("probe.mp3", tts_r.content, "audio/mpeg")})
    assert r.status_code == 200
    text = r.json()["text"]
    assert "天氣" in text

def test_stt_empty_400():
    r = client.post("/stt", files={"audio": ("a.webm", b"", "audio/webm")})
    assert r.status_code == 400
```

- [ ] **Step 2: 確認失敗**

Run: `.venv/Scripts/python -m pytest test_voice.py::test_stt_roundtrip -v`
Expected: FAIL 404（/stt 不存在）

- [ ] **Step 3: main.py 加 /stt 與模型載入**

```python
def get_whisper():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        try:
            _whisper_model = WhisperModel("small", device="cuda", compute_type="int8_float16")
        except Exception:
            # ponytail: 無 CUDA 環境自動退 CPU int8，短句約 1-3 秒，可接受
            _whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
    return _whisper_model


@app.post("/stt")
async def stt(audio: UploadFile = File(...)):
    data = await audio.read()
    if not data:
        raise HTTPException(status_code=400, detail="empty audio")
    suffix = os.path.splitext(audio.filename or "clip.webm")[1] or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(data)
        tmp_path = f.name
    try:
        model = get_whisper()
        segments, _info = model.transcribe(tmp_path, language="zh", beam_size=5)
        text = "".join(seg.text for seg in segments).strip()
    finally:
        os.unlink(tmp_path)
    return {"text": text}
```

- [ ] **Step 4: 跑全部測試**

Run: `.venv/Scripts/python -m pytest test_voice.py -v`
Expected: 5 passed（roundtrip 首次跑會下載 whisper small 模型，耐心等）

- [ ] **Step 5: Commit**

```bash
cd C:/Users/User/Desktop/project-golem && git add apps/voice-service && git commit -m "feat(voice): local /stt via faster-whisper (zh, GPU with CPU fallback)"
```

---

### Task 3: 本地大腦設為 deepseek-r1:8b

**Files:**
- Modify: `C:/Users/User/Desktop/project-golem/.env`（EnvManager 管理的檔；只加/改一行，不動其他行）

**Interfaces:**
- Produces: env `GOLEM_OLLAMA_BRAIN_MODEL=deepseek-r1:8b`。golem 的 OllamaClient（`src/services/OllamaClient.js:32`）在 `GOLEM_BACKEND=ollama` 時會用它。Task 4 的切換開關只改 `golemBackend`，模型名由此處決定。

- [ ] **Step 1: 前置確認模型存在**

Run: `ollama list | grep deepseek`
Expected: `deepseek-r1:8b` 一行。若沒有：`ollama pull deepseek-r1:8b` 先完成。

- [ ] **Step 2: 改 .env**

在 `C:/Users/User/Desktop/project-golem/.env` 中：若已有 `GOLEM_OLLAMA_BRAIN_MODEL=` 行就改值為 `deepseek-r1:8b`；沒有就在檔尾加：

```
GOLEM_OLLAMA_BRAIN_MODEL=deepseek-r1:8b
```

- [ ] **Step 3: 驗證模型真的能推理**

Run: `curl -s http://127.0.0.1:11434/api/chat -d "{\"model\":\"deepseek-r1:8b\",\"stream\":false,\"messages\":[{\"role\":\"user\",\"content\":\"用一句話介紹你自己\"}]}"`
Expected: JSON 內 `message.content` 有中文回覆（可能含 `<think>` 段，屬正常）

- [ ] **Step 4: Commit（若 .env 在 gitignore 則略過 commit，僅記錄於 PR/回報說明）**

```bash
cd C:/Users/User/Desktop/project-golem && git check-ignore .env && echo "env ignored, skip commit" || (git add .env && git commit -m "chore: local brain model -> deepseek-r1:8b")
```

---

### Task 4: VAULT 指揮中心頁面

**Files:**
- Create: `C:/Users/User/Desktop/project-golem/web-dashboard/src/app/dashboard/vault/page.tsx`
- Modify: `C:/Users/User/Desktop/project-golem/web-dashboard/src/app/dashboard/layout.tsx`（NAV_ITEMS 的 chat 群組加一項）
- Modify: `C:/Users/User/Desktop/project-golem/web-dashboard/src/lib/i18n/messages.ts`（zh 區塊約 line 27 附近、en 區塊約 line 444 附近各加一個 key）

**Interfaces:**
- Consumes: voice-service `GET /health`、`POST /stt`（multipart `audio`）、`POST /tts {"text"}`（Task 1-2）；golem `POST /api/chat {golemId,message}`、socket `log` 事件 `{golemId,type,raw}`、`GET/POST /api/system/config`、`GET /api/skills`、`GET /api/calendar/events`、Ollama `GET http://127.0.0.1:11434/api/tags`
- Produces: 路由 `/dashboard/vault`

- [ ] **Step 1: layout.tsx 加 nav 項**

在 `NAV_ITEMS` 的「對話與人格」群組（`sidebar.nav.chat` 那行之前）加：

```tsx
    { labelKey: "sidebar.nav.vault", href: "/dashboard/vault", icon: Mic, group: "chat" },
```

並在該檔頂部 lucide-react import 清單加入 `Mic`（若已存在則略過）。

- [ ] **Step 2: messages.ts 加兩個 key**

zh 區（`"sidebar.nav.chat": "直接交談",` 旁）加：

```ts
    "sidebar.nav.vault": "V.A.U.L.T. 指揮中心",
```

en 區（`"sidebar.nav.chat": "Chat",` 旁）加：

```ts
    "sidebar.nav.vault": "V.A.U.L.T.",
```

- [ ] **Step 3: 建立 vault/page.tsx**

```tsx
"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { useGolem } from "@/components/GolemContext";
import { socket } from "@/lib/socket";
import { apiGet, apiPost } from "@/lib/api-client";
import { Mic, Cpu, Sparkles, CalendarDays, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

const VOICE_BASE = "http://127.0.0.1:8765";
const OLLAMA_BASE = "http://127.0.0.1:11434";

type LogPayload = { golemId?: string; type?: string; raw?: string };
type OllamaTag = { name: string; size?: number };
type SkillItem = { id?: string; name?: string; title?: string; description?: string; enabled?: boolean };
type CalEvent = { id: string; title?: string; summary?: string; start?: string; date?: string };
type SystemConfig = { golemBackend?: string; golemOllamaBrainModel?: string };
type Turn = { role: "user" | "agent"; text: string };

function stripThink(text: string): string {
    return text.replace(/<think>[\s\S]*?<\/think>/g, "").trim();
}

export default function VaultPage() {
    const { activeGolem } = useGolem();
    const [voiceOnline, setVoiceOnline] = useState(false);
    const [recording, setRecording] = useState(false);
    const [busy, setBusy] = useState(false);
    const [speaking, setSpeaking] = useState(false);
    const [turns, setTurns] = useState<Turn[]>([]);
    const [config, setConfig] = useState<SystemConfig>({});
    const [models, setModels] = useState<OllamaTag[]>([]);
    const [skills, setSkills] = useState<SkillItem[]>([]);
    const [events, setEvents] = useState<CalEvent[]>([]);
    const recorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);
    const awaitingReplyRef = useRef(false);
    const audioRef = useRef<HTMLAudioElement | null>(null);

    // ---- 資料載入 ----
    useEffect(() => {
        const load = async () => {
            try { setConfig(await apiGet<SystemConfig>("/api/system/config")); } catch { /* 離線容忍 */ }
            try {
                const t = await fetch(`${OLLAMA_BASE}/api/tags`).then(r => r.json());
                setModels(Array.isArray(t?.models) ? t.models : []);
            } catch { setModels([]); }
            try {
                const s = await apiGet<{ skills?: SkillItem[] } | SkillItem[]>("/api/skills");
                setSkills(Array.isArray(s) ? s : (Array.isArray((s as { skills?: SkillItem[] })?.skills) ? (s as { skills: SkillItem[] }).skills : []));
            } catch { setSkills([]); }
            try {
                const c = await apiGet<{ events?: CalEvent[] }>("/api/calendar/events");
                setEvents(Array.isArray(c?.events) ? c.events.slice(0, 6) : []);
            } catch { setEvents([]); }
        };
        load();
    }, []);

    // ---- voice-service 健康輪詢 ----
    useEffect(() => {
        let alive = true;
        const ping = async () => {
            try {
                const r = await fetch(`${VOICE_BASE}/health`, { signal: AbortSignal.timeout(2000) });
                if (alive) setVoiceOnline(r.ok);
            } catch { if (alive) setVoiceOnline(false); }
        };
        ping();
        const id = setInterval(ping, 5000);
        return () => { alive = false; clearInterval(id); };
    }, []);

    // ---- TTS 播放 ----
    const speak = useCallback(async (text: string) => {
        try {
            const r = await fetch(`${VOICE_BASE}/tts`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text }),
            });
            if (!r.ok) return; // 斷網/離線：靜默退化為純文字
            const url = URL.createObjectURL(await r.blob());
            const audio = new Audio(url);
            audioRef.current = audio;
            setSpeaking(true);
            audio.onended = () => { setSpeaking(false); URL.revokeObjectURL(url); };
            await audio.play().catch(() => setSpeaking(false));
        } catch { /* 不打擾使用者 */ }
    }, []);

    // ---- 接收 golem 回覆 ----
    useEffect(() => {
        const onLog = (payload: unknown) => {
            const data = payload as LogPayload;
            if (!awaitingReplyRef.current) return;
            if (data?.golemId !== activeGolem || data?.type !== "agent" || !data?.raw) return;
            awaitingReplyRef.current = false;
            setBusy(false);
            const clean = stripThink(data.raw);
            setTurns(prev => [...prev, { role: "agent", text: clean }]);
            void speak(clean);
        };
        socket.on("log", onLog);
        return () => { socket.off("log", onLog); };
    }, [activeGolem, speak]);

    // ---- 按住說話 ----
    const startRecording = useCallback(async () => {
        if (!voiceOnline || busy) return;
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const rec = new MediaRecorder(stream, { mimeType: "audio/webm" });
            chunksRef.current = [];
            rec.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
            rec.onstop = async () => {
                stream.getTracks().forEach(t => t.stop());
                const blob = new Blob(chunksRef.current, { type: "audio/webm" });
                if (blob.size < 1000) return; // 太短視為誤觸
                setBusy(true);
                try {
                    const form = new FormData();
                    form.append("audio", blob, "clip.webm");
                    const sttRes = await fetch(`${VOICE_BASE}/stt`, { method: "POST", body: form }).then(r => r.json());
                    const text = String(sttRes?.text || "").trim();
                    if (!text) { setBusy(false); return; }
                    setTurns(prev => [...prev, { role: "user", text }]);
                    awaitingReplyRef.current = true;
                    await apiPost("/api/chat", { golemId: activeGolem, message: text });
                } catch { setBusy(false); awaitingReplyRef.current = false; }
            };
            rec.start();
            recorderRef.current = rec;
            setRecording(true);
        } catch { /* 麥克風權限拒絕：按鈕維持原狀，使用者可用聊天頁打字 */ }
    }, [voiceOnline, busy, activeGolem]);

    const stopRecording = useCallback(() => {
        recorderRef.current?.stop();
        recorderRef.current = null;
        setRecording(false);
    }, []);

    // ---- 大腦切換 ----
    const isLocalBrain = config.golemBackend === "ollama";
    const toggleBrain = useCallback(async () => {
        const next = isLocalBrain ? "gemini" : "ollama";
        try {
            await apiPost("/api/system/config", { golemBackend: next });
            setConfig(await apiGet<SystemConfig>("/api/system/config"));
        } catch { /* 顯示維持原狀 */ }
    }, [isLocalBrain]);

    const brainLabel = isLocalBrain
        ? `本地 · ${config.golemOllamaBrainModel || "ollama"}`
        : `雲端 · ${config.golemBackend || "gemini"}`;

    return (
        <div className="min-h-full bg-[#05070d] text-slate-200 p-6 font-mono">
            <header className="mb-6 flex items-end justify-between border-b border-cyan-900/50 pb-3">
                <div>
                    <h1 className="text-2xl tracking-[0.3em] text-cyan-300">V.A.U.L.T.</h1>
                    <p className="text-xs text-slate-500">Voice-Activated Unified Logic Terminal</p>
                </div>
                <button
                    onClick={toggleBrain}
                    className={cn(
                        "rounded border px-3 py-1 text-xs transition",
                        isLocalBrain
                            ? "border-emerald-500/60 text-emerald-300 hover:bg-emerald-500/10"
                            : "border-sky-500/60 text-sky-300 hover:bg-sky-500/10"
                    )}
                    title="切換本地/雲端大腦"
                >
                    <Cpu className="mr-1 inline h-3 w-3" />{brainLabel}
                </button>
            </header>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_1.4fr_1fr]">
                {/* Metrics */}
                <section className="rounded-lg border border-cyan-900/40 bg-slate-950/60 p-4">
                    <h2 className="mb-3 flex items-center gap-2 text-sm text-cyan-400"><Activity className="h-4 w-4" />METRICS</h2>
                    <ul className="space-y-2 text-xs">
                        <li className="flex justify-between">
                            <span className="text-slate-500">語音服務</span>
                            <span className={voiceOnline ? "text-emerald-400" : "text-rose-400"}>{voiceOnline ? "ONLINE" : "OFFLINE"}</span>
                        </li>
                        <li className="flex justify-between">
                            <span className="text-slate-500">大腦</span><span>{brainLabel}</span>
                        </li>
                        <li className="text-slate-500">本地模型（{models.length}）</li>
                        {models.map(m => (
                            <li key={m.name} className="truncate pl-2 text-slate-400">▸ {m.name}</li>
                        ))}
                    </ul>
                </section>

                {/* Voice 中央區 */}
                <section className="flex flex-col rounded-lg border border-cyan-700/40 bg-slate-950/80 p-4">
                    <h2 className="mb-2 text-center text-sm text-cyan-400">VOICE LINK</h2>
                    <div className="flex-1 space-y-2 overflow-y-auto py-2 text-sm" style={{ maxHeight: "40vh" }}>
                        {turns.length === 0 && (
                            <p className="pt-10 text-center text-xs text-slate-600">按住下方按鈕開始說話</p>
                        )}
                        {turns.map((t, i) => (
                            <p key={i} className={t.role === "user" ? "text-right text-sky-300" : "text-left text-slate-300"}>
                                {t.text}
                            </p>
                        ))}
                        {busy && <p className="animate-pulse text-center text-xs text-cyan-500">…思考中…</p>}
                    </div>
                    <div className="mt-4 flex justify-center">
                        <button
                            onMouseDown={startRecording}
                            onMouseUp={stopRecording}
                            onMouseLeave={() => recording && stopRecording()}
                            onTouchStart={startRecording}
                            onTouchEnd={stopRecording}
                            disabled={!voiceOnline || busy}
                            className={cn(
                                "flex h-24 w-24 items-center justify-center rounded-full border-2 transition-all select-none",
                                recording
                                    ? "scale-110 border-rose-400 bg-rose-500/20 shadow-[0_0_40px_rgba(244,63,94,0.4)]"
                                    : speaking
                                        ? "border-emerald-400 bg-emerald-500/10 shadow-[0_0_30px_rgba(52,211,153,0.3)]"
                                        : "border-cyan-500 bg-cyan-500/10 hover:shadow-[0_0_30px_rgba(34,211,238,0.35)]",
                                (!voiceOnline || busy) && "cursor-not-allowed opacity-40"
                            )}
                        >
                            <Mic className={cn("h-10 w-10", recording ? "text-rose-300" : "text-cyan-300")} />
                        </button>
                    </div>
                    <p className="mt-2 text-center text-[10px] text-slate-600">
                        {voiceOnline ? "按住說話・放開送出" : "voice-service 離線（執行 apps/voice-service/start-voice.bat）"}
                    </p>
                </section>

                {/* Skills + Schedule */}
                <div className="space-y-4">
                    <section className="rounded-lg border border-cyan-900/40 bg-slate-950/60 p-4">
                        <h2 className="mb-3 flex items-center gap-2 text-sm text-cyan-400"><Sparkles className="h-4 w-4" />SKILLS</h2>
                        <ul className="space-y-1 text-xs text-slate-400">
                            {skills.length === 0 && <li className="text-slate-600">（無資料）</li>}
                            {skills.slice(0, 8).map((s, i) => (
                                <li key={s.id || i} className="truncate">▸ {s.name || s.title || s.id}</li>
                            ))}
                        </ul>
                    </section>
                    <section className="rounded-lg border border-cyan-900/40 bg-slate-950/60 p-4">
                        <h2 className="mb-3 flex items-center gap-2 text-sm text-cyan-400"><CalendarDays className="h-4 w-4" />SCHEDULE</h2>
                        <ul className="space-y-1 text-xs text-slate-400">
                            {events.length === 0 && <li className="text-slate-600">（近期無排程）</li>}
                            {events.map(e => (
                                <li key={e.id} className="truncate">▸ {e.title || e.summary || "未命名"}{(e.start || e.date) ? ` — ${String(e.start || e.date).slice(0, 16)}` : ""}</li>
                            ))}
                        </ul>
                    </section>
                </div>
            </div>
        </div>
    );
}
```

- [ ] **Step 4: 型別/建置檢查**

Run: `cd C:/Users/User/Desktop/project-golem/web-dashboard && npx tsc --noEmit 2>&1 | head -30`
Expected: vault/page.tsx 無錯誤（既有檔案原本的錯誤不算）。若 `useGolem`/`apiGet` 型別簽名與 chat/page.tsx 實際用法不同，以 chat/page.tsx 的現行用法為準修正。

- [ ] **Step 5: Commit**

```bash
cd C:/Users/User/Desktop/project-golem && git add web-dashboard/src/app/dashboard/vault web-dashboard/src/app/dashboard/layout.tsx web-dashboard/src/lib/i18n/messages.ts && git commit -m "feat(vault): V.A.U.L.T. command center page with push-to-talk voice"
```

---

### Task 5: 端到端驗證（瀏覽器實測）

**Files:** 無新檔（驗證任務）

- [ ] **Step 1: 啟動三個服務**

1. Ollama 已在跑（tray）
2. `C:/Users/User/Desktop/project-golem/apps/voice-service/start-voice.bat`
3. golem dashboard：依 `package.json`，`npm run dev`（或使用者慣用的 Start-Golem.bat）

- [ ] **Step 2: smoke — 三端點**

```bash
curl -s http://127.0.0.1:8765/health
curl -s -X POST http://127.0.0.1:8765/tts -H "Content-Type: application/json" -d "{\"text\":\"系統上線\"}" -o probe.mp3 && ls -l probe.mp3
curl -s -X POST http://127.0.0.1:8765/stt -F "audio=@probe.mp3"
```
Expected: health ok:true；probe.mp3 > 5KB；stt 回 `{"text":"...系統上線..."}` 近似字樣

- [ ] **Step 3: 瀏覽器驗證（webapp-testing / playwright MCP）**

開 `http://localhost:3000/dashboard/vault`（port 依實際 dev server）確認：
1. 頁面載入、四區塊有資料（Metrics 顯示模型清單、語音服務 ONLINE）
2. 大腦切換按鈕點擊後 label 在 本地/雲端 間切換（測完切回原設定）
3. 打開 chat 頁確認原功能未壞
4. 麥克風流程需真人說話，請使用者實測按住說話一次

- [ ] **Step 4: 回報結果並附截圖**
