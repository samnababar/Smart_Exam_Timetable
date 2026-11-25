from collections import defaultdict


def build_conflict_graph(subjects, enrollments):
    """Return adjacency map where each subject connects to conflicting subjects."""
    subject_ids = {item["id"] for item in subjects}
    adjacency = {subject_id: set() for subject_id in subject_ids}
    students_to_subjects = defaultdict(set)

    for enrollment in enrollments:
        students_to_subjects[enrollment["student_id"]].add(enrollment["subject_id"])

    for related_subjects in students_to_subjects.values():
        related_subjects = list(related_subjects)
        for index, subject_id in enumerate(related_subjects):
            for other_subject_id in related_subjects[index + 1:]:
                if subject_id != other_subject_id:
                    adjacency[subject_id].add(other_subject_id)
                    adjacency[other_subject_id].add(subject_id)

    return adjacency


def get_conflict_pairs(subjects, enrollments):
    """Return a sorted list of unique conflict pairs."""
    adjacency = build_conflict_graph(subjects, enrollments)
    pairs = set()
    for subject_id, neighbors in adjacency.items():
        for neighbor_id in neighbors:
            if subject_id < neighbor_id:
                pairs.add((subject_id, neighbor_id))
    return sorted(pairs)
