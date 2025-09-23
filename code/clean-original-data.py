

import json
import csv
from collections import Counter
from pathlib import Path

LOC_THRESHOLD  = 0.70   # ≥  % of Location votes must match
TIME_THRESHOLD = 0.65   # ≥  % of individual Time tags must match
MAX_CONTROVERSIAL = 50  # how many on-the-fence tasks to keep


def consensus(items, threshold):
    """
    Given a list of hashable things, return (value, share)
      • value  – the majority choice     (None if no value meets threshold)
         share  – its relative frequency (0-1), rounded to 3 decimals
    """
    if not items:
        return None, 0.0
    total = len(items)
    counter = Counter(items)
    winner, votes = counter.most_common(1)[0]
    share = votes / total
    return (winner if share >= threshold else None), round(share, 3)


def flatten_times(judgements):
    """
    Turn the list of Times strings into a list of individual tags
    (splits on commas and strips whitespace)
    """
    tags = []
    for j in judgements:
        if j.get("Known") == "yes":
            tags.extend(t.strip() for t in j["Times"].split(",") if t.strip())
    return tags


def main(infile="MS-LaTTE.json",
         csv_out="filtered_tasks.csv",
         json_out="controversial_tasks.json"):

    data = json.loads(Path(infile).read_text())

    high_agreement = []
    controversial  = []

    # Collect for overall statistics
    all_locations = set()
    all_times     = set()

    for task in data:

        
        loc_votes = [
            j["Locations"].strip()
            for j in task["LocJudgements"]
            if j.get("Known") == "yes" and j["Locations"].strip()
        ]
        majority_loc, loc_share = consensus(loc_votes, LOC_THRESHOLD)
        all_locations.update(loc_votes)

         
        time_votes = flatten_times(task["TimeJudgements"])
        all_times.update(time_votes)

        # For time we allow *multiple* tags to clear the bar
        tag_counter = Counter(time_votes)
        maj_times = [
            tag for tag, count in tag_counter.items()
            if count / len(time_votes) >= TIME_THRESHOLD
        ]

        
        if majority_loc and maj_times:
            high_agreement.append({
                "ID"         : task["ID"],
                "TaskTitle"  : task["TaskTitle"],
                "ListTitle"  : task["ListTitle"],
                "Location"   : majority_loc,
                "Times"      : ";".join(sorted(maj_times)),
                "LocShare"   : loc_share,
            })
        else:
            # Measure fuzziness = 1 - (max share of Locations *AND* Times)
            fuzz = 1 - min(loc_share, max(
                (c / len(time_votes) for c in tag_counter.values()),
                default=0.0
            ))
            controversial.append((fuzz, task))

    # keep only the least-clear 10 - FIX: use key function to sort only by fuzz value
    controversial.sort(key=lambda x: x[0], reverse=True)  # sort by fuzz value only
    controversial = [t for _, t in controversial[:MAX_CONTROVERSIAL]]

    
    with open(csv_out, "w", newline="", encoding="utf-8") as fh:
        fieldnames = ["ID", "TaskTitle", "ListTitle",
                      "Location", "Times", "LocShare"]
        wr = csv.DictWriter(fh, fieldnames=fieldnames)
        wr.writeheader()
        wr.writerows(high_agreement)

    Path(json_out).write_text(json.dumps(controversial, indent=2))

    
    print(f"High-agreement tasks written: {len(high_agreement)}")
    print(f"Unique Location values: {sorted(all_locations)}")
    print(f"Unique Time tags     : {sorted(all_times)}")


if __name__ == "__main__":
    main()