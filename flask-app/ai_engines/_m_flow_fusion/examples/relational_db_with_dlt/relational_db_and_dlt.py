"""Ingest data from a relational database (via dlt) into M-flow's knowledge graph."""

import os
import asyncio
import dlt
from dlt.destinations.impl.sqlalchemy.configuration import SqlalchemyCredentials

import m_flow
from m_flow.shared.logging_utils import setup_logging, ERROR
from m_flow.api.v1.search import RecallMode


class PatchedCredentials(SqlalchemyCredentials):
    """Work around dlt's credential validation for local SQLite."""

    def __init__(self, connection_string=None):
        super().__init__()
        if connection_string:
            self.drivername = "sqlite"
            self.database = connection_string.replace("sqlite:///", "")


# --- dlt pipeline: fetch Pokémon data from PokéAPI ---


@dlt.resource(write_disposition="replace")
def pokemon_list(limit: int = 5):
    """Fetch a short list of Pokémon names from the API."""
    import requests

    resp = requests.get(f"https://pokeapi.co/api/v2/pokemon?limit={limit}").json()
    yield resp.get("results", [])


@dlt.transformer(data_from=pokemon_list)
def pokemon_details(pokemons):
    """Enrich each Pokémon with type and stat details."""
    import requests

    for p in pokemons:
        detail = requests.get(p["url"]).json()
        yield {
            "name": detail["name"],
            "types": [t["type"]["name"] for t in detail["types"]],
            "height": detail["height"],
            "weight": detail["weight"],
            "base_experience": detail.get("base_experience"),
        }


async def run_dlt_pipeline():
    """Load Pokémon data into a local SQLite database via dlt."""
    db_path = os.path.join(os.path.dirname(__file__), "pokemon.sqlite")
    conn_str = f"sqlite:///{db_path}"

    pipeline = dlt.pipeline(
        workflow_name="pokemon_etl",
        destination=dlt.destinations.sqlalchemy(
            credentials=PatchedCredentials(conn_str),
        ),
        dataset_name="pokedex",
    )

    print("Running dlt pipeline (fetching Pokémon data)...")
    info = pipeline.run(pokemon_details)
    print(f"dlt load: {info.loads_ids}")
    return db_path


async def apply_fk_fixes(db_path: str):
    """Apply foreign-key patches to the dlt-generated schema."""
    fix_sql = os.path.join(os.path.dirname(__file__), "fix_foreign_keys.sql")
    if not os.path.exists(fix_sql):
        print("No FK fix script found — skipping.")
        return

    import sqlite3

    conn = sqlite3.connect(db_path)
    with open(fix_sql) as f:
        conn.executescript(f.read())
    conn.close()
    print("FK fixes applied.")


async def ingest_into_mflow(db_path: str):
    """Migrate the SQLite database into M-flow's knowledge graph."""
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    m_flow.config.set_relational_db_config(
        {
            "db_path": os.path.dirname(db_path),
            "db_name": os.path.basename(db_path).replace(".sqlite", ""),
            "db_provider": "sqlite",
        }
    )

    await m_flow.add(db_path, dataset_name="pokemon_db")
    await m_flow.memorize(datasets=["pokemon_db"])
    print("M-flow knowledge graph built from SQLite data.")


async def query_graph():
    """Run sample queries against the graph."""
    for q in ["What types of Pokémon exist?", "Which Pokémon is the heaviest?"]:
        results = await m_flow.search(
            query_type=RecallMode.TRIPLET_COMPLETION,
            query_text=q,
        )
        print(f"\nQ: {q}")
        for r in results:
            print(f"  · {r}")


async def run():
    db_path = await run_dlt_pipeline()
    await apply_fk_fixes(db_path)
    await ingest_into_mflow(db_path)
    await query_graph()


if __name__ == "__main__":
    setup_logging(log_level=ERROR)
    asyncio.run(run())
