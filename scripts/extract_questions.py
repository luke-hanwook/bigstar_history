#!/usr/bin/env python3
"""Extract lesson questions and answer keys from the supplied study PDF."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pdfplumber


DEFAULT_SOURCE = Path.home() / "Downloads" / "최태성 한능검 심화 별채우기_전범위.pdf"
QUESTION_RE = re.compile(r"^(\d{1,2})[.]?\s+(.+)$")
MARKER_RE = re.compile(r"(?<!\d)(\d{2})(?!\d)")
USER_CONFIRMED_LABELS = {
    (9, 28): 27,
    (22, 7): 6,
    (23, 7): 6,
    (24, 19): 18,
    (31, 7): 6,
}


def course_for(title: str) -> str:
    if "선사" in title or "여러 나라" in title:
        return "선사와 여러 나라"
    if "고대" in title:
        return "삼국과 남북국"
    if "고려" in title:
        return "고려"
    if "조선 전기" in title:
        return "조선 전기"
    if "조선 후기" in title:
        return "조선 후기"
    if "조선" in title:
        return "조선 전기"
    if "개항기" in title or "국권 피탈" in title:
        return "개항기와 대한제국"
    if "일제 강점기" in title:
        return "일제 강점기"
    return "현대"


def question_lines(lines: list[str]) -> tuple[str, list[tuple[int, str]]]:
    title = lines[0].strip() if lines else "미분류"
    content = []
    for line in lines[1:]:
        if line.strip().startswith("정답"):
            break
        content.append(line.strip())

    questions: list[tuple[int, str]] = []
    for line in content:
        match = QUESTION_RE.match(line)
        if match:
            questions.append((int(match.group(1)), match.group(2).strip()))
        elif questions and line:
            number, previous = questions[-1]
            questions[-1] = (number, f"{previous} {line}".strip())
    return title, questions


def answer_body(lines: list[str]) -> str:
    for index, line in enumerate(lines):
        if line.strip().startswith("정답"):
            return " ".join([line.split(":", 1)[-1], *lines[index + 1 :]]).strip()
    return ""


def comma_parts(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def split_answer_value(value: str, prompt: str) -> list[str]:
    runs = [match.group(0) for match in re.finditer(r"☆+", prompt)]
    wanted = len(runs)
    comma_values = comma_parts(value)
    if len(comma_values) == wanted:
        return comma_values
    if wanted > 1 and "." in prompt:
        dotted = [part.strip() for part in value.split(".") if part.strip()]
        if len(dotted) == wanted:
            return dotted
    compact = re.sub(r"[\s,./·ㆍ()（）]", "", value)
    if wanted > 1 and len(compact) == sum(map(len, runs)):
        parts = []
        offset = 0
        for run in runs:
            parts.append(compact[offset : offset + len(run)])
            offset += len(run)
        return parts
    return comma_values or ([value.strip()] if value.strip() else [])


def group_count(text: str) -> int:
    return len(re.findall(r"☆+", text))


def align_answers(key: str, questions: list[tuple[int, str]]) -> tuple[list[str], list[str]]:
    """Align answer-key entries by printed number, tolerating a repeated label typo.

    The printed key occasionally repeats a question number. The sequential question
    position and number of comma-separated answers are used as a secondary signal.
    """
    markers = list(MARKER_RE.finditer(key))
    if not questions:
        return [], ["No questions found on this page."]

    # Dynamic programming chooses an ordered sequence of answer-key boundaries.
    # Matching the printed question number is preferred; the expected number of
    # answers for each prompt helps disambiguate numeric answer values.
    n = len(questions)
    neg = -10**9
    scores: list[dict[int, tuple[int, int | None]]] = [dict() for _ in range(n)]
    for j, marker in enumerate(markers):
        label = int(marker.group(1))
        expected = questions[0][0]
        if label in (expected, expected - 1):
            scores[0][j] = (10 if label == expected else 3, None)

    for i in range(1, n):
        expected = questions[i][0]
        desired_parts = group_count(questions[i - 1][1])
        for j, marker in enumerate(markers):
            label = int(marker.group(1))
            label_score = 10 if label == expected else (3 if label == questions[i - 1][0] else -8)
            if label_score < 0:
                continue
            for k, (prior_score, _) in scores[i - 1].items():
                if k >= j:
                    continue
                payload = key[markers[k].end() : marker.start()].strip()
                actual_parts = len(split_answer_value(payload, questions[i - 1][1]))
                part_score = 5 if actual_parts == desired_parts else -min(6, abs(actual_parts - desired_parts) * 2)
                candidate = prior_score + label_score + part_score
                current = scores[i].get(j)
                if current is None or candidate > current[0]:
                    scores[i][j] = (candidate, k)

    if not scores[-1]:
        return [""] * n, ["Could not align the answer key automatically."]

    # Score the final answer segment and backtrack the selected markers.
    best_j = max(
        scores[-1],
        key=lambda j: scores[-1][j][0]
        + (5 if len(split_answer_value(key[markers[j].end() :], questions[-1][1])) == group_count(questions[-1][1]) else -5),
    )
    chosen = [best_j]
    for i in range(n - 1, 0, -1):
        previous = scores[i][chosen[-1]][1]
        if previous is None:
            return [""] * n, ["Answer-key alignment is incomplete."]
        chosen.append(previous)
    chosen.reverse()

    aligned = []
    warnings = []
    for i, j in enumerate(chosen):
        start = markers[j].end()
        end = markers[chosen[i + 1]].start() if i + 1 < n else len(key)
        value = key[start:end].strip()
        aligned.append(value)
        expected_num = questions[i][0]
        marker_num = int(markers[j].group(1))
        if marker_num != expected_num:
            warnings.append(f"Printed answer number {marker_num:02d} aligned to question {expected_num:02d} (likely repeated/misprinted key number).")
        actual_parts = len(split_answer_value(value, questions[i][1]))
        if actual_parts != group_count(questions[i][1]):
            warnings.append(f"Question {expected_num:02d}: {group_count(questions[i][1])} blank groups but answer key has {actual_parts} parsed parts ({value!r}).")
    return aligned, warnings


def replace_stars(text: str, answers: list[str]) -> tuple[str, list[str]]:
    groups = iter(answers)
    warnings = []

    def substitute(_match: re.Match[str]) -> str:
        answer = next(groups, "").strip()
        return "{{" + answer + "}}"

    result = re.sub(r"☆+", substitute, text)
    leftovers = list(groups)
    if leftovers:
        warnings.append(f"{len(leftovers)} extra answer field(s) were not placed into the prompt.")
    if result.count("{{}}"):
        warnings.append("One or more star blanks have no extracted answer.")
    return result, warnings


def extract(source: Path) -> dict:
    lessons = []
    page_warnings = []
    reviewed_source_notes = []
    with pdfplumber.open(source) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            lines = (page.extract_text() or "").splitlines()
            title, raw_questions = question_lines(lines)
            raw_key = answer_body(lines)
            answer_values, alignment_warnings = align_answers(raw_key, raw_questions)
            reviewed_questions = {}
            for warning in alignment_warnings:
                match = re.match(r"Printed answer number (\d+) aligned to question (\d+) \(likely repeated/misprinted key number\)\.", warning)
                if match:
                    printed_number, question_number = map(int, match.groups())
                    expected_printed_number = USER_CONFIRMED_LABELS.get((page_number, question_number))
                    if expected_printed_number == printed_number:
                        q_index = next((i for i, (number, _) in enumerate(raw_questions) if number == question_number), None)
                        answer = answer_values[q_index] if q_index is not None else ""
                        question_id = f"p{page_number:02d}-q{q_index + 1:02d}" if q_index is not None else None
                        note = {
                            "page": page_number,
                            "questionId": question_id,
                            "questionNumber": question_number,
                            "printedAnswerNumber": printed_number,
                            "status": "user-confirmed",
                            "answers": split_answer_value(answer, raw_questions[q_index][1]) if q_index is not None else [],
                            "note": "원본 정답란의 번호 중복을 확인했고, 이 문항과 정답의 연결을 사용자와 대조했습니다.",
                        }
                        reviewed_source_notes.append(note)
                        if question_id:
                            reviewed_questions[q_index] = note
                        continue
                page_warnings.append(f"Page {page_number}: {warning}")
            questions = []
            for index, (printed_number, prompt) in enumerate(raw_questions):
                answer_text = answer_values[index] if index < len(answer_values) else ""
                answers = split_answer_value(answer_text, prompt)
                text, prompt_warnings = replace_stars(prompt, answers)
                questions.append(
                    {
                        "id": f"p{page_number:02d}-q{index + 1:02d}",
                        "number": printed_number,
                        "text": text,
                        "answers": answers,
                        "sourceText": prompt,
                        "answerKeyRaw": answer_text,
                        "explain": "제공된 자료에는 정답만 있어요. 관련 개념은 함께 공부한 교재에서 복습해 보세요.",
                        "sourcePage": page_number,
                        "warnings": prompt_warnings,
                        **({"review": reviewed_questions[index]} if index in reviewed_questions else {}),
                    }
                )
                if prompt_warnings:
                    page_warnings.extend(f"Page {page_number}, question {printed_number:02d}: {warning}" for warning in prompt_warnings)
            lessons.append(
                {
                    "id": f"lesson-{page_number:02d}",
                    "title": title,
                    "course": course_for(title),
                    "sourcePage": page_number,
                    "questions": questions,
                }
            )

    return {
        "schemaVersion": 1,
        "source": source.name,
        "sourcePages": len(lessons),
        "questionCount": sum(len(lesson["questions"]) for lesson in lessons),
        "lessons": lessons,
        "extractionWarnings": page_warnings,
        "reviewedSourceNotes": reviewed_source_notes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", nargs="?", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent.parent / 'data' / 'questions.json')
    args = parser.parse_args()
    data = extract(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {data['questionCount']} questions from {data['sourcePages']} pages to {args.output}")
    print(f"Warnings: {len(data['extractionWarnings'])}")
    for warning in data["extractionWarnings"][:40]:
        print(f"- {warning}")


if __name__ == "__main__":
    main()
