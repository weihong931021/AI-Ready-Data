import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
RELATION_DIR = BASE_DIR / "資料" / "3_EAP上傳" / "CSV" / "關係"

R2_PATH = RELATION_DIR / "R2_法規衍生義務.csv"
R3_PATH = RELATION_DIR / "R3_法規衍生權益.csv"

EXPECTED_EXISTING_R2 = {
    ("L001", "D002"),
    ("L001", "D003"),
    ("L001", "D004"),
    ("L001", "D005"),
    ("L007", "D001"),
    ("L007", "D008"),
    ("L008", "D007"),
    ("L008", "D006"),
    ("L009", "D007"),
}

EXPECTED_EXISTING_R3 = {
    ("L003", "B001"),
    ("L003", "B002"),
    ("L003", "B005"),
    ("L004", "B001"),
    ("L005", "B002"),
    ("L005", "B006"),
    ("L006", "B003"),
    ("L006", "B004"),
    ("L010", "B001"),
    ("L010", "B002"),
    ("L010", "B003"),
    ("L010", "B004"),
}

NEW_R2_EDGES = [
    ("L011", "D002"),
    ("L011", "D003"),
    ("L011", "D004"),
    ("L011", "D005"),
    ("L012", "D007"),
    ("L015", "D002"),
    ("L015", "D003"),
    ("L015", "D004"),
    ("L015", "D005"),
    ("L018", "D007"),
    ("L019", "D001"),
    ("L020", "D002"),
    ("L020", "D003"),
    ("L020", "D004"),
    ("L020", "D005"),
    ("L021", "D007"),
    ("L022", "D007"),
    ("L029", "D001"),
]

NEW_R3_EDGES = [
    ("L011", "B001"),
    ("L011", "B002"),
    ("L011", "B003"),
    ("L011", "B004"),
    ("L011", "B005"),
    ("L013", "B001"),
    ("L013", "B002"),
    ("L016", "B003"),
    ("L016", "B004"),
    ("L017", "B001"),
    ("L017", "B002"),
    ("L017", "B005"),
    ("L018", "B001"),
    ("L018", "B002"),
    ("L018", "B003"),
    ("L018", "B004"),
    ("L018", "B005"),
    ("L021", "B001"),
    ("L021", "B005"),
    ("L024", "B001"),
    ("L025", "B001"),
    ("L025", "B002"),
    ("L025", "B003"),
    ("L025", "B004"),
    ("L025", "B005"),
    ("L025", "B006"),
    ("L026", "B001"),
    ("L026", "B005"),
    ("L027", "B001"),
    ("L027", "B005"),
]


def read_edges(path, expected_fieldnames):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(expected_fieldnames):
            raise ValueError(
                f"{path} 欄位不符: {reader.fieldnames} != {list(expected_fieldnames)}"
            )
        rows = list(reader)

    source_col, target_col = expected_fieldnames
    edges = {(row[source_col], row[target_col]) for row in rows}
    return rows, edges


def append_missing_edges(path, fieldnames, candidate_edges, expected_existing):
    rows, existing_edges = read_edges(path, fieldnames)
    missing_expected = expected_existing - existing_edges
    if missing_expected:
        missing = ", ".join(format_edge(edge) for edge in sorted(missing_expected))
        raise ValueError(f"{path.name} 缺少既有邊，請先檢查檔案: {missing}")

    duplicate_candidates = [
        edge for index, edge in enumerate(candidate_edges) if edge in candidate_edges[:index]
    ]
    if duplicate_candidates:
        duplicates = ", ".join(format_edge(edge) for edge in duplicate_candidates)
        raise ValueError(f"{path.name} 待新增清單內有重複邊: {duplicates}")

    additions = [edge for edge in candidate_edges if edge not in existing_edges]
    if additions:
        source_col, target_col = fieldnames
        with path.open("a", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            for source, target in additions:
                writer.writerow({source_col: source, target_col: target})

    updated_rows, updated_edges = read_edges(path, fieldnames)
    expected_row_count = len(rows) + len(additions)
    if len(updated_rows) != expected_row_count:
        raise ValueError(
            f"{path.name} 回讀行數不符: {len(updated_rows)} != {expected_row_count}"
        )

    missing_after_write = set(additions) - updated_edges
    if missing_after_write:
        missing = ", ".join(format_edge(edge) for edge in sorted(missing_after_write))
        raise ValueError(f"{path.name} 追加後仍缺少邊: {missing}")

    return len(rows), additions


def format_edge(edge):
    return f"{edge[0]}→{edge[1]}"


def format_edges(edges):
    return ", ".join(format_edge(edge) for edge in edges) if edges else "無"


def main():
    original_r2_count, added_r2 = append_missing_edges(
        R2_PATH,
        ("條文ID", "義務ID"),
        NEW_R2_EDGES,
        EXPECTED_EXISTING_R2,
    )
    original_r3_count, added_r3 = append_missing_edges(
        R3_PATH,
        ("條文ID", "權益ID"),
        NEW_R3_EDGES,
        EXPECTED_EXISTING_R3,
    )

    print(f"R2新增: {format_edges(added_r2)}")
    print(f"R3新增: {format_edges(added_r3)}")
    print("統計:")
    print(f"原有R2邊數: {original_r2_count}")
    print(f"新增R2邊數: {len(added_r2)}")
    print(f"原有R3邊數: {original_r3_count}")
    print(f"新增R3邊數: {len(added_r3)}")


if __name__ == "__main__":
    main()
