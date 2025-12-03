## Running LlumDocs in different environments

This document gives a high‑level view of how LlumDocs can be run in containerised (Docker‑based) environments.
It is intended for people who decide **where** LlumDocs runs, not for those building or modifying its internals.

LlumDocs can be:

- run on a single machine for a small team,
- deployed on a server for a department or organisation,
- or integrated into existing platforms that already use containers.

---

### What Docker adds on top of the base product

When LlumDocs is packaged and run with Docker:

- The web interface, API, and supporting components are started together in a predictable way.
- The environment is consistent across machines, which makes behaviour more repeatable.
- Optional components (such as local language models or GPU acceleration) can be turned on or off depending on the host infrastructure.

From an end‑user point of view, the experience is the same:
you open a URL provided by your organisation and use the features described elsewhere in the documentation.

---

### Typical deployment patterns

- **Local or pilot environment**
  - Used for evaluation, prototyping, or small teams.
  - Usually runs on a single machine using containers.
  - Users access LlumDocs through a browser on `http://localhost` or an internal address.

- **Shared internal service**
  - Used by many users across a department or organisation.
  - Runs on a dedicated server or cluster managed by IT or platform teams.
  - Users access LlumDocs through an internal URL or via integrations in other tools.

- **Hybrid setups**
  - Some parts (for example, local language models) may run close to the data, while other parts (such as the user interface) are exposed more broadly.
  - This allows organisations to balance performance, cost, and data‑location requirements.

For all of these, the responsibility for configuring and operating the containers sits with your infrastructure or platform owner.

---

### CPU and GPU considerations

LlumDocs works on standard CPU‑only machines. In addition, some environments may:

- enable **GPU acceleration** to speed up heavier AI workloads,
- or combine CPU and GPU resources to support more concurrent users.

As an end user, you do not need to choose between CPU and GPU directly; you simply use LlumDocs as usual.
If performance is critical for your use case, your IT or platform team can decide whether GPU support is appropriate.

For more background on GPU‑enabled environments, see `docker/SETUP_GPU.md`.

---

### What administrators should decide

If you are responsible for offering LlumDocs to others, you will typically decide:

- where it runs (local machine, shared server, or existing container platform),
- how users authenticate and reach it (URL, network access, single sign‑on),
- which features are available (for example, whether to enable email intelligence or certain document types),
- whether to use CPU‑only or add GPU acceleration,
- and how to monitor and update the service over time.

The rest of this repository’s documentation focuses on what users can do once LlumDocs is available.
For environment‑specific instructions, follow your organisation’s internal platform and security guidelines.
