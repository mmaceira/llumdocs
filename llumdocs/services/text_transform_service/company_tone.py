from __future__ import annotations

from typing import Literal

from .common import _call_llm, _validate_text

# Tone type definitions
SERIOUS_IMPORTANT = "serious_important"
CALM_PROFESSIONAL = "calm_professional"

# Supported languages for company tone
SUPPORTED_LANGUAGES = {
    "ca": "Catalan",
    "es": "Spanish",
    "en": "English",
}

CompanyToneLanguage = Literal["ca", "es", "en"]


def apply_company_tone(
    text: str,
    *,
    tone_type: str,
    language: CompanyToneLanguage = "en",
    model_hint: str | None = None,
) -> str:
    """
    Generate a complete, valid email ready to send to a customer with a tone aligned
    with company communication standards.

    Args:
        text: The text content to transform into an email
        tone_type: One of 'serious_important' or 'calm_professional'
        language: Language code for the email (ca/es/en). Defaults to 'en'
        model_hint: Optional model identifier

    Returns:
        A complete email with subject, greeting, body, closing, and signature
        in the specified language
    """
    _validate_text(text)

    # Validate language
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Invalid language: {language}. Must be one of {list(SUPPORTED_LANGUAGES.keys())}"
        )

    language_label = SUPPORTED_LANGUAGES[language]

    if tone_type == SERIOUS_IMPORTANT:
        tone_description = "serious and important"
        constraints = [
            "Use a formal, authoritative tone appropriate for important business communications.",
            "Maintain professionalism and gravitas throughout.",
            "Ensure the message conveys importance and seriousness.",
            "Do not change the original meaning or introduce new information.",
            "Preserve critical data, quantities, and references.",
        ]
        system_prompt = (
            f"You are an expert business writer specializing in formal, "
            f"important company communications in {language_label}. "
            f"Generate complete, professional emails ready to send to customers "
            f"with a serious, authoritative tone. "
            f"The email must be written entirely in {language_label}."
        )
    elif tone_type == CALM_PROFESSIONAL:
        tone_description = "calm, professional but casual"
        constraints = [
            "Use a warm, approachable tone that remains professional.",
            "Balance professionalism with a friendly, calm demeanor.",
            "Avoid overly formal language while maintaining business appropriateness.",
            "Do not change the original meaning or introduce new information.",
            "Preserve critical data, quantities, and references.",
        ]
        system_prompt = (
            f"You are an expert business writer specializing in professional "
            f"yet approachable company communications in {language_label}. "
            f"Generate complete, professional emails ready to send to customers "
            f"with a calm, friendly tone. "
            f"The email must be written entirely in {language_label}."
        )
    else:
        raise ValueError(
            f"Invalid tone_type: {tone_type}. "
            f"Must be one of '{SERIOUS_IMPORTANT}' or '{CALM_PROFESSIONAL}'"
        )

    user_prompt = (
        f"Generate a complete, valid email ready to send to a customer "
        f"based on the following content. "
        f"The email must be written entirely in {language_label} and should have "
        f"a {tone_description} tone suitable for company communications.\n\n"
        f"The email must include:\n"
        f"- A clear and appropriate subject line in {language_label}\n"
        f"- A professional greeting appropriate for {language_label} "
        f"(e.g., 'Dear [Customer]' or 'Hello [Customer]')\n"
        f"- A well-structured body that incorporates all the information "
        f"from the input text\n"
        f"- A professional closing appropriate for {language_label} "
        f"(e.g., 'Best regards', 'Sincerely')\n"
        f"- A signature placeholder (e.g., '[Your Name]' or '[Company Name]')\n\n"
        "Constraints:\n" + "\n".join(f"- {item}" for item in constraints) + "\n\n"
        f"Language: {language_label}\n"
        "Input content:\n"
        f"{text.strip()}\n\n"
        f"Generate the complete email in {language_label} now:"
    )

    return _call_llm(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model_hint=model_hint,
    )
