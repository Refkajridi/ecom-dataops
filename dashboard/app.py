import os
from pathlib import Path

import duckdb
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DB = os.getenv("DUCKDB_PATH", str(ROOT / "data" / "warehouse.duckdb"))

st.set_page_config(page_title="Ecom DataOps", layout="wide")


@st.cache_data(ttl=60)
def q(sql: str):
    con = duckdb.connect(DB, read_only=True)
    try:
        return con.execute(sql).df()
    finally:
        con.close()


st.title("Ecom DataOps")

# Bandeau de fraÃ®cheur
fresh = q("""select max(ingested_at) as last_ingest,
             date_diff('hour', max(ingested_at), now()) as age_h
             from raw.orders""")
age = int(fresh["age_h"][0])
msg = f"DerniÃ¨re ingestion : {fresh['last_ingest'][0]} (il y a {age} h)"
if age > 24:
    st.error(msg + " : donnÃ©es en retard")
elif age > 6:
    st.warning(msg)
else:
    st.success(msg)

tab1, tab2, tab3 = st.tabs(["Ventes", "Marge", "SantÃ© du pipeline"])

with tab1:
    st.subheader("Quel est le chiffre d'affaires par jour (EUR) ?")
    daily = q("""select order_date, round(sum(amount_eur), 2) as ca_eur
                 from main.fct_orders group by 1 order by 1""")
    st.bar_chart(daily.set_index("order_date"))
    st.subheader("Chiffre d'affaires par catÃ©gorie")
    cat = q("""select category, round(sum(amount_eur), 2) as ca_eur
               from main.fct_orders group by 1 order by 2 desc""")
    st.bar_chart(cat.set_index("category"))

with tab2:
    st.subheader("Quelle catÃ©gorie est la plus rentable ?")
    marge = q("""select category,
                 round(sum(amount_eur), 2) as ca_eur,
                 round(sum(cost_total), 2) as cout_eur,
                 round(sum(amount_eur) - sum(cost_total), 2) as marge_eur
                 from main.fct_orders group by 1 order by 4 desc""")
    st.dataframe(marge, width="stretch")
    st.bar_chart(marge.set_index("category")[["marge_eur"]])

with tab3:
    st.subheader("Derniers runs du pipeline")
    try:
        runs = q("""select run_at, status, duration_s, detail
                    from ops.pipeline_runs order by run_at desc limit 20""")
        st.dataframe(runs, width="stretch")
    except duckdb.CatalogException:
        st.info("Aucun run enregistrÃ© pour le moment.")
