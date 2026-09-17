"""Recipe recommendation engine using M-flow's low-level graph API."""

import asyncio
from m_flow import prune
from m_flow.adapters.graph import get_graph_provider
from m_flow.low_level import setup, MemoryNode
from m_flow.storage import persist_memory_nodes


# --- Domain models ---


class Cuisines(MemoryNode):
    name: str = "Cuisines"


cuisine_root = Cuisines()


class Cuisine(MemoryNode):
    name: str
    region: str
    is_type: Cuisines = cuisine_root
    metadata: dict = {"index_fields": ["name"]}


class Ingredients(MemoryNode):
    name: str = "Ingredients"


ingredient_root = Ingredients()


class Ingredient(MemoryNode):
    name: str
    category: str  # vegetable, protein, spice, etc.
    is_type: Ingredients = ingredient_root
    metadata: dict = {"index_fields": ["name"]}


class Diets(MemoryNode):
    name: str = "Diets"


diet_root = Diets()


class Diet(MemoryNode):
    name: str
    restrictions: list[str]
    is_type: Diets = diet_root
    metadata: dict = {"index_fields": ["name"]}


class Recipe(MemoryNode):
    name: str
    cuisine: Cuisine
    ingredients: list[Ingredient]
    prep_time_minutes: int
    metadata: dict = {"index_fields": ["name"]}


class UserProfile(MemoryNode):
    name: str
    preferred_cuisines: list[Cuisine]
    dietary_needs: list[Diet]
    metadata: dict = {"index_fields": ["name"]}


# --- Sample data ---

CUISINES = [
    Cuisine(name="Italian", region="Europe"),
    Cuisine(name="Japanese", region="Asia"),
    Cuisine(name="Mexican", region="Americas"),
]

INGREDIENTS = [
    Ingredient(name="Tomato", category="vegetable"),
    Ingredient(name="Mozzarella", category="dairy"),
    Ingredient(name="Basil", category="herb"),
    Ingredient(name="Salmon", category="protein"),
    Ingredient(name="Rice", category="grain"),
    Ingredient(name="Avocado", category="fruit"),
    Ingredient(name="Tortilla", category="grain"),
]

DIETS = [
    Diet(name="Vegetarian", restrictions=["meat", "fish"]),
    Diet(name="Gluten-Free", restrictions=["wheat", "barley"]),
]

RECIPES = [
    Recipe(
        name="Margherita Pizza",
        cuisine=CUISINES[0],
        ingredients=[INGREDIENTS[0], INGREDIENTS[1], INGREDIENTS[2]],
        prep_time_minutes=30,
    ),
    Recipe(
        name="Salmon Sushi Bowl",
        cuisine=CUISINES[1],
        ingredients=[INGREDIENTS[3], INGREDIENTS[4], INGREDIENTS[5]],
        prep_time_minutes=20,
    ),
    Recipe(
        name="Veggie Burrito",
        cuisine=CUISINES[2],
        ingredients=[INGREDIENTS[5], INGREDIENTS[6], INGREDIENTS[0]],
        prep_time_minutes=15,
    ),
]

USERS = [
    UserProfile(name="Alice", preferred_cuisines=[CUISINES[0], CUISINES[1]], dietary_needs=[DIETS[0]]),
    UserProfile(name="Bob", preferred_cuisines=[CUISINES[2]], dietary_needs=[DIETS[1]]),
]


async def load_graph(nodes):
    """Store all nodes in the knowledge graph."""
    await persist_memory_nodes(nodes)
    return nodes


async def recommend(user: UserProfile):
    """Find recipes matching user preferences via graph traversal."""
    engine = await get_graph_provider()
    connections = await engine.get_triplets(str(user.id))
    print(f"\nRecommendations for {user.name}:")
    for src, edge, dst in connections:
        print(f"  {src.get('name', '?')} --{edge.get('relationship_name', '?')}--> {dst.get('name', '?')}")


async def run():
    await prune.prune_data()
    await prune.prune_system(metadata=True)
    await setup()

    all_nodes = CUISINES + INGREDIENTS + DIETS + RECIPES + USERS + [cuisine_root, ingredient_root, diet_root]

    await load_graph(all_nodes)
    print(f"Loaded {len(all_nodes)} nodes into graph")

    for user in USERS:
        await recommend(user)


if __name__ == "__main__":
    asyncio.run(run())
