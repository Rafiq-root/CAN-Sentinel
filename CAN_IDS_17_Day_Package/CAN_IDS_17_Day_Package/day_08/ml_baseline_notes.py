"""Day 8 guardrail: use only if trustworthy ground-truth labels exist."""
def readiness_check(has_labels: bool, labels_documented: bool, session_split_available: bool) -> str:
    if not has_labels:
        return "Skip ML: no ground-truth labels. Continue with rule-based IDS."
    if not labels_documented:
        return "Do not train yet: document what each label means."
    if not session_split_available:
        return "Do not report generalization yet: create a held-out session/time split."
    return "Ready to implement a separate sklearn baseline and evaluate on held-out data."

if __name__ == "__main__":
    print(readiness_check(has_labels=False, labels_documented=False, session_split_available=False))
