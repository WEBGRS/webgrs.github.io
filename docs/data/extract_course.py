# Pull the aggregates the uw-course-lookup figure draws out of that project's local insights file.
#   python docs/data/extract_course.py [path/to/insights.json]
# The file is built by uw-course-lookup/scripts/analyze.py and is gitignored there. This keeps only
# course codes and GPA figures: no instructor names, no mention counts.
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent.parent.parent / "uw-course-lookup" / "data" / "insights.json"
d = json.loads(SRC.read_text(encoding="utf-8"))
trend = d["campus_trend"]
out = {
    "courses": d["counts"]["courses"],
    "graded_students": d["counts"]["graded_students"],
    # Same course, different instructor: the spread between the most and least generous instructor
    "spread": [{"code": x["code"], "mean": x["gpa"], "low": x["low"]["gpa"], "high": x["high"]["gpa"], "spread": x["spread"]}
               for x in d["instructor_spread"]],
    "correlations": {k: v for k, v in d["correlations"].items() if k in ("mentions_vs_gpa", "reddit_tone_vs_gpa")},
    "campus": {"first": {"label": trend[0]["label"], "gpa": trend[0]["gpa"]}, "last": {"label": trend[-1]["label"], "gpa": trend[-1]["gpa"]}},
}
(HERE / "course.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(f"{len(out['spread'])} spreads, campus {out['campus']['first']['gpa']} to {out['campus']['last']['gpa']}")
