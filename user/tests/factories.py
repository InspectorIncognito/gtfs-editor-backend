import factory
from user.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Faker('email')
    password = factory.Faker('password')
    name = factory.Faker('name')
    last_name = factory.Faker('last_name')

