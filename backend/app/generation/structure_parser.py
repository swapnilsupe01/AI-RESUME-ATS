"""
Sentence Structure Parser using spaCy.

Distinguishes compound predicates from 3+ item lists/series to eliminate
ungrammatical commas before coordinating conjunctions ('and', 'or') without
affecting series/lists or independent clauses.
"""

import re
import logging
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

# Cached spaCy NLP instance
_nlp = None


def get_spacy_nlp():
    """
    Lazy-load spaCy English NLP model.
    Attempts 'en_core_web_sm', falls back to blank 'en' if not downloaded.
    """
    global _nlp
    if _nlp is not None:
        return _nlp

    try:
        import spacy
        try:
            _nlp = spacy.load("en_core_web_sm")
            logger.debug("[spaCy] Loaded 'en_core_web_sm' successfully.")
        except Exception:
            # Fall back to blank model with sentencizer if full pipeline isn't installed
            _nlp = spacy.blank("en")
            if "sentencizer" not in _nlp.pipe_names:
                _nlp.add_pipe("sentencizer")
            logger.debug("[spaCy] Loaded blank 'en' pipeline fallback.")
    except ImportError:
        logger.warning("[spaCy] spaCy is not installed. Sentence structure analysis will use heuristic fallback.")
        _nlp = False

    return _nlp


def is_spacy_available() -> bool:
    """Return True if a functional spaCy NLP pipeline is available."""
    nlp = get_spacy_nlp()
    return nlp is not None and nlp is not False


def clean_compound_predicate_commas_spacy(text: str) -> str:
    """
    Uses spaCy syntactic dependency analysis to remove ungrammatical commas before
    coordinating conjunctions ('and', 'or') in compound predicates (two verbs sharing
    the same subject), while strictly preserving:
      1. Lists of 3 or more elements (e.g. 'analytics, reporting, and monitoring')
      2. Independent clauses with explicit subjects (e.g. 'The API processed ..., and the team deployed ...')
      3. Introductory dependent clauses / participial openers
    """
    if not text or (", and " not in text and ", or " not in text and "both " not in text.lower()):
        return text

    # Quick cleanup: ungrammatical comma in correlative 'both ... and'
    cleaned = re.sub(r'\bboth\s+([^,]+?),\s+and\s+', r'both \1 and ', text, flags=re.IGNORECASE)
    cleaned = re.sub(r',\s+and\s+both\b', ' and both', cleaned, flags=re.IGNORECASE)

    if ", and " not in cleaned and ", or " not in cleaned:
        return cleaned

    nlp = get_spacy_nlp()
    if nlp is False or nlp is None or not hasattr(nlp, "pipe_names") or "parser" not in nlp.pipe_names:
        # Graceful heuristic fallback if full spaCy model with dependency parser is unavailable
        return _fallback_fix_unnecessary_commas(cleaned)

    try:
        doc = nlp(cleaned)
        chars_to_remove = set()

        for token in doc:
            # Check for coordinating conjunctions 'and' / 'or'
            if token.text.lower() in ("and", "or") and token.pos_ in ("CCONJ", "CC"):
                # Find preceding token (must be comma)
                prev_token = token.nbor(-1) if token.i > 0 else None
                if not prev_token or prev_token.text != ",":
                    continue

                comma_char_idx = prev_token.idx

                # Check head relationship
                head = token.head
                # In spaCy dependency trees, conjunctions link conjuncts (dep == 'conj')
                # If head is a verb or token coordinate is a verb
                conjuncts = [c for c in head.conjuncts]

                # 1. Check if this is a series/list of 3 or more coordinate items
                # e.g., head has multiple conjuncts, or total items in the conj chain >= 2
                if len(conjuncts) >= 2:
                    # 3+ items (head + 2 conjuncts = 3 items). This is a series/list.
                    # Do NOT remove comma.
                    continue

                # Also check comma counts before this conjunction in the same clause/phrase
                # If there are preceding commas separating items of the same category, it's a list.
                preceding_commas = [t for t in doc[:prev_token.i] if t.text == ","]
                if preceding_commas:
                    # Check if the preceding commas are separating parallel list items
                    last_preceding_comma = preceding_commas[-1]
                    # If there are multiple commas separating short parallel chunks, it's likely a list
                    between_commas = doc[last_preceding_comma.i + 1: prev_token.i].text.strip()
                    if len(between_commas.split()) <= 4 and not any(t.dep_ == "ROOT" for t in doc[last_preceding_comma.i + 1: prev_token.i]):
                        # Parallel list element (e.g. "A, B, and C")
                        # Do NOT remove comma.
                        continue

                # 2. Check if the conjunction joins an independent clause with its own subject
                # Look at the tokens following the conjunction for an explicit subject (nsubj)
                tokens_after = [t for t in doc[token.i + 1: token.i + 8]]
                has_explicit_subject = any(t.dep_ in ("nsubj", "nsubjpass") for t in tokens_after)
                if has_explicit_subject:
                    # Independent clause with distinct subject: comma is grammatically allowed.
                    continue

                # 3. Check for compound predicate:
                # The conjunction joins two verbs (either head is VERB and coordinate is VERB, or resume bullet action verbs)
                is_verb_coord = (head.pos_ == "VERB") or any(c.pos_ == "VERB" for c in conjuncts)
                # In resume bullets, often starts with past tense action verb (ROOT)
                # e.g. "Implemented ... using Docker, and deployed ..."
                # 'deployed' is conj of 'Implemented'
                if is_verb_coord:
                    # Compound predicate: two verbs sharing subject. Remove the unneeded comma.
                    chars_to_remove.add(comma_char_idx)
                elif any(t.pos_ == "VERB" for t in tokens_after[:2]):
                    # If directly followed by a verb (e.g. "and deployed"), it's a compound predicate
                    chars_to_remove.add(comma_char_idx)

        if not chars_to_remove:
            return cleaned

        # Reconstruct string without the flagged comma characters
        result = []
        for idx, char in enumerate(cleaned):
            if idx in chars_to_remove:
                continue
            result.append(char)
        
        # Clean up any potential double spaces created
        return re.sub(r'\s{2,}', ' ', "".join(result))

    except Exception as e:
        logger.warning("[spaCy] Dependency parse error: %s. Using heuristic fallback.", e)
        return _fallback_fix_unnecessary_commas(cleaned)


def _fallback_fix_unnecessary_commas(text: str) -> str:
    """
    Heuristic rule-based fallback when spaCy parsing is not active.
    Distinguishes 2-verb compound predicates from 3-item lists and independent clauses.
    """
    if ", and " not in text and ", or " not in text:
        return text

    common_verbs = {
        "deployed", "engineered", "built", "designed", "created", "developed",
        "implemented", "configured", "optimized", "integrated", "architected",
        "managed", "maintained", "automated", "spearheaded", "directed",
        "led", "reduced", "increased", "accelerated", "conducted", "provided",
        "established", "orchestrated", "collaborated", "authored", "resolved"
    }

    pattern = re.compile(r',\s+(and|or)\s+', re.IGNORECASE)

    def replacer(match: re.Match) -> str:
        conjunction = match.group(1)
        start_pos = match.start()
        end_pos = match.end()

        prefix = text[:start_pos]
        suffix = text[end_pos:]

        words_after = re.findall(r'[a-zA-Z0-9_\-\.]+', suffix)
        if not words_after:
            return match.group(0)

        first_word_after = words_after[0].lower()
        second_word_after = words_after[1].lower() if len(words_after) > 1 else ""

        target_verb = first_word_after
        if first_word_after.endswith("ly") and second_word_after:
            target_verb = second_word_after

        is_verb_phrase = target_verb in common_verbs or target_verb.endswith("ed")

        preceding_comma_idx = prefix.rfind(',')

        if preceding_comma_idx == -1:
            # Only ONE comma before 'and' -> cannot be a 3-item list (A, B, and C requires 2 commas)
            if is_verb_phrase:
                return f" {conjunction} "
            return match.group(0)
        else:
            item2 = prefix[preceding_comma_idx + 1:].strip()
            item2_words = re.findall(r'[a-zA-Z0-9_\-\.]+', item2)

            item1 = prefix[:preceding_comma_idx].strip()
            item1_words = re.findall(r'[a-zA-Z0-9_\-\.]+', item1)

            intro_starters = {"using", "by", "with", "through", "via", "after", "while", "for", "as"}
            first_word_item1 = item1_words[0].lower() if item1_words else ""
            first_word_item2 = item2_words[0].lower() if item2_words else ""

            # Introductory clause e.g. "Using Docker and Nginx, containerized ..., and deployed ..."
            if first_word_item1 in intro_starters and first_word_item2 not in intro_starters:
                if is_verb_phrase and (first_word_item2 in common_verbs or first_word_item2.endswith("ed")):
                    return f" {conjunction} "

            # 3-verb list check: if item2 also starts with an action verb, it's a 3+ item list of verbs!
            if is_verb_phrase:
                if first_word_item2 in common_verbs or first_word_item2.endswith("ed"):
                    # 3-item list: preserve
                    return match.group(0)
                else:
                    return f" {conjunction} "
            else:
                # Noun or phrase list: preserve
                return match.group(0)

    return pattern.sub(replacer, text)
