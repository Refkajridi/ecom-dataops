import glob
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = sorted(glob.glob(str(ROOT / "contracts" / "*.yml")))


@pytest.mark.parametrize("path", CONTRACTS)
def test_contract(con, path):
    with open(path, encoding="utf-8") as f:
        c = yaml.safe_load(f)
    schema_name, table = c["source"].split(".")
    types = {r[0]: r[1] for r in con.execute(
        "select column_name, data_type from information_schema.columns "
        "where table_schema = ? and table_name = ?", [schema_name, table]).fetchall()}

    for col, spec in c["columns"].items():
        assert col in types, f"colonne manquante : {col}"
        assert types[col] == spec["type"], f"type incorrect pour {col} : {types[col]}"
        if spec.get("nullable") is False:
            n = con.execute(f"select count(*) from {c['source']} where {col} is null").fetchone()[0]
            assert n == 0, f"{col} contient des NULL"
        if "min" in spec:
            n = con.execute(f"select count(*) from {c['source']} where {col} < {spec['min']}").fetchone()[0]
            assert n == 0, f"{col} < {spec['min']}"
        if "allowed" in spec:
            vals = ",".join(f"'{v}'" for v in spec["allowed"])
            n = con.execute(f"select count(*) from {c['source']} where {col} not in ({vals})").fetchone()[0]
            assert n == 0, f"{col} contient des valeurs hors {spec['allowed']}"