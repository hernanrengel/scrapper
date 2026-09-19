import factory

from scraper.models import Link, Page, PageStatusEvent, Status


class PageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Page

    url = factory.Sequence(lambda n: f"https://example.com/page-{n}")
    normalized_url = factory.LazyAttribute(lambda o: o.url)
    title = factory.Faker("sentence", nb_words=3)
    status = Status.PENDING


class LinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Link

    page = factory.SubFactory(PageFactory)
    href = factory.Sequence(lambda n: f"https://example.com/link-{n}")
    name_html = factory.Faker("word")


class PageStatusEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PageStatusEvent

    page = factory.SubFactory(PageFactory)
    from_status = None
    to_status = Status.PENDING
