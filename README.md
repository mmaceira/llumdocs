# LlumDocs — Intelligent document assistant for everyday work

LlumDocs helps you understand and work with documents, emails, and images in your daily workflow.
You can use it through a web interface or connect to it from other tools through a simple HTTP API.

![LlumDocs interface](docs/images/document_summary.png)

---

## Getting started

### Quick start

1. **Get access**: Contact your IT team, data team, or project owner to get the LlumDocs URL and any login credentials.
2. **Open LlumDocs**: Navigate to the provided URL in your browser and sign in if required.
3. **Choose a feature**: Use the tabs to access translation, summaries, document extraction, image description, text transformation, or email intelligence.
4. **Try your first task**: Paste some text, upload a document, or paste an email to see how LlumDocs works.

For detailed getting-started guidance, see [`docs/INSTALL.md`](docs/INSTALL.md).

---

## What LlumDocs does

LlumDocs focuses on a few core capabilities:

- **Understand documents**: extract key facts, surface important details, and generate clear summaries.
- **Work across languages**: translate and rewrite text between Catalan, Spanish, and English.
- **Make text clearer**: simplify or make content more technical, or adapt it to a professional company tone.
- **Describe images**: generate natural-language descriptions of pictures and scanned content.
- **Review emails**: analyse emails for routing, phishing risk, and sentiment.

You can use any of these capabilities on their own or combine them in your own workflows.

---

## Main features

- **Text translation**: Translate between Catalan, Spanish, and English with automatic language detection.
- **Document summaries**: Generate short, detailed, or executive summaries from long documents.
- **Keyword extraction**: Identify key terms and concepts for tagging and quick scanning.
- **Text transformation**: Rewrite text in plain language, technical tone, or company tone.
- **Document extraction**: Extract structured data from delivery notes, bank statements, and payroll documents.
- **Image description**: Generate captions and descriptions for photos, scanned pages, and screenshots.
- **Email intelligence**: Route emails, detect phishing risk, and analyse sentiment.

For detailed feature descriptions and use cases, see [`docs/LLM_FEATURE_SPECS.md`](docs/LLM_FEATURE_SPECS.md).
For a visual tour of the interface, see [`docs/GUI_SCREENSHOTS.md`](docs/GUI_SCREENSHOTS.md).

---

## How to access LlumDocs

LlumDocs can be accessed in different ways depending on how your organisation has set it up:

- **Web interface**: Open the LlumDocs URL in your browser and use the tabs for different features.
- **Embedded in other tools**: Look for LlumDocs buttons or panels in your ticketing system, CRM, or other internal tools.
- **HTTP API**: Integrate LlumDocs capabilities into your own applications or automated workflows.

For detailed access instructions and setup guidance, see [`docs/INSTALL.md`](docs/INSTALL.md).
For information on how LlumDocs fits into different environments, see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Typical workflows

- **Preparing a client‑facing summary**
  - Upload or paste a contract, report, or specification.
  - Generate an executive summary and extract keywords.
  - Rewrite the summary in plain language or company tone and paste it into your email or document template.

- **Processing back‑office documents**
  - Upload a batch of delivery notes, bank statements, or payroll documents one by one.
  - Review the extracted fields and export them to your preferred system.
  - Use summaries and keywords to quickly understand unusual cases.

- **Working in multiple languages**
  - Draft content in your preferred language.
  - Translate it into the target language while preserving tone.
  - Optionally simplify or make the text more technical before sending.

- **Reviewing a suspicious or sensitive email**
  - Paste the message into the email intelligence view.
  - Check the suggested routing, phishing risk, and sentiment.
  - Decide how to respond or where to escalate the case.

---

## Documentation

- **[Getting started](docs/INSTALL.md)**: How to access and start using LlumDocs in your organisation.
- **[Feature guide](docs/LLM_FEATURE_SPECS.md)**: Detailed descriptions of each capability with use cases and examples.
- **[Interface tour](docs/GUI_SCREENSHOTS.md)**: Visual overview of the main screens and how they work.
- **[How LlumDocs helps you](docs/LLM_GUIDE_GLOBAL.md)**: Scenarios by role and tips for effective use.
- **[Practical tips](docs/LLM_DEVELOPMENT_GUIDE.md)**: Best practices for getting the most value from LlumDocs.
- **[Environment overview](docs/ARCHITECTURE.md)**: How LlumDocs fits into web apps, embedded tools, and automated workflows.
- **[Reliability and quality](docs/TESTING.md)**: What to expect from LlumDocs and how to report issues.

For administrators and platform teams:
- **[Docker deployment](docker/README.md)**: Running LlumDocs in containerised environments.
- **[GPU environments](docker/SETUP_GPU.md)**: Understanding GPU-enabled deployments.
