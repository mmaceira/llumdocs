## How LlumDocs fits into your environment

This document gives a high‑level view of how you can expect to use LlumDocs in your day‑to‑day work, without going into technical details about how it is built.

At a glance, LlumDocs usually appears in three places:

- as a **web application** you open in your browser,
- as **capabilities embedded** in the tools you already use,
- and as **automated processes** that handle documents and emails for you in the background.

---

### Web application: your main workspace

When LlumDocs is available as a web app:

- You open it in your browser through a link provided by your organisation.
- The home screen presents several tabs or sections:
  - Translation
  - Text transformation
  - Document summaries and extraction
  - Image description
  - Email intelligence
- Each tab focuses on a single type of task and guides you with:
  - a short explanation of what it does,
  - input areas (text boxes or file uploads),
  - and a main action button.

You can move freely between tabs. For example, you might:

- summarise a long report,
- then translate the summary,
- and finally rewrite the result in your company’s preferred tone.

---

### Embedded features in your existing tools

LlumDocs is often connected to other systems within your organisation so that you can use its capabilities without leaving your usual workflow.

Depending on how it is configured, you might see:

- a “Translate” or “Summarise” action next to documents, tickets, or records,
- a “Generate reply” or “Rewrite” option inside your email or support tool,
- an “Analyse with LlumDocs” option for uploaded files.

From your perspective:

- You stay inside the application you already know.
- LlumDocs quietly performs tasks such as translation, summarisation, or email analysis.
- The results are shown directly in that application (for example, as text you can insert or as a side‑panel with insights).

If you are not sure where LlumDocs is available, ask your internal administrator which tools have been connected.

---

### Automated document and email workflows

In some organisations, LlumDocs runs in the background as part of larger workflows. For example:

- Incoming documents (such as delivery notes or bank statements) may be processed automatically to extract key fields for finance systems.
- New emails in a shared inbox may be analysed so they can be routed to the right team, checked for phishing risk, or tagged with sentiment.
- Long reports or meeting notes may be summarised automatically and attached to records in your project or case‑management system.

In these cases, you might not interact with LlumDocs directly, but you will see its results:

- pre‑filled fields in forms or records,
- automatic tags, labels, or categories,
- and short summaries or highlights attached to items.

If you want to understand which automated processes involve LlumDocs, your internal contact can point you to the relevant workflows.

---

### How LlumDocs communicates with other systems

Without going into implementation details, it can be useful to know that:

- LlumDocs can be accessed both by humans (through a browser) and by other systems (through simple HTTP calls).
- The same capabilities you see in the interface—translation, summaries, text rewrites, image description, document extraction, and email intelligence—can also be triggered programmatically.
- This allows your organisation to:
  - give you an interactive workspace for ad‑hoc tasks,
  - and also automate repetitive flows where LlumDocs’ strengths add the most value.

If you are designing business processes, you can treat LlumDocs as a “document and language assistant” that:

- receives text, documents, images, or emails,
- returns translations, summaries, descriptions, extractions, or insights,
- and plugs these directly into your existing tools and records.

---

### Finding your way around the documentation

- For a tour of what each feature does, see `docs/LLM_FEATURE_SPECS.md`.
- For a visual overview of the main screens, see `docs/GUI_SCREENSHOTS.md`.
- For user‑centric guidance on access and usage, see `docs/INSTALL.md` and the root `README.md`.
