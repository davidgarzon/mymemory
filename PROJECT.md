PROJECT.md — Second Memory (Conversational Reminder + Vector Memory)

1) Goal

Build a personal “second memory” that captures notes/reminders by text or voice, links them to people + time, syncs with Google Calendar, and proactively reminds me before meetings about pending topics.

This is conversation-oriented memory, not a generic task manager.

Single-user system (me).

⸻

2) Core Use Cases

Capture
	•	“Apunta esta idea: …”
	•	“Recuérdame hablar con Toni sobre subidas salariales”
	•	“Recuérdame mañana a las 9 hablar con Sergio de X”
	•	“Cuando hable con Toni, acuérdame de X”

Pre-meeting briefing

If I have a meeting with a person, I receive a message 30 minutes before with pending topics to discuss.

Post-meeting update

“Ya he hablado con Toni de salarios”
→ mark that topic as discussed so it won’t appear again.

Deduplication / enrichment

If I say the same reminder multiple times with different wording, the system should detect it’s likely the same topic, avoid duplicates, and merge or enrich existing memory items.

⸻

3) Non-goals (NOT building now)
	•	Multi-user
	•	Web UI / complex mobile UI
	•	Collaboration
	•	Full CRM
	•	Complex task/project management
	•	Advanced analytics

⸻

4) Channels (MVP)

Input
	•	WhatsApp text
	•	WhatsApp audio (voice note → transcription)

Output
	•	WhatsApp messages (reminders + briefings)

⸻

5) Architecture (High Level)

Components:
	1.	API Backend (FastAPI)
	2.	Intent Parsing Service (LLM)
	3.	Memory Engine
	•	structured memory (Postgres)
	•	semantic memory (pgvector embeddings)
	4.	Calendar Sync Service (Google Calendar)
	5.	Reminder Scheduler (Celery + Redis)
	6.	WhatsApp Integration
	•	inbound webhook
	•	outbound message sender

⸻

6) Tech Stack (Locked)
	•	Python 3.11
	•	FastAPI
	•	PostgreSQL 15+
	•	pgvector extension
	•	Redis
	•	Celery
	•	SQLAlchemy (or SQLModel)
	•	Alembic migrations
	•	Docker + docker-compose
	•	LLM API (OpenAI or equivalent)
	•	Whisper (or equivalent) for speech-to-text
	•	Google Calendar API
	•	WhatsApp Cloud API (Meta) OR Twilio (adapter pattern)

⸻

7) Data Model (Source of Truth = Postgres)

7.1 Person

Represents a real person I talk to.

Fields:
	•	id (uuid)
	•	display_name (string)
	•	aliases (array of strings)
	•	created_at

7.2 MemoryItem

Represents a note/reminder/idea.

Fields:
	•	id (uuid)
	•	type (idea, reminder, note)
	•	content (text)
	•	normalized_summary (text, optional)
	•	related_person_id (nullable FK → Person)
	•	due_at (nullable datetime)
	•	status (pending, discussed, archived)
	•	created_at
	•	updated_at

7.3 CalendarEvent

Events synced from Google Calendar.

Fields:
	•	id (uuid)
	•	provider (google)
	•	provider_event_id (string)
	•	title (string)
	•	start_time (datetime)
	•	end_time (datetime)
	•	attendees_raw (json)
	•	related_person_id (nullable FK → Person)
	•	created_at
	•	updated_at

7.4 InteractionLog

Tracks reminders/updates.

Fields:
	•	id (uuid)
	•	memory_item_id (FK)
	•	calendar_event_id (nullable FK)
	•	action (created, reminded, discussed, postponed, merged)
	•	metadata (json)
	•	created_at

⸻

8) Semantic Memory (Vector Memory)

8.1 Why

Postgres stores exact text and cannot detect semantic duplicates.
Vector memory enables:
	•	semantic duplicate detection
	•	context retrieval (“this thing I said before…”)
	•	enrichment/merging

8.2 Implementation

Use pgvector inside PostgreSQL.

Preferred approach: memory_item_embeddings table with:
	•	id (uuid)
	•	memory_item_id (FK)
	•	embedding (vector)
	•	embedding_model (string)
	•	created_at

8.3 Embedding policy

Vectorize:
	•	MemoryItem.content
	•	optionally MemoryItem.normalized_summary

Do NOT vectorize:
	•	raw logs
	•	calendar events

8.4 Retrieval flow

Before creating a new MemoryItem:
	1.	compute embedding
	2.	search top K similar existing items (same person if available)
	3.	if similarity above threshold:
	•	merge/enrich existing MemoryItem
	•	log action merged
	4.	else:
	•	create new MemoryItem

8.5 LLM context injection rule

The LLM has no memory.
The system must retrieve relevant memories via vector search and pass them explicitly as context.

⸻

9) Intent Parsing Contract (LLM)

The parser must return valid JSON with:
	•	intent: create_memory_item OR mark_discussed OR list_pending OR unknown
	•	memory_item:
	•	type: idea OR reminder OR note
	•	content: string
	•	related_person_name: string or null
	•	due_at_iso: ISO string or null
	•	confidence: float 0.0–1.0
	•	notes: string

Rules:
	•	If time is implicit (“cuando hable con Toni”), set due_at_iso = null and set person.
	•	If person is unclear, keep it null.
	•	Never invent people.
	•	Prefer unknown when unsure.

⸻

10) Calendar Linking Logic

If a MemoryItem has:
	•	related_person_id not null
	•	due_at is null

Then:
	•	search upcoming CalendarEvents with that person
	•	link reminder to the closest upcoming event
	•	schedule reminder at event.start_time minus 30 minutes

If no event exists:
	•	keep it pending without schedule

⸻

11) Reminder Scheduling

A reminder is sent when:
	•	time matches scheduled trigger
	•	MemoryItem.status is pending

Reminder message must include:
	•	person name
	•	bullet list of pending topics (short)

⸻

12) WhatsApp Message Format (Output)

Pre-meeting briefing:
Reunión con [Person] en 30 min
Pendiente hablar:
	•	Topic 1
	•	Topic 2

Single reminder:
Recordatorio
Tienes pendiente hablar con [Person] sobre:
	•	Topic

⸻

13) Repository Structure

Root:
	•	PROJECT.md
	•	docker-compose.yml

App:
	•	app/main.py
	•	app/core/config.py
	•	app/core/db.py
	•	app/api/routes_whatsapp.py
	•	app/api/routes_memory.py
	•	app/models/
	•	app/services/intent_parser.py
	•	app/services/memory_engine.py
	•	app/services/vector_store.py
	•	app/services/calendar_service.py
	•	app/services/reminder_service.py
	•	app/workers/celery_app.py
	•	app/workers/tasks.py
	•	app/migrations/

⸻

14) Milestone Plan (MVP)

Milestone 1:
	•	FastAPI running
	•	Postgres connected
	•	Create MemoryItem via API (text)
	•	List pending items

Milestone 2:
	•	pgvector embeddings
	•	semantic deduplication
	•	retrieve context for parsing

Milestone 3:
	•	Google Calendar sync
	•	meeting linking
	•	reminder scheduling

Milestone 4:
	•	WhatsApp webhook + outbound messages
	•	audio transcription pipeline

⸻

15) Rules for Cursor / AI Coding
	•	Do not add features not listed here.
	•	Prefer minimal working code over perfect architecture.
	•	Keep everything testable and observable.
	•	No refactors without explanation.
	•	Always implement DB migrations for schema changes.
	•	Do not introduce new dependencies without asking.
	•	Persist important LLM outputs.
	•	All LLM calls must be wrapped behind a service interface.