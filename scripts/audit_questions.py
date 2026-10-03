#!/usr/bin/env python3
"""Run structural checks; historical correctness still needs PDF comparison."""
from __future__ import annotations
import argparse
import json
import re
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
DEFAULT_DATA=ROOT/"data"/"questions.json"
PLACEHOLDER=re.compile(r"\{\{(.*?)\}\}")
STAR_GROUP=re.compile(r"☆+")

def audit(data):
    issues=[]
    lessons=data.get("lessons")
    if not isinstance(lessons,list):
        return {"summary":{"lessonCount":0,"questionCount":0,"errors":1,"warnings":0},
                "issues":[{"severity":"error","code":"lessons-not-list","message":"lessons must be an array"}]}
    count=sum(len(l.get("questions",[])) for l in lessons if isinstance(l,dict))
    def add(severity,code,lesson,question,message):
        issues.append({"severity":severity,"code":code,"lessonId":lesson.get("id"),
            "lessonTitle":lesson.get("title"),"questionId":question.get("id") if question else None,
            "questionNumber":question.get("number") if question else None,
            "sourcePage":(question or {}).get("sourcePage",lesson.get("sourcePage")),"message":message})
    if data.get("questionCount",count)!=count:
        issues.append({"severity":"error","code":"question-count-mismatch","message":f"metadata says {data.get('questionCount')}; found {count}"})
    ids=Counter()
    lesson_ids=Counter()
    for lesson in lessons:
        lesson_ids[lesson.get("id","")]+=1
        page=lesson.get("sourcePage")
        if not isinstance(page,int) or not 1<=page<=data.get("sourcePages",0):
            add("error","invalid-lesson-page",lesson,None,f"invalid lesson page: {page!r}")
        numbers=Counter()
        for q in lesson.get("questions",[]):
            qid=str(q.get("id","")); ids[qid]+=1
            number=str(q.get("number","")); numbers[number]+=1
            text=q.get("text") if isinstance(q.get("text"),str) else ""
            answers=q.get("answers") if isinstance(q.get("answers"),list) else []
            source=q.get("sourceText") if isinstance(q.get("sourceText"),str) else ""
            qpage=q.get("sourcePage",page)
            if not qid: add("error","missing-id",lesson,q,"empty question id")
            if not text.strip(): add("error","empty-text",lesson,q,"empty question text")
            if not isinstance(qpage,int) or not 1<=qpage<=data.get("sourcePages",0):
                add("error","invalid-question-page",lesson,q,f"invalid source page: {qpage!r}")
            if not source.strip(): add("warning","missing-source-text",lesson,q,"empty sourceText")
            slots=PLACEHOLDER.findall(text)
            if not slots: add("warning","no-answer-slot",lesson,q,"no {{answer}} placeholder")
            if len(slots)!=len(answers):
                add("error","slot-answer-count",lesson,q,f"{len(slots)} placeholders but {len(answers)} answers")
            elif any(s.strip()!=str(a).strip() for s,a in zip(slots,answers)):
                add("error","slot-answer-mismatch",lesson,q,"placeholder labels differ from answers")
            if any(not str(a).strip() for a in answers): add("error","empty-answer",lesson,q,"empty answer value")
            star_slots=STAR_GROUP.findall(source)
            if source and len(star_slots)!=len(answers):
                add("warning","source-slot-count",lesson,q,f"{len(star_slots)} star groups but {len(answers)} answers")
            if source and slots and len(slots)==len(answers):
                rebuilt=PLACEHOLDER.sub(lambda m:"☆"*len(m.group(1).strip()),text)
                if rebuilt!=source: add("warning","source-text-differs",lesson,q,"answer placeholders do not reconstruct sourceText exactly")
            for warning in q.get("warnings",[]): add("warning","extraction-warning",lesson,q,str(warning))
        for number,n in numbers.items():
            if n>1: add("warning","duplicate-question-number",lesson,None,f"question {number!r} appears {n} times")
    for value,n in lesson_ids.items():
        if value and n>1: issues.append({"severity":"error","code":"duplicate-lesson-id","lessonId":value,"message":f"lesson id appears {n} times"})
    for value,n in ids.items():
        if value and n>1: issues.append({"severity":"error","code":"duplicate-question-id","questionId":value,"message":f"question id appears {n} times"})
    tally=Counter(i["severity"] for i in issues)
    return {"summary":{"lessonCount":len(lessons),"questionCount":count,"expectedQuestionCount":data.get("questionCount"),
        "issueCount":len(issues),"errors":tally["error"],"warnings":tally["warning"],
        "extractionWarningCount":len(data.get("extractionWarnings",[])),
        "note":"Structural checks do not verify historical correctness against the PDF."},"issues":issues}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data",nargs="?",type=Path,default=DEFAULT_DATA)
    parser.add_argument("--output",type=Path,help="also write JSON report to this path")
    args=parser.parse_args()
    result=audit(json.loads(args.data.read_text(encoding="utf-8")))
    s=result["summary"]
    print(f"Lessons: {s['lessonCount']} | Questions: {s['questionCount']}")
    print(f"Structural errors: {s['errors']} | Warnings: {s['warnings']}")
    print(s["note"])
    for i in result["issues"]:
        where="/".join(str(i.get(k)) for k in ("lessonId","questionId") if i.get(k)) or "dataset"
        page=f" (PDF p. {i['sourcePage']})" if i.get("sourcePage") else ""
        print(f"[{i['severity']}] {where}{page}: {i['message']}")
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(f"Report saved to {args.output}")
if __name__=="__main__": main()
