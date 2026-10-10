from recipes.models import IngredientRecipe, Recipe
from users.models import User

PASSWORD = 'Str0ng-Passw0rd!'

# A valid 1x1 PNG, the same format the frontend sends.
IMAGE = (
    'data:image/png;base64,'
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk'
    'YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
)


def make_user(username):
    return User.objects.create_user(
        username=username,
        email=f'{username}@example.com',
        password=PASSWORD,
        first_name=username.capitalize(),
        last_name='Tester',
    )


def make_recipe(author, tags, ingredients, name='Блины', cooking_time=30):
    """Create a recipe; ingredients is a list of (ingredient, amount)."""
    recipe = Recipe.objects.create(
        author=author,
        name=name,
        text='Смешать и пожарить.',
        cooking_time=cooking_time,
    )
    recipe.tags.set(tags)
    for ingredient, amount in ingredients:
        IngredientRecipe.objects.create(
            recipe=recipe, ingredient=ingredient, amount=amount
        )
    return recipe
